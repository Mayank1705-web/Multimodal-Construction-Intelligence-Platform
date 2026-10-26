import asyncio

import pytest

from app import llm
from app.errors import AppError
from app.schemas import SafetyResult

PLAN = {"project_name": "Test house", "plot_width_ft": 30, "plot_depth_ft": 50, "floors": 2, "bedrooms": 3,
        "quality": "Standard", "city": "Bhopal"}


def ok(r):
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "success"
    assert body["meta"]["request_id"]
    return body["data"]


# ---------------------------------------------------------------- health
def test_health(client):
    r = client.get("/api/health").json()
    assert r["status"] == "ok" and r["demo_mode"] is True


# ---------------------------------------------------------------- safety
def test_safety_text_only(client):
    d = ok(client.post("/api/safety/analyze", data={"description": "Workers on scaffold without helmet near trench"}))
    assert d["overall_risk"] in {"Low", "Medium", "High", "Critical"}
    assert d["hazards"] and d["ppe"]


def test_safety_with_image(client, png):
    r = client.post("/api/safety/analyze", data={"description": "Roof edge work"},
                    files=[("images", ("site.png", png, "image/png"))])
    assert ok(r)["confidence"] > 0


def test_safety_requires_input(client):
    r = client.post("/api/safety/analyze", data={"description": ""})
    assert r.status_code == 422 and r.json()["error"]["code"] == "no_input"


def test_corrupt_and_truncated_images_rejected(client, png):
    r = client.post("/api/safety/analyze", files=[("images", ("bad.png", b"not an image", "image/png"))])
    assert r.status_code == 422 and r.json()["error"]["code"] == "corrupt_image"
    r = client.post("/api/cracks/analyze", files=[("images", ("cut.png", png[: len(png) // 2], "image/png"))])
    assert r.status_code == 422 and r.json()["error"]["code"] == "corrupt_image"


def test_unsupported_and_empty_images(client):
    r = client.post("/api/safety/analyze", files=[("images", ("a.gif", b"GIF89a", "image/gif"))])
    assert r.status_code == 415
    r = client.post("/api/safety/analyze", files=[("images", ("a.png", b"", "image/png"))])
    assert r.status_code == 422


def test_too_many_images(client, png):
    files = [("images", (f"{i}.png", png, "image/png")) for i in range(6)]
    assert client.post("/api/safety/analyze", files=files).json()["error"]["code"] == "too_many_images"


def test_tiny_image_warns(client):
    from tests.conftest import make_image
    tiny = make_image(size=(60, 60))
    r = client.post("/api/cracks/analyze", data={"description": "small crack"}, files=[("images", ("t.png", tiny, "image/png"))])
    assert ok(r) is not None and r.json()["meta"]["warnings"]


# ---------------------------------------------------------------- cracks
def test_crack_detected_and_clean(client, png):
    d = ok(client.post("/api/cracks/analyze", data={"description": "diagonal crack near stair, 4 mm wide", "element_type": "Wall"},
                       files=[("images", ("c.png", png, "image/png"))]))
    assert d["crack_detected"] and d["cracks"][0]["probable_causes"] and d["needs_engineer_review"]
    d = ok(client.post("/api/cracks/analyze", data={"description": "plain painted surface with no defects visible"}))
    assert d["crack_detected"] is False and d["cracks"] == []


# ---------------------------------------------------------------- valuation
def test_valuation(client):
    d = ok(client.post("/api/valuation/estimate", json={"property_type": "Apartment", "city": "Bhopal", "area_sqft": 1200,
                                                         "bedrooms": 2, "age_years": 4, "condition": "Good", "amenities": ["Parking", "Lift"]}))
    assert d["estimated_value_low"] <= d["estimated_value_mid"] <= d["estimated_value_high"]


@pytest.mark.parametrize("payload", [
    {"property_type": "Apartment", "city": "Bhopal", "area_sqft": -5},
    {"property_type": "Castle", "city": "Bhopal", "area_sqft": 100},
    {"property_type": "Apartment", "city": "", "area_sqft": 100},
    {"property_type": "Apartment", "city": "Bhopal", "area_sqft": 100, "currency": "XYZ"},
])
def test_valuation_bad_input(client, payload):
    r = client.post("/api/valuation/estimate", json=payload)
    assert r.status_code == 422 and r.json()["status"] == "error"


# ---------------------------------------------------------------- planning
def test_planning_consistency(client):
    d = ok(client.post("/api/planning/generate", json=PLAN))
    c = d["cost"]
    assert abs(sum(m["total_cost"] for m in d["materials"]) - c["materials"]) <= 1
    parts = c["materials"] + c["labour"] + c["equipment"] + c["permits_and_overheads"] + c["contingency"]
    assert abs(parts - c["total"]) <= 3
    ends = {t["id"]: t["end_day"] for t in d["tasks"]}
    for t in d["tasks"]:
        assert t["start_day"] >= max((ends[x] for x in t["depends_on"]), default=0)
    assert d["total_duration_days"] == max(ends.values())
    fp = d["floor_plan"]
    assert all(r["x"] + r["w"] <= fp["width_ft"] + 0.1 and r["y"] + r["h"] <= fp["depth_ft"] + 0.1 for r in fp["rooms"])


def test_planning_quality_changes_cost(client):
    a = ok(client.post("/api/planning/generate", json={**PLAN, "quality": "Economy"}))["cost"]["total"]
    b = ok(client.post("/api/planning/generate", json={**PLAN, "quality": "Premium"}))["cost"]["total"]
    assert b > a


def test_planning_rejects_bad_dimensions(client):
    assert client.post("/api/planning/generate", json={**PLAN, "plot_width_ft": 0}).status_code == 422
    assert client.post("/api/planning/generate", json={**PLAN, "floors": 500}).status_code == 422


def test_planning_repairs_bad_ai_output(client, monkeypatch):
    from app import routes
    from app.schemas import FloorPlan, Material, PlanResult, Room, Task

    async def fake(task, model, text, images, ctx):
        bad = PlanResult(project_name="x", summary="s",
                         materials=[Material(item="Gold", unit="kg", quantity=1e6, unit_cost=1e6)],
                         tasks=[Task(id="A", name="a", phase="p", duration_days=3, depends_on=["B"]),
                                Task(id="B", name="b", phase="p", duration_days=3, depends_on=["A"])],
                         floor_plan=FloorPlan(width_ft=10, depth_ft=10, rooms=[Room(name="r", x=0, y=0, w=50, h=5)]))
        return bad, "test", 1

    monkeypatch.setattr(routes.llm, "run_task", fake)
    r = client.post("/api/planning/generate", json=PLAN)
    d = ok(r)
    assert len(r.json()["meta"]["warnings"]) == 3
    assert d["cost"]["total"] > 0 and d["tasks"][0]["id"] == "T1"


# ---------------------------------------------------------------- assistant, knowledge
def test_assistant_and_knowledge(client):
    d = ok(client.post("/api/assistant/daily", json={"message": "Slab pour planned today with 25 workers", "phase": "Structure", "open_issues": ["Pump delayed"]}))
    assert d["checklist"] and d["warnings"]
    assert ok(client.post("/api/knowledge/ask", json={"question": "What is the minimum curing period for concrete?"}))["answer"]
    assert client.post("/api/knowledge/ask", json={"question": "hi"}).status_code == 422
    assert client.post("/api/assistant/daily", json={"message": "x"}).status_code == 422


# ---------------------------------------------------------------- weather
def test_weather(client, monkeypatch):
    from app import routes
    from app.schemas import WeatherDay, WeatherNow

    async def fake(_):
        return ("Bhopal, MP, India", WeatherNow(temperature_c=30, humidity_pct=60, wind_kph=12, precipitation_mm=0),
                [WeatherDay(date="2026-10-27", temp_max_c=33, temp_min_c=22, precipitation_mm=25, wind_max_kph=20)])

    monkeypatch.setattr(routes, "fetch_weather", fake)
    d = ok(client.post("/api/weather/advisory", json={"location": "Bhopal", "activities": ["Concrete pouring", "Excavation"]}))
    by = {a["activity"]: a["suitability"] for a in d["activities"]}
    assert by["Concrete pouring"] == "Hold"


def test_weather_failure_is_structured(client, monkeypatch):
    from app import routes

    async def boom(_):
        raise AppError("weather_unavailable", "down", 502)

    monkeypatch.setattr(routes, "fetch_weather", boom)
    r = client.post("/api/weather/advisory", json={"location": "Bhopal"})
    assert r.status_code == 502 and r.json()["error"]["code"] == "weather_unavailable"


# ---------------------------------------------------------------- history
def test_history_roundtrip(client):
    rid = client.post("/api/knowledge/ask", json={"question": "What is slump test?"}).json()["meta"]["record_id"]
    assert any(i["id"] == rid for i in client.get("/api/history").json()["data"])
    assert client.get(f"/api/history/{rid}").json()["data"]["result"]["answer"]
    assert client.delete(f"/api/history/{rid}").status_code == 200
    assert client.get(f"/api/history/{rid}").status_code == 404


def test_unknown_route_is_json(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and r.json()["status"] == "error"


# ---------------------------------------------------------------- LLM gateway
def test_extract_json_variants():
    assert llm.extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert llm.extract_json('Here you go: {"a": {"b": 2}} done') == {"a": {"b": 2}}
    with pytest.raises(ValueError):
        llm.extract_json("no json here")


def test_gateway_repairs_then_succeeds(monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    get_settings.cache_clear()
    replies = iter(["not json at all", '{"overall_risk":"Low","summary":"ok"}'])

    async def fake(system, text, images):
        return next(replies)

    monkeypatch.setattr(llm, "_call_provider", fake)
    result, provider, _ = asyncio.run(llm.run_task("safety", SafetyResult, "t", [], {}))
    assert result.overall_risk == "Low" and provider == "anthropic"
    get_settings.cache_clear()


def test_gateway_fails_cleanly_after_retry(monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    get_settings.cache_clear()

    async def fake(system, text, images):
        return '{"overall_risk":"Extreme"}'

    monkeypatch.setattr(llm, "_call_provider", fake)
    with pytest.raises(AppError) as e:
        asyncio.run(llm.run_task("safety", SafetyResult, "t", [], {}))
    assert e.value.code == "invalid_ai_response"
    get_settings.cache_clear()
