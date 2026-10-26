import { useState } from "react";
import { postJson } from "../api.js";
import { useAnalysis } from "../hooks.js";
import { arr, money, num, str } from "../safe.js";
import { Empty, ErrorNote, Field, List, ResultHead, Spinner, Warnings } from "../components/ui.jsx";
import { FloorPlanView, GanttChart } from "../components/Charts.jsx";

const INIT = { project_name: "Family residence", building_type: "Residential", plot_width_ft: 30, plot_depth_ft: 50, floors: 2, bedrooms: 3, quality: "Standard", city: "", currency: "INR", notes: "" };

export default function Planning() {
  const [f, setF] = useState(INIT);
  const { loading, result, error, run } = useAnalysis();
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const d = result?.data;
  const cur = d?.currency || "INR";

  const submit = (e) => {
    e.preventDefault();
    run(() => postJson("/api/planning/generate", {
      ...f, plot_width_ft: Number(f.plot_width_ft), plot_depth_ft: Number(f.plot_depth_ft), floors: Number(f.floors), bedrooms: Number(f.bedrooms),
    }));
  };
  const valid = Number(f.plot_width_ft) > 5 && Number(f.plot_depth_ft) > 5 && Number(f.floors) >= 1;

  return (
    <>
      <div className="page-head">
        <h1>Project planning</h1>
        <p>Enter the plot and specification. The platform produces a floor layout, material estimate, cost calculation and a dependency-checked schedule.</p>
      </div>
      <div className="workbench">
        <form className="panel stack" onSubmit={submit}>
          <Field label="Project name"><input type="text" value={f.project_name} onChange={set("project_name")} maxLength={120} /></Field>
          <div className="row">
            <Field label="Building type"><select value={f.building_type} onChange={set("building_type")}>{["Residential", "Commercial", "Industrial", "Institutional"].map((x) => <option key={x}>{x}</option>)}</select></Field>
            <Field label="Quality"><select value={f.quality} onChange={set("quality")}>{["Economy", "Standard", "Premium"].map((x) => <option key={x}>{x}</option>)}</select></Field>
          </div>
          <div className="row">
            <Field label="Plot width (ft)"><input type="number" min="6" value={f.plot_width_ft} onChange={set("plot_width_ft")} /></Field>
            <Field label="Plot depth (ft)"><input type="number" min="6" value={f.plot_depth_ft} onChange={set("plot_depth_ft")} /></Field>
          </div>
          <div className="row">
            <Field label="Floors"><input type="number" min="1" max="60" value={f.floors} onChange={set("floors")} /></Field>
            <Field label="Bedrooms"><input type="number" min="0" max="20" value={f.bedrooms} onChange={set("bedrooms")} /></Field>
          </div>
          <div className="row">
            <Field label="City"><input type="text" value={f.city} onChange={set("city")} placeholder="Bhopal" /></Field>
            <Field label="Currency"><select value={f.currency} onChange={set("currency")}>{["INR", "USD", "EUR", "GBP", "AED"].map((x) => <option key={x}>{x}</option>)}</select></Field>
          </div>
          <Field label="Notes"><textarea value={f.notes} onChange={set("notes")} maxLength={1500} placeholder="Vastu preferences, parking, budget limit, soil condition" /></Field>
          <button className="btn" disabled={loading || !valid}>{loading ? <Spinner text="Planning" /> : "Generate plan"}</button>
        </form>

        <div>
          <ErrorNote error={error} />
          {!d && !loading && !error ? <Empty>The plan appears here once you generate it.</Empty> : null}
          {d ? (
            <section className="panel" aria-live="polite">
              <ResultHead title={str(d.project_name, "Project plan")} meta={result.meta} />
              <Warnings items={result.meta?.warnings} />
              <p>{str(d.summary)}</p>
              <div className="stat-grid">
                <div className="stat"><span>Total cost</span><strong>{money(d.cost?.total, cur)}</strong></div>
                <div className="stat"><span>Cost per sq ft built</span><strong>{money(d.cost?.cost_per_sqft, cur)}</strong></div>
                <div className="stat"><span>Duration</span><strong>{num(d.total_duration_days)} days</strong></div>
              </div>

              <div className="section-title">Floor layout</div>
              <FloorPlanView plan={d.floor_plan} />
              <List title="Elevation notes" items={d.elevation_notes} />

              <div className="section-title">Schedule</div>
              <GanttChart tasks={d.tasks} />

              <div className="section-title">Cost breakdown</div>
              <div className="table-scroll"><table className="data"><tbody>
                {[["Materials", d.cost?.materials], ["Labour", d.cost?.labour], ["Equipment", d.cost?.equipment], ["Permits and overheads", d.cost?.permits_and_overheads], ["Contingency", d.cost?.contingency]].map(([k, v]) => (
                  <tr key={k}><td>{k}</td><td className="n">{money(v, cur)}</td></tr>
                ))}
                <tr><th>Total</th><th className="n">{money(d.cost?.total, cur)}</th></tr>
              </tbody></table></div>

              <div className="section-title">Material estimate</div>
              <div className="table-scroll"><table className="data">
                <thead><tr><th>Item</th><th className="n">Quantity</th><th>Unit</th><th className="n">Unit cost</th><th className="n">Total</th></tr></thead>
                <tbody>{arr(d.materials).map((m, i) => (
                  <tr key={i}><td>{str(m.item)}</td><td className="n">{num(m.quantity).toLocaleString()}</td><td>{str(m.unit)}</td><td className="n">{money(m.unit_cost, cur)}</td><td className="n">{money(m.total_cost, cur)}</td></tr>
                ))}</tbody>
              </table></div>
              <List title="Project risks" items={d.risks} />
              <p className="meta" style={{ marginTop: 14 }}>Quantities and rates are planning estimates. Confirm with a quantity surveyor and local rate schedules before budgeting.</p>
            </section>
          ) : null}
        </div>
      </div>
    </>
  );
}
