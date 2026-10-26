from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from fastapi import APIRouter, File, Form, UploadFile

from . import llm, planlib, storage
from .config import get_settings
from .errors import AppError
from .images import PreparedImage, prepare_images
from .schemas import (AssistantRequest, AssistantResult, CrackResult, KnowledgeRequest, KnowledgeResult,
                      PlanRequest, PlanResult, SafetyResult, ValuationRequest, ValuationResult,
                      WeatherAdvisory, WeatherAdvisoryAI, WeatherRequest)
from .weather import fetch_weather

router = APIRouter(prefix="/api")


def _envelope(kind: str, title: str, request: dict, result: Any, provider: str, latency: int,
              warnings: Optional[list[str]] = None) -> dict:
    payload = result.model_dump(mode="json")
    rid = storage.save(kind, title, request, payload, provider)
    return {"status": "success", "data": payload,
            "meta": {"request_id": uuid.uuid4().hex[:12], "provider": provider, "latency_ms": latency,
                     "record_id": rid, "warnings": warnings or []}}


def _image_note(images: list[PreparedImage]) -> str:
    return f"{len(images)} image(s) attached." if images else "No images attached."


# ------------------------------------------------------------------ health
@router.get("/health")
async def health() -> dict:
    s = get_settings()
    return {"status": "ok", "provider": s.llm_provider, "demo_mode": s.llm_provider == "mock"}


# ------------------------------------------------------------------ safety
@router.post("/safety/analyze")
async def safety_analyze(description: str = Form(""), site_type: str = Form("General construction site"),
                         images: list[UploadFile] = File(default=[])) -> dict:
    description = description.strip()[:3000]
    imgs, warnings = await prepare_images(images)
    if not imgs and len(description) < 10:
        raise AppError("no_input", "Upload at least one site photo or describe the site in 10 or more characters.", 422)
    text = f"Site type: {site_type}\nNotes: {description or 'None'}\n{_image_note(imgs)}"
    result, provider, ms = await llm.run_task("safety", SafetyResult, text, imgs,
                                              {"description": description, "n_images": len(imgs)})
    return _envelope("safety", f"Safety review: {site_type}", {"site_type": site_type, "description": description,
                     "images": [i.filename for i in imgs]}, result, provider, ms, warnings)


# ------------------------------------------------------------------ cracks
@router.post("/cracks/analyze")
async def cracks_analyze(description: str = Form(""), element_type: str = Form("Wall"),
                         age_months: Optional[float] = Form(None),
                         images: list[UploadFile] = File(default=[])) -> dict:
    description = description.strip()[:3000]
    imgs, warnings = await prepare_images(images)
    if not imgs and len(description) < 10:
        raise AppError("no_input", "Upload a photo of the crack or describe it in 10 or more characters.", 422)
    text = (f"Structural element: {element_type}\nStructure age (months): {age_months if age_months is not None else 'unknown'}\n"
            f"Notes: {description or 'None'}\n{_image_note(imgs)}")
    result, provider, ms = await llm.run_task("cracks", CrackResult, text, imgs,
                                              {"description": description, "n_images": len(imgs), "element_type": element_type})
    return _envelope("cracks", f"Crack analysis: {element_type}", {"element_type": element_type, "age_months": age_months,
                     "description": description, "images": [i.filename for i in imgs]}, result, provider, ms, warnings)


# ------------------------------------------------------------------ valuation
@router.post("/valuation/estimate")
async def valuation_estimate(req: ValuationRequest) -> dict:
    planlib.fx(req.currency)
    text = "Property details (JSON):\n" + req.model_dump_json()
    result, provider, ms = await llm.run_task("valuation", ValuationResult, text, [], req.model_dump())
    lo, mid, hi = sorted([result.estimated_value_low, result.estimated_value_mid, result.estimated_value_high])
    result = result.model_copy(update={"estimated_value_low": lo, "estimated_value_mid": mid, "estimated_value_high": hi,
                                       "price_per_sqft": result.price_per_sqft or round(mid / req.area_sqft)})
    return _envelope("valuation", f"Valuation: {req.property_type}, {req.city}", req.model_dump(), result, provider, ms)


# ------------------------------------------------------------------ planning
@router.post("/planning/generate")
async def planning_generate(req: PlanRequest) -> dict:
    planlib.fx(req.currency)
    text = "Project brief (JSON):\n" + req.model_dump_json()
    result, provider, ms = await llm.run_task("planning", PlanResult, text, [], {"request": req.model_dump()})
    warnings: list[str] = []

    baseline = planlib.baseline_materials(req)
    materials = result.materials
    if not planlib.materials_plausible(materials, baseline):
        if materials:
            warnings.append("AI material quantities were outside a plausible range and were replaced with platform estimates.")
        materials = baseline
    materials, cost = planlib.compute_costs(materials, req)

    try:
        tasks = planlib.schedule(result.tasks) if result.tasks else planlib.default_tasks(req)
    except ValueError:
        warnings.append("AI schedule had invalid dependencies and was replaced with a standard sequence.")
        tasks = planlib.default_tasks(req)

    layout = result.floor_plan
    if not planlib.layout_valid(layout):
        if layout:
            warnings.append("AI floor plan overlapped or exceeded the plot and was replaced with a standard layout.")
        layout = planlib.default_layout(req)

    final = result.model_copy(update={
        "materials": materials, "cost": cost, "tasks": tasks, "floor_plan": layout, "currency": req.currency,
        "total_duration_days": max((t.end_day for t in tasks), default=0),
    })
    return _envelope("planning", f"Plan: {req.project_name}", req.model_dump(), final, provider, ms, warnings)


# ------------------------------------------------------------------ assistant
@router.post("/assistant/daily")
async def assistant_daily(req: AssistantRequest) -> dict:
    text = "Site context (JSON):\n" + req.model_dump_json()
    result, provider, ms = await llm.run_task("assistant", AssistantResult, text, [], req.model_dump())
    return _envelope("assistant", req.message[:80], req.model_dump(), result, provider, ms)


# ------------------------------------------------------------------ weather
@router.post("/weather/advisory")
async def weather_advisory(req: WeatherRequest) -> dict:
    label, now, days = await fetch_weather(req.location)
    activities = [a.strip() for a in req.activities if a.strip()][:8] or ["General site work"]
    text = (f"Location: {label}\nCurrent: {now.model_dump_json()}\nForecast: {json.dumps([d.model_dump() for d in days])}\n"
            f"Activities to assess: {json.dumps(activities)}")
    ai, provider, ms = await llm.run_task("weather", WeatherAdvisoryAI, text, [],
                                          {"forecast": [d.model_dump() for d in days], "activities": activities})
    result = WeatherAdvisory(location=label, current=now, forecast=days, **ai.model_dump())
    return _envelope("weather", f"Weather advisory: {label}", req.model_dump(), result, provider, ms)


# ------------------------------------------------------------------ knowledge
@router.post("/knowledge/ask")
async def knowledge_ask(req: KnowledgeRequest) -> dict:
    result, provider, ms = await llm.run_task("knowledge", KnowledgeResult, f"Question: {req.question}", [],
                                              {"question": req.question})
    return _envelope("knowledge", req.question[:80], req.model_dump(), result, provider, ms)


# ------------------------------------------------------------------ history
@router.get("/history")
async def history(kind: Optional[str] = None, limit: int = 50) -> dict:
    return {"status": "success", "data": storage.list_items(kind, limit)}


@router.get("/history/{item_id}")
async def history_item(item_id: int) -> dict:
    item = storage.get(item_id)
    if not item:
        raise AppError("not_found", "That record does not exist.", 404)
    return {"status": "success", "data": item}


@router.delete("/history/{item_id}")
async def history_delete(item_id: int) -> dict:
    if not storage.delete(item_id):
        raise AppError("not_found", "That record does not exist.", 404)
    return {"status": "success", "data": {"deleted": item_id}}
