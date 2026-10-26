import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { FloorPlanView, GanttChart } from "../components/Charts.jsx";
import { ApiError, postJson } from "../api.js";
import { arr, money, num, str } from "../safe.js";

describe("safe helpers", () => {
  it("never throw on bad values", () => {
    expect(arr(null)).toEqual([]);
    expect(arr("x")).toEqual([]);
    expect(num(NaN, 3)).toBe(3);
    expect(str(null, "none")).toBe("none");
    expect(money(undefined, "BAD")).toBeTruthy();
  });
});

describe("charts survive malformed data", () => {
  it("floor plan with nothing", () => {
    render(<FloorPlanView plan={null} />);
    expect(screen.getByText(/No floor plan/)).toBeTruthy();
  });
  it("floor plan with junk rooms", () => {
    render(<FloorPlanView plan={{ width_ft: 20, depth_ft: 20, rooms: [{ name: 5, x: "a", y: null, w: -1, h: 0 }] }} />);
    expect(screen.getByText(/No floor plan/)).toBeTruthy();
  });
  it("floor plan renders valid rooms", () => {
    render(<FloorPlanView plan={{ width_ft: 20, depth_ft: 20, rooms: [{ name: "Hall", x: 0, y: 0, w: 10, h: 10 }] }} />);
    expect(screen.getByText("Hall")).toBeTruthy();
  });
  it("gantt with nothing", () => {
    render(<GanttChart tasks={undefined} />);
    expect(screen.getByText(/No schedule/)).toBeTruthy();
  });
  it("gantt renders tasks", () => {
    render(<GanttChart tasks={[{ id: "T1", name: "Excavation", phase: "Site", start_day: 0, end_day: 5, duration_days: 5 }]} />);
    expect(screen.getByText("Excavation")).toBeTruthy();
  });
});

describe("api client", () => {
  it("maps network failure to a readable error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("down")));
    await expect(postJson("/api/x", {})).rejects.toMatchObject({ code: "network" });
  });
  it("maps non-JSON responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 502, json: () => Promise.reject(new Error("x")) }));
    await expect(postJson("/api/x", {})).rejects.toBeInstanceOf(ApiError);
  });
  it("surfaces server error messages", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, status: 422, json: () => Promise.resolve({ status: "error", error: { code: "no_input", message: "Add input" } }) }));
    await expect(postJson("/api/x", {})).rejects.toMatchObject({ code: "no_input", message: "Add input" });
  });
});
