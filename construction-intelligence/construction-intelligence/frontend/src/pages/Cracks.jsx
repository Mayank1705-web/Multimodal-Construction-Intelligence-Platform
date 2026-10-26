import { useState } from "react";
import { postForm } from "../api.js";
import { useAnalysis } from "../hooks.js";
import { arr, num, percent, str } from "../safe.js";
import { Chip, Dropzone, Empty, ErrorNote, Field, List, ResultHead, Spinner, Warnings } from "../components/ui.jsx";

const ELEMENTS = ["Wall", "Column", "Beam", "Slab or ceiling", "Foundation or plinth", "Floor", "Retaining wall"];

export default function Cracks() {
  const [files, setFiles] = useState([]);
  const [text, setText] = useState("");
  const [element, setElement] = useState(ELEMENTS[0]);
  const [age, setAge] = useState("");
  const { loading, result, error, run } = useAnalysis();
  const canRun = files.length > 0 || text.trim().length >= 10;
  const d = result?.data;

  return (
    <>
      <div className="page-head">
        <h1>Crack detection and analysis</h1>
        <p>Add close-up photos with a coin or ruler for scale. The report classifies each crack, rates severity and lists causes and repairs.</p>
      </div>
      <div className="workbench">
        <form className="panel stack" onSubmit={(e) => { e.preventDefault(); run(() => postForm("/api/cracks/analyze", { description: text, element_type: element, age_months: age }, files)); }}>
          <div className="row">
            <Field label="Element"><select value={element} onChange={(e) => setElement(e.target.value)}>{ELEMENTS.map((x) => <option key={x}>{x}</option>)}</select></Field>
            <Field label="Age in months"><input type="number" min="0" max="1200" value={age} onChange={(e) => setAge(e.target.value)} placeholder="Optional" /></Field>
          </div>
          <Dropzone files={files} onChange={setFiles} label="Drop crack photos here or click to choose" />
          <Field label="Observations" hint="Width, direction, whether it is growing, any leakage or stains.">
            <textarea value={text} onChange={(e) => setText(e.target.value)} maxLength={3000} placeholder="Example: Diagonal crack from the window corner, about 3 mm wide, appeared after the monsoon." />
          </Field>
          <button className="btn" disabled={loading || !canRun}>{loading ? <Spinner text="Analysing" /> : "Analyse cracks"}</button>
        </form>

        <div>
          <ErrorNote error={error} />
          {!d && !loading && !error ? <Empty>Results appear here after you add a photo or observations.</Empty> : null}
          {d ? (
            <section className="panel" aria-live="polite">
              <ResultHead title="Crack report" meta={result.meta} critical={d.overall_severity === "Critical"} />
              <Warnings items={result.meta?.warnings} />
              {d.needs_engineer_review ? <div className="error" role="alert">A structural engineer should inspect this before any repair.</div> : null}
              <p style={{ marginTop: 10 }}>
                {d.crack_detected ? <><Chip kind="sev" value={d.overall_severity} /> overall severity. </> : <strong>No crack detected. </strong>}
                Confidence {percent(d.confidence)}.
              </p>
              <p><strong>Structural risk:</strong> {str(d.structural_risk)}</p>
              <p>{str(d.summary)}</p>
              {arr(d.cracks).map((c, i) => (
                <div className="item" key={i}>
                  <div className="item-top"><strong>{str(c.type)}</strong><Chip kind="sev" value={c.severity} /></div>
                  <dl className="kv">
                    <dt>Location</dt><dd>{str(c.location)}</dd>
                    <dt>Orientation</dt><dd>{str(c.orientation)}</dd>
                    <dt>Estimated width</dt><dd>{c.estimated_width_mm == null ? "Not judgeable" : `${num(c.estimated_width_mm)} mm`}</dd>
                  </dl>
                  <List title="Probable causes" items={c.probable_causes} />
                  <List title="Recommended actions" items={c.recommended_actions} />
                </div>
              ))}
              <List title="Monitoring plan" items={d.monitoring_plan} />
              {d.limitations ? <p className="meta" style={{ marginTop: 14 }}>Limitations: {str(d.limitations)}</p> : null}
            </section>
          ) : null}
        </div>
      </div>
    </>
  );
}
