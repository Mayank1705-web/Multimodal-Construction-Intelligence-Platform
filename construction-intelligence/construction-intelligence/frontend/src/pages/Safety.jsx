import { useState } from "react";
import { postForm } from "../api.js";
import { useAnalysis } from "../hooks.js";
import { arr, num, percent, str } from "../safe.js";
import { Chip, Dropzone, Empty, ErrorNote, Field, List, ResultHead, Spinner, Warnings } from "../components/ui.jsx";

const SITE_TYPES = ["General construction site", "High-rise building", "Road or bridge works", "Industrial plant", "Renovation or interior"];

export default function Safety() {
  const [files, setFiles] = useState([]);
  const [text, setText] = useState("");
  const [site, setSite] = useState(SITE_TYPES[0]);
  const { loading, result, error, run } = useAnalysis();
  const canRun = files.length > 0 || text.trim().length >= 10;

  const submit = (e) => {
    e.preventDefault();
    run(() => postForm("/api/safety/analyze", { description: text, site_type: site }, files));
  };
  const d = result?.data;

  return (
    <>
      <div className="page-head">
        <h1>Site safety monitoring</h1>
        <p>Upload site photos or describe conditions. The analysis lists hazards, PPE status and the action to take for each.</p>
      </div>
      <div className="workbench">
        <form className="panel stack" onSubmit={submit}>
          <Field label="Site type">
            <select value={site} onChange={(e) => setSite(e.target.value)}>
              {SITE_TYPES.map((s) => <option key={s}>{s}</option>)}
            </select>
          </Field>
          <Dropzone files={files} onChange={setFiles} />
          <Field label="Site notes" hint="Optional when a photo is attached. At least 10 characters when there is no photo.">
            <textarea value={text} onChange={(e) => setText(e.target.value)} maxLength={3000} placeholder="Example: Scaffold on the third floor has no toe boards. Two workers are not wearing helmets." />
          </Field>
          <button className="btn" disabled={loading || !canRun}>{loading ? <Spinner text="Analysing" /> : "Analyse site"}</button>
        </form>

        <div>
          <ErrorNote error={error} />
          {!d && !loading && !error ? <Empty>Results appear here. Add a photo or notes, then choose Analyse site.</Empty> : null}
          {d ? (
            <section className="panel" aria-live="polite">
              <ResultHead title="Safety review" meta={result.meta} critical={d.overall_risk === "Critical"} />
              <Warnings items={result.meta?.warnings} />
              <p><Chip kind="sev" value={d.overall_risk} /> overall risk, confidence {percent(d.confidence)}</p>
              <p>{str(d.summary)}</p>

              <div className="section-title">Hazards</div>
              {arr(d.hazards).length ? arr(d.hazards).map((h, i) => (
                <div className="item" key={i}>
                  <div className="item-top"><strong>{str(h.name)}</strong><Chip kind="sev" value={h.severity} /></div>
                  <dl className="kv">
                    <dt>Location</dt><dd>{str(h.location)}</dd>
                    <dt>Finding</dt><dd>{str(h.description)}</dd>
                    <dt>Action</dt><dd>{str(h.corrective_action)}</dd>
                  </dl>
                </div>
              )) : <p>No hazards identified.</p>}

              <div className="section-title">PPE check</div>
              <div className="table-scroll">
                <table className="data">
                  <thead><tr><th>Item</th><th>Status</th><th>Note</th></tr></thead>
                  <tbody>
                    {arr(d.ppe).map((p, i) => (
                      <tr key={i}><td>{str(p.item)}</td><td><Chip kind="ok" value={p.status} /></td><td>{str(p.note)}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <List title="Recommendations" items={d.recommendations} />
              {d.limitations ? <p className="meta" style={{ marginTop: 14 }}>Limitations: {str(d.limitations)}</p> : null}
            </section>
          ) : null}
        </div>
      </div>
    </>
  );
}
