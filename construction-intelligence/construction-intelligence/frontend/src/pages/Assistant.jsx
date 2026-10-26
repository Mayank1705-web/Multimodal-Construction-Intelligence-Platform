import { useState } from "react";
import { postJson } from "../api.js";
import { useAnalysis } from "../hooks.js";
import { arr, str } from "../safe.js";
import { Chip, Empty, ErrorNote, Field, List, ResultHead, Spinner } from "../components/ui.jsx";

export default function Assistant() {
  const [f, setF] = useState({ message: "", project_name: "", phase: "Structure", crew_size: "", issues: "" });
  const { loading, result, error, run } = useAnalysis();
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });
  const d = result?.data;

  const submit = (e) => {
    e.preventDefault();
    run(() => postJson("/api/assistant/daily", {
      message: f.message, project_name: f.project_name, phase: f.phase, crew_size: Number(f.crew_size) || 0,
      open_issues: f.issues.split("\n").map((s) => s.trim()).filter(Boolean),
    }));
  };

  return (
    <>
      <div className="page-head">
        <h1>Daily site assistant</h1>
        <p>Describe today's work. You get a direct answer, a prioritised checklist and warnings for open issues.</p>
      </div>
      <div className="workbench">
        <form className="panel stack" onSubmit={submit}>
          <Field label="What is happening on site today?"><textarea value={f.message} onChange={set("message")} maxLength={3000} placeholder="Example: We plan to pour the second floor slab this afternoon with 25 workers." /></Field>
          <div className="row">
            <Field label="Project"><input type="text" value={f.project_name} onChange={set("project_name")} /></Field>
            <Field label="Phase"><select value={f.phase} onChange={set("phase")}>{["Site preparation", "Foundation", "Structure", "Masonry", "MEP", "Finishing", "Handover"].map((x) => <option key={x}>{x}</option>)}</select></Field>
          </div>
          <Field label="Crew size"><input type="number" min="0" value={f.crew_size} onChange={set("crew_size")} /></Field>
          <Field label="Open issues" hint="One per line"><textarea value={f.issues} onChange={set("issues")} style={{ minHeight: 70 }} /></Field>
          <button className="btn" disabled={loading || f.message.trim().length < 3}>{loading ? <Spinner text="Thinking" /> : "Get site guidance"}</button>
        </form>
        <div>
          <ErrorNote error={error} />
          {!d && !loading && !error ? <Empty>Guidance appears here.</Empty> : null}
          {d ? (
            <section className="panel" aria-live="polite">
              <ResultHead title="Site guidance" meta={result.meta} />
              <p>{str(d.answer)}</p>
              <div className="section-title">Checklist</div>
              {arr(d.checklist).map((c, i) => (
                <div className="item" key={i}><div className="item-top"><strong>{str(c.task)}</strong><Chip kind="sev" value={c.priority} /></div><span className="meta">Owner: {str(c.owner)}</span></div>
              ))}
              <List title="Warnings" items={d.warnings} />
              <List title="Questions to settle" items={d.follow_up_questions} />
            </section>
          ) : null}
        </div>
      </div>
    </>
  );
}
