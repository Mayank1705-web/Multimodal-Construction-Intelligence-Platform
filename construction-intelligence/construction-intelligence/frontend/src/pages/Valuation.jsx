import { useState } from "react";
import { postJson } from "../api.js";
import { useAnalysis } from "../hooks.js";
import { arr, money, percent, str } from "../safe.js";
import { Chip, Empty, ErrorNote, Field, List, ResultHead, Spinner } from "../components/ui.jsx";

const AMENITIES = ["Parking", "Lift", "Security", "Garden", "Gym", "Power backup", "Club house", "Swimming pool"];
const INIT = { property_type: "Apartment", city: "", locality: "", area_sqft: 1200, bedrooms: 2, age_years: 3, floor: 2, condition: "Good", currency: "INR", amenities: [], notes: "" };

export default function Valuation() {
  const [f, setF] = useState(INIT);
  const { loading, result, error, run } = useAnalysis();
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const toggle = (a) => setF({ ...f, amenities: f.amenities.includes(a) ? f.amenities.filter((x) => x !== a) : [...f.amenities, a] });
  const d = result?.data;
  const valid = f.city.trim().length >= 2 && Number(f.area_sqft) > 0;

  const submit = (e) => {
    e.preventDefault();
    run(() => postJson("/api/valuation/estimate", { ...f, area_sqft: Number(f.area_sqft), bedrooms: Number(f.bedrooms), age_years: Number(f.age_years), floor: Number(f.floor) }));
  };

  return (
    <>
      <div className="page-head">
        <h1>Real estate valuation</h1>
        <p>Get an indicative value range with the factors that move it. This is not a certified valuation.</p>
      </div>
      <div className="workbench">
        <form className="panel stack" onSubmit={submit}>
          <div className="row">
            <Field label="Property type"><select value={f.property_type} onChange={set("property_type")}>{["Apartment", "Independent House", "Villa", "Plot", "Commercial"].map((x) => <option key={x}>{x}</option>)}</select></Field>
            <Field label="Condition"><select value={f.condition} onChange={set("condition")}>{["Poor", "Fair", "Good", "Excellent"].map((x) => <option key={x}>{x}</option>)}</select></Field>
          </div>
          <div className="row">
            <Field label="City"><input type="text" value={f.city} onChange={set("city")} placeholder="Bhopal" /></Field>
            <Field label="Locality"><input type="text" value={f.locality} onChange={set("locality")} placeholder="Optional" /></Field>
          </div>
          <div className="row">
            <Field label="Area (sq ft)"><input type="number" min="1" value={f.area_sqft} onChange={set("area_sqft")} /></Field>
            <Field label="Bedrooms"><input type="number" min="0" value={f.bedrooms} onChange={set("bedrooms")} /></Field>
          </div>
          <div className="row">
            <Field label="Age (years)"><input type="number" min="0" value={f.age_years} onChange={set("age_years")} /></Field>
            <Field label="Floor"><input type="number" min="0" value={f.floor} onChange={set("floor")} /></Field>
            <Field label="Currency"><select value={f.currency} onChange={set("currency")}>{["INR", "USD", "EUR", "GBP", "AED"].map((x) => <option key={x}>{x}</option>)}</select></Field>
          </div>
          <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
            <legend style={{ fontWeight: 500, fontSize: 14, marginBottom: 6 }}>Amenities</legend>
            <div className="row" style={{ gap: 6 }}>
              {AMENITIES.map((a) => (
                <label key={a} style={{ flex: "0 0 auto", border: "1px solid var(--line)", borderRadius: 4, padding: "4px 9px", background: f.amenities.includes(a) ? "#dbe7f2" : "#fff", cursor: "pointer", fontSize: 14 }}>
                  <input type="checkbox" checked={f.amenities.includes(a)} onChange={() => toggle(a)} style={{ marginRight: 6 }} />{a}
                </label>
              ))}
            </div>
          </fieldset>
          <Field label="Notes"><textarea value={f.notes} onChange={set("notes")} maxLength={1500} placeholder="Road width, corner plot, view, legal status" /></Field>
          <button className="btn" disabled={loading || !valid}>{loading ? <Spinner text="Estimating" /> : "Estimate value"}</button>
        </form>

        <div>
          <ErrorNote error={error} />
          {!d && !loading && !error ? <Empty>The estimate appears here after you enter the property details.</Empty> : null}
          {d ? (
            <section className="panel" aria-live="polite">
              <ResultHead title="Valuation estimate" meta={result.meta} />
              <div className="stat-grid">
                <div className="stat"><span>Low</span><strong>{money(d.estimated_value_low, d.currency)}</strong></div>
                <div className="stat"><span>Most likely</span><strong>{money(d.estimated_value_mid, d.currency)}</strong></div>
                <div className="stat"><span>High</span><strong>{money(d.estimated_value_high, d.currency)}</strong></div>
                <div className="stat"><span>Per sq ft</span><strong>{money(d.price_per_sqft, d.currency)}</strong></div>
              </div>
              <p style={{ marginTop: 12 }}>{str(d.summary)} Confidence {percent(d.confidence)}.</p>
              <div className="section-title">Factors</div>
              {arr(d.factors).map((x, i) => (
                <div className="item" key={i}><div className="item-top"><strong>{str(x.factor)}</strong><Chip kind="imp" value={x.impact} /></div><span>{str(x.note)}</span></div>
              ))}
              <List title="Assumptions" items={d.assumptions} />
              <p className="meta" style={{ marginTop: 14 }}>{str(d.disclaimer)}</p>
            </section>
          ) : null}
        </div>
      </div>
    </>
  );
}
