"""Deterministic planning helpers: baseline quantities, cost maths, schedule maths, layout checks.

The language model proposes a plan; this module verifies and corrects the numbers so that
costs always add up and the schedule always respects dependencies.
"""
from __future__ import annotations

from .errors import AppError
from .schemas import CostBreakdown, FloorPlan, Material, PlanRequest, Room, Task

FX = {"INR": 1.0, "USD": 0.012, "EUR": 0.011, "GBP": 0.0095, "AED": 0.044}
QUALITY = {"Economy": 0.85, "Standard": 1.0, "Premium": 1.35}
COVERAGE = 0.70  # share of the plot that is built per floor

# (item, unit, quantity per built-up sq ft, INR unit cost)
BASE_ITEMS = [
    ("Cement (OPC/PPC, 50 kg bag)", "bag", 0.40, 410),
    ("Reinforcement steel", "kg", 4.0, 68),
    ("River/M-sand", "cft", 1.25, 55),
    ("Coarse aggregate 20 mm", "cft", 1.35, 48),
    ("Bricks or AAC blocks", "nos", 9.0, 9),
    ("Flooring tiles", "sq ft", 0.85, 85),
    ("Paint and putty", "sq ft", 2.4, 24),
    ("Electrical fittings and wiring", "sq ft", 1.0, 120),
    ("Plumbing and sanitary", "sq ft", 1.0, 135),
    ("Doors and windows", "sq ft", 1.0, 110),
]


def built_up_area(req: PlanRequest) -> float:
    return req.plot_width_ft * req.plot_depth_ft * COVERAGE * req.floors


def fx(currency: str) -> float:
    if currency not in FX:
        raise AppError("unsupported_currency", f"Currency must be one of {', '.join(FX)}.", 422)
    return FX[currency]


def baseline_materials(req: PlanRequest) -> list[Material]:
    area, q, rate = built_up_area(req), QUALITY[req.quality], fx(req.currency)
    out = []
    for item, unit, per_sqft, cost in BASE_ITEMS:
        qty = round(area * per_sqft, 1)
        unit_cost = round(cost * q * rate, 2)
        out.append(Material(item=item, unit=unit, quantity=qty, unit_cost=unit_cost, total_cost=round(qty * unit_cost, 2)))
    return out


def materials_plausible(candidate: list[Material], baseline: list[Material]) -> bool:
    if not candidate:
        return False
    cand = sum(m.quantity * m.unit_cost for m in candidate)
    base = sum(m.quantity * m.unit_cost for m in baseline)
    return base > 0 and 0.5 <= cand / base <= 2.0


def compute_costs(materials: list[Material], req: PlanRequest) -> tuple[list[Material], CostBreakdown]:
    fixed = []
    for m in materials:
        fixed.append(m.model_copy(update={"total_cost": round(m.quantity * m.unit_cost, 2)}))
    mat = sum(m.total_cost for m in fixed)
    labour, equipment, permits = mat * 0.40, mat * 0.06, mat * 0.03
    contingency = (mat + labour + equipment + permits) * 0.07
    total = mat + labour + equipment + permits + contingency
    area = max(built_up_area(req), 1)
    return fixed, CostBreakdown(
        materials=round(mat), labour=round(labour), equipment=round(equipment),
        permits_and_overheads=round(permits), contingency=round(contingency),
        total=round(total), cost_per_sqft=round(total / area, 2),
    )


def default_tasks(req: PlanRequest) -> list[Task]:
    f = req.floors
    spec = [
        ("T1", "Site clearing, survey and marking", "Site preparation", 5, []),
        ("T2", "Excavation", "Site preparation", 6 + f, ["T1"]),
        ("T3", "Footings and plinth beam", "Foundation", 14 + 2 * f, ["T2"]),
        ("T4", "Columns, slabs and beams", "Structure", 24 * f, ["T3"]),
        ("T5", "Masonry and plastering", "Masonry", 18 * f, ["T4"]),
        ("T6", "Electrical and plumbing rough-in", "MEP", 14 * f, ["T4"]),
        ("T7", "Waterproofing and flooring", "Finishing", 12 * f, ["T5", "T6"]),
        ("T8", "Doors, windows and carpentry", "Finishing", 10 * f, ["T5"]),
        ("T9", "Painting and fixtures", "Finishing", 12 * f, ["T7", "T8"]),
        ("T10", "Snagging, cleaning and handover", "Handover", 7, ["T9"]),
    ]
    return schedule([Task(id=i, name=n, phase=p, duration_days=d, depends_on=dep) for i, n, p, d, dep in spec])


def schedule(tasks: list[Task]) -> list[Task]:
    """Compute start/end days from dependencies. Raises ValueError on a cycle or unknown dependency."""
    by_id = {t.id: t for t in tasks}
    if len(by_id) != len(tasks):
        raise ValueError("duplicate task ids")
    done: dict[str, tuple[int, int]] = {}
    visiting: set[str] = set()

    def resolve(tid: str) -> tuple[int, int]:
        if tid in done:
            return done[tid]
        if tid in visiting:
            raise ValueError("dependency cycle")
        if tid not in by_id:
            raise ValueError(f"unknown dependency {tid}")
        visiting.add(tid)
        t = by_id[tid]
        start = max((resolve(d)[1] for d in t.depends_on), default=0)
        done[tid] = (start, start + t.duration_days)
        visiting.discard(tid)
        return done[tid]

    return [t.model_copy(update={"start_day": resolve(t.id)[0], "end_day": resolve(t.id)[1]}) for t in tasks]


def layout_valid(plan: FloorPlan | None) -> bool:
    if not plan or not plan.rooms:
        return False
    eps = 0.01
    for r in plan.rooms:
        if r.x + r.w > plan.width_ft + eps or r.y + r.h > plan.depth_ft + eps:
            return False
    for i, a in enumerate(plan.rooms):
        for b in plan.rooms[i + 1:]:
            if a.x < b.x + b.w - eps and b.x < a.x + a.w - eps and a.y < b.y + b.h - eps and b.y < a.y + a.h - eps:
                return False
    return True


def default_layout(req: PlanRequest) -> FloorPlan:
    """Simple band layout: public rooms at the front, bedrooms at the back, services between."""
    w = round(req.plot_width_ft * 0.84, 1)
    d = round(req.plot_depth_ft * 0.84, 1)
    beds = max(req.bedrooms, 0)
    front_h = round(d * 0.38, 1)
    mid_h = round(d * 0.18, 1)
    back_h = round(d - front_h - mid_h, 1)
    rooms: list[Room] = [
        Room(name="Living room", x=0, y=0, w=round(w * 0.6, 1), h=front_h),
        Room(name="Dining and kitchen", x=round(w * 0.6, 1), y=0, w=round(w - w * 0.6, 1), h=front_h),
        Room(name="Passage", x=0, y=front_h, w=round(w * 0.5, 1), h=mid_h),
        Room(name="Bathroom", x=round(w * 0.5, 1), y=front_h, w=round(w * 0.25, 1), h=mid_h),
        Room(name="Utility", x=round(w * 0.75, 1), y=front_h, w=round(w - w * 0.75, 1), h=mid_h),
    ]
    y0 = front_h + mid_h
    if beds == 0:
        rooms.append(Room(name="Study / store", x=0, y=y0, w=w, h=back_h))
    else:
        shown = min(beds, 4)
        bw = round(w / shown, 1)
        for i in range(shown):
            width = bw if i < shown - 1 else round(w - bw * (shown - 1), 1)
            rooms.append(Room(name=f"Bedroom {i + 1}", x=round(bw * i, 1), y=y0, w=width, h=back_h))
    return FloorPlan(width_ft=w, depth_ft=d, floor_label="Typical floor", rooms=rooms)
