"""Strict JSON contracts shared by the AI layer, the API and the React frontend.

Every AI response is validated against one of these models before it is returned.
If validation fails the backend retries once with a repair prompt, then returns a
structured error. The frontend therefore never receives a malformed payload.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Severity = Literal["Low", "Medium", "High", "Critical"]


class Strict(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


# ---------------------------------------------------------------- envelope
class Meta(Strict):
    request_id: str
    provider: str
    latency_ms: int
    record_id: Optional[int] = None
    warnings: list[str] = Field(default_factory=list)


class ErrorBody(Strict):
    code: str
    message: str


class Envelope(Strict):
    status: Literal["success", "error"]
    data: Optional[Any] = None
    error: Optional[ErrorBody] = None
    meta: Optional[Meta] = None


# ---------------------------------------------------------------- safety
class Hazard(Strict):
    name: str
    severity: Severity
    location: str = "Not specified"
    description: str
    corrective_action: str


class PPEItem(Strict):
    item: str
    status: Literal["Compliant", "Missing", "Unclear"]
    note: str = ""


class SafetyResult(Strict):
    overall_risk: Severity
    summary: str
    hazards: list[Hazard] = Field(default_factory=list)
    ppe: list[PPEItem] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, default=0.5)
    limitations: str = ""


# ---------------------------------------------------------------- cracks
class CrackFinding(Strict):
    type: str  # e.g. hairline, shrinkage, settlement, flexural, shear, diagonal, map cracking
    severity: Severity
    location: str = "Not specified"
    orientation: str = "Not specified"
    estimated_width_mm: Optional[float] = Field(default=None, ge=0)
    probable_causes: list[str] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list)


class CrackResult(Strict):
    crack_detected: bool
    overall_severity: Severity
    structural_risk: str
    summary: str
    cracks: list[CrackFinding] = Field(default_factory=list)
    needs_engineer_review: bool = False
    monitoring_plan: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, default=0.5)
    limitations: str = ""


# ---------------------------------------------------------------- valuation
class ValuationFactor(Strict):
    factor: str
    impact: Literal["Positive", "Negative", "Neutral"]
    note: str = ""


class ValuationResult(Strict):
    currency: str = "INR"
    estimated_value_low: float = Field(ge=0)
    estimated_value_mid: float = Field(ge=0)
    estimated_value_high: float = Field(ge=0)
    price_per_sqft: float = Field(ge=0)
    summary: str
    factors: list[ValuationFactor] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, default=0.5)
    disclaimer: str = "Indicative estimate only. Obtain a certified valuation before any transaction."


class ValuationRequest(Strict):
    property_type: Literal["Apartment", "Independent House", "Villa", "Plot", "Commercial"]
    city: str = Field(min_length=2, max_length=80)
    locality: str = Field(default="", max_length=120)
    area_sqft: float = Field(gt=0, le=1_000_000)
    bedrooms: int = Field(default=0, ge=0, le=20)
    age_years: float = Field(default=0, ge=0, le=200)
    floor: int = Field(default=0, ge=0, le=200)
    condition: Literal["Poor", "Fair", "Good", "Excellent"] = "Good"
    amenities: list[str] = Field(default_factory=list)
    currency: str = "INR"
    notes: str = Field(default="", max_length=1500)


# ---------------------------------------------------------------- planning
class Material(Strict):
    item: str
    unit: str
    quantity: float = Field(ge=0)
    unit_cost: float = Field(ge=0)
    total_cost: float = Field(ge=0, default=0)


class CostBreakdown(Strict):
    materials: float = 0
    labour: float = 0
    equipment: float = 0
    permits_and_overheads: float = 0
    contingency: float = 0
    total: float = 0
    cost_per_sqft: float = 0


class Task(Strict):
    id: str
    name: str
    phase: str
    duration_days: int = Field(ge=1, le=2000)
    depends_on: list[str] = Field(default_factory=list)
    start_day: int = Field(ge=0, default=0)
    end_day: int = Field(ge=0, default=0)


class Room(Strict):
    name: str
    x: float = Field(ge=0)
    y: float = Field(ge=0)
    w: float = Field(gt=0)
    h: float = Field(gt=0)


class FloorPlan(Strict):
    width_ft: float = Field(gt=0)
    depth_ft: float = Field(gt=0)
    floor_label: str = "Ground floor"
    rooms: list[Room] = Field(default_factory=list)


class PlanResult(Strict):
    project_name: str
    summary: str
    materials: list[Material] = Field(default_factory=list)
    cost: CostBreakdown = Field(default_factory=CostBreakdown)
    tasks: list[Task] = Field(default_factory=list)
    total_duration_days: int = 0
    floor_plan: Optional[FloorPlan] = None
    elevation_notes: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    currency: str = "INR"


class PlanRequest(Strict):
    project_name: str = Field(default="New construction project", max_length=120)
    building_type: Literal["Residential", "Commercial", "Industrial", "Institutional"] = "Residential"
    plot_width_ft: float = Field(gt=5, le=2000)
    plot_depth_ft: float = Field(gt=5, le=2000)
    floors: int = Field(default=1, ge=1, le=60)
    bedrooms: int = Field(default=2, ge=0, le=20)
    quality: Literal["Economy", "Standard", "Premium"] = "Standard"
    city: str = Field(default="", max_length=80)
    start_date: str = ""
    currency: str = "INR"
    notes: str = Field(default="", max_length=1500)


# ---------------------------------------------------------------- assistant
class ChecklistItem(Strict):
    task: str
    priority: Literal["Low", "Medium", "High"]
    owner: str = "Site engineer"


class AssistantResult(Strict):
    answer: str
    checklist: list[ChecklistItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)


class AssistantRequest(Strict):
    message: str = Field(min_length=3, max_length=3000)
    project_name: str = Field(default="", max_length=120)
    phase: str = Field(default="", max_length=80)
    crew_size: int = Field(default=0, ge=0, le=5000)
    open_issues: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------- weather
class WeatherDay(Strict):
    date: str
    temp_max_c: float
    temp_min_c: float
    precipitation_mm: float
    wind_max_kph: float


class WeatherNow(Strict):
    temperature_c: float
    humidity_pct: float
    wind_kph: float
    precipitation_mm: float


class ActivityAdvice(Strict):
    activity: str
    suitability: Literal["Go", "Caution", "Hold"]
    reason: str
    recommendation: str


class WeatherAdvisory(Strict):
    location: str
    current: WeatherNow
    forecast: list[WeatherDay] = Field(default_factory=list)
    overall: Literal["Favourable", "Mixed", "Unfavourable"]
    summary: str
    activities: list[ActivityAdvice] = Field(default_factory=list)
    precautions: list[str] = Field(default_factory=list)


class WeatherAdvisoryAI(Strict):
    """The part of the advisory generated by the model."""
    overall: Literal["Favourable", "Mixed", "Unfavourable"]
    summary: str
    activities: list[ActivityAdvice] = Field(default_factory=list)
    precautions: list[str] = Field(default_factory=list)


class WeatherRequest(Strict):
    location: str = Field(min_length=2, max_length=80)
    activities: list[str] = Field(default_factory=lambda: ["Concrete pouring", "Crane operations", "Roofing", "Excavation"])


# ---------------------------------------------------------------- knowledge
class KnowledgeResult(Strict):
    answer: str
    key_points: list[str] = Field(default_factory=list)
    standards_to_check: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)


class KnowledgeRequest(Strict):
    question: str = Field(min_length=5, max_length=2000)
