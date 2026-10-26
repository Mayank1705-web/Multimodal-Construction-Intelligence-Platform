"""Deterministic offline provider. Lets the whole platform run, and be tested, without an API key.

Output follows the same schemas as the real model and reacts to keywords in the input,
but it is not an AI analysis. The UI labels results from this provider as demo output.
"""
from __future__ import annotations

from typing import Any

from . import planlib
from .schemas import PlanRequest

CITY_RATE = {  # INR per sq ft, rough tiers for demo purposes
    "mumbai": 22000, "delhi": 14000, "gurgaon": 13000, "bengaluru": 9500, "bangalore": 9500, "pune": 7500,
    "hyderabad": 7500, "chennai": 7000, "kolkata": 6000, "ahmedabad": 5500, "indore": 4800, "bhopal": 4200,
    "jaipur": 4800, "lucknow": 4500, "nagpur": 4200,
}


def _has(text: str, *words: str) -> bool:
    t = text.lower()
    return any(w in t for w in words)


def safety(ctx: dict[str, Any]) -> dict:
    text = ctx.get("description", "")
    n = ctx.get("n_images", 0)
    hazards, ppe = [], []
    if _has(text, "scaffold", "height", "edge", "roof") or n:
        hazards.append({"name": "Fall from height", "severity": "High", "location": "Upper working level or edge",
                        "description": "Working edges and platforms should have guardrails, toe boards and fall arrest where rails are not possible.",
                        "corrective_action": "Install double guardrails and toe boards, tag the scaffold after inspection, and require harnesses above 1.8 m."})
    if _has(text, "trench", "excavat", "pit"):
        hazards.append({"name": "Unsupported excavation", "severity": "Critical", "location": "Excavation",
                        "description": "Excavations deeper than 1.5 m need shoring, sloping or benching.",
                        "corrective_action": "Stop entry until shoring is installed and a competent person has inspected the excavation."})
    if _has(text, "wire", "electric", "cable"):
        hazards.append({"name": "Exposed electrical supply", "severity": "High", "location": "Temporary power distribution",
                        "description": "Temporary wiring needs insulated cable, earth-leakage protection and covered joints.",
                        "corrective_action": "Isolate and re-route the cable, fit an RCD and use industrial sockets."})
    hazards.append({"name": "Housekeeping and material storage", "severity": "Medium", "location": "Work area",
                    "description": "Loose material and offcuts in walkways raise trip risk.",
                    "corrective_action": "Designate stacking zones and clear walkways at the end of every shift."})
    for item in ["Safety helmet", "High-visibility vest", "Safety footwear", "Gloves", "Eye protection"]:
        missing = _has(text, f"no {item.split()[-1].lower()}", "without helmet") and item == "Safety helmet"
        ppe.append({"item": item, "status": "Missing" if missing else ("Unclear" if not n else "Compliant"),
                    "note": "Reported missing in the notes." if missing else ("No image to verify." if not n else "Confirm on the ground; this is a demo estimate.")})
    risk = max((h["severity"] for h in hazards), key=["Low", "Medium", "High", "Critical"].index)
    return {"overall_risk": risk, "summary": f"Demo analysis found {len(hazards)} hazard group(s). Highest risk level: {risk}.",
            "hazards": hazards, "ppe": ppe,
            "recommendations": ["Hold a short toolbox talk on the hazards listed before work resumes.", "Assign one person to verify PPE at the site entry.", "Re-inspect after corrective actions and record the result."],
            "confidence": 0.55 if n else 0.35,
            "limitations": "Demo provider: output is rule based and not a visual inspection." + ("" if n else " No image was supplied.")}


def cracks(ctx: dict[str, Any]) -> dict:
    text, n = ctx.get("description", ""), ctx.get("n_images", 0)
    if not n and not _has(text, "crack"):
        return {"crack_detected": False, "overall_severity": "Low", "structural_risk": "No crack reported",
                "summary": "No image or crack description was provided, so nothing could be assessed.",
                "cracks": [], "needs_engineer_review": False, "monitoring_plan": ["Upload a close-up photo with a scale reference."],
                "confidence": 0.2, "limitations": "Demo provider with no input evidence."}
    diagonal = _has(text, "diagonal", "stair", "step", "settle")
    wide = _has(text, "wide", "3 mm", "4 mm", "5 mm", "through", "leak")
    sev = "High" if (diagonal and wide) else "Medium" if (diagonal or wide) else "Low"
    f = {"type": "Diagonal / settlement crack" if diagonal else "Hairline shrinkage crack", "severity": sev,
         "location": ctx.get("element_type") or "Not specified", "orientation": "Diagonal" if diagonal else "Irregular",
         "estimated_width_mm": 3.0 if wide else 0.3,
         "probable_causes": ["Differential foundation settlement", "Overloading"] if diagonal else ["Plastic shrinkage during curing", "Thermal movement"],
         "recommended_actions": (["Install crack gauges and measure weekly", "Have a structural engineer inspect before any repair"] if diagonal
                                 else ["Seal with flexible polymer-modified mortar", "Improve curing on later pours"])}
    return {"crack_detected": True, "overall_severity": sev,
            "structural_risk": "Possible structural movement" if sev in ("High", "Medium") else "Cosmetic, low structural risk",
            "summary": f"Demo analysis classifies the defect as: {f['type']} ({sev} severity).",
            "cracks": [f], "needs_engineer_review": sev in ("High", "Critical"),
            "monitoring_plan": ["Mark crack ends with dated pencil lines", "Photograph every two weeks with a scale"],
            "confidence": 0.5 if n else 0.3, "limitations": "Demo provider: keyword based, not an image analysis."}


def valuation(ctx: dict[str, Any]) -> dict:
    city = ctx["city"].lower().strip()
    base = CITY_RATE.get(city, 5000)
    cond = {"Poor": 0.8, "Fair": 0.9, "Good": 1.0, "Excellent": 1.1}[ctx["condition"]]
    age = max(0.65, 1 - 0.01 * ctx["age_years"])
    kind = {"Apartment": 1.0, "Independent House": 1.1, "Villa": 1.35, "Plot": 0.7, "Commercial": 1.5}[ctx["property_type"]]
    amen = 1 + min(len(ctx.get("amenities", [])), 6) * 0.015
    ppsf = round(base * cond * age * kind * amen)
    mid = round(ppsf * ctx["area_sqft"])
    return {"currency": ctx.get("currency", "INR"), "estimated_value_low": round(mid * 0.9), "estimated_value_mid": mid,
            "estimated_value_high": round(mid * 1.1), "price_per_sqft": ppsf,
            "summary": f"Demo estimate for a {ctx['property_type'].lower()} in {ctx['city']} at about {ppsf} per sq ft.",
            "factors": [{"factor": "City price tier", "impact": "Neutral", "note": "Base rate from a rough city tier table."},
                        {"factor": "Condition", "impact": "Positive" if cond > 1 else "Negative" if cond < 1 else "Neutral", "note": ctx["condition"]},
                        {"factor": "Building age", "impact": "Negative" if ctx["age_years"] > 5 else "Neutral", "note": f"{ctx['age_years']} years"}],
            "assumptions": ["Clear title and no legal dispute", "Demo rate table, not live market data"], "confidence": 0.3}


def planning(ctx: dict[str, Any]) -> dict:
    req = PlanRequest.model_validate(ctx["request"])
    tasks = planlib.default_tasks(req)
    layout = planlib.default_layout(req)
    mats = planlib.baseline_materials(req)
    return {"project_name": req.project_name,
            "summary": f"{req.floors}-floor {req.building_type.lower()} project on a {req.plot_width_ft:g} x {req.plot_depth_ft:g} ft plot, {req.quality.lower()} specification.",
            "materials": [m.model_dump() for m in mats], "tasks": [t.model_dump() for t in tasks],
            "floor_plan": layout.model_dump(),
            "elevation_notes": ["Plinth about 450 mm above road level", "Floor-to-floor height 3.0 m", "Sunshade projection on the west facade"],
            "risks": ["Monsoon delays to foundation work", "Steel and cement price movement", "Late approvals for utility connections"],
            "currency": req.currency}


def assistant(ctx: dict[str, Any]) -> dict:
    phase = ctx.get("phase") or "current phase"
    return {"answer": f"Demo reply for the {phase}. Start the day with a toolbox talk, confirm material deliveries, and close the open issues in order of safety impact.",
            "checklist": [{"task": "Toolbox talk and PPE check at gate", "priority": "High", "owner": "Safety officer"},
                          {"task": "Verify today's pour or lift plan and equipment inspection tags", "priority": "High", "owner": "Site engineer"},
                          {"task": "Record labour attendance and material receipts", "priority": "Medium", "owner": "Store keeper"},
                          {"task": "Photograph progress for the daily report", "priority": "Low", "owner": "Site engineer"}],
            "warnings": [f"Open issue: {i}" for i in ctx.get("open_issues", [])[:3]],
            "follow_up_questions": ["Which activities are on the critical path today?", "Are any subcontractors starting new work?"]}


def weather(ctx: dict[str, Any]) -> dict:
    f = ctx["forecast"]
    rain = max((d["precipitation_mm"] for d in f), default=0)
    wind = max((d["wind_max_kph"] for d in f), default=0)
    overall = "Unfavourable" if rain > 20 or wind > 45 else "Mixed" if rain > 5 or wind > 30 else "Favourable"
    acts = []
    for a in ctx["activities"]:
        low = a.lower()
        hold = (("concrete" in low or "paint" in low or "roof" in low) and rain > 10) or (("crane" in low or "lift" in low) and wind > 35)
        caution = rain > 3 or wind > 25
        acts.append({"activity": a, "suitability": "Hold" if hold else "Caution" if caution else "Go",
                     "reason": f"Peak rain {rain:g} mm and wind {wind:g} km/h in the forecast window.",
                     "recommendation": "Postpone and re-check tomorrow." if hold else "Proceed with protection and monitoring." if caution else "Proceed as planned."})
    return {"overall": overall, "summary": f"Demo advisory: conditions look {overall.lower()} over the next days.", "activities": acts,
            "precautions": ["Cover fresh concrete and stacked cement before rain", "Stop crane lifts when wind exceeds the manufacturer limit"]}


def knowledge(ctx: dict[str, Any]) -> dict:
    return {"answer": f"Demo answer. For the question \"{ctx['question']}\", confirm the governing code and the project specification, then apply the standard site practice for the element in question.",
            "key_points": ["Check the approved drawings and specification first", "Record test results and inspections", "Escalate any deviation to the structural engineer"],
            "standards_to_check": ["IS 456", "NBC 2016"], "follow_up_questions": ["Which grade of concrete is specified?", "What is the exposure condition?"]}


HANDLERS = {"safety": safety, "cracks": cracks, "valuation": valuation, "planning": planning,
            "assistant": assistant, "weather": weather, "knowledge": knowledge}


def generate(task: str, ctx: dict[str, Any]) -> dict:
    return HANDLERS[task](ctx)
