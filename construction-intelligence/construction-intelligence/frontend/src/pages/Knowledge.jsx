import { useState } from "react";
import { postJson } from "../api.js";
import { useAnalysis } from "../hooks.js";
import { str } from "../safe.js";
import { Empty, ErrorNote, Field, List, ResultHead, Spinner } from "../components/ui.jsx";

const EXAMPLES = ["What is the minimum curing period for OPC concrete?", "When is a slump test required on site?", "How do I check bar spacing before a slab pour?"];

export default function Knowledge() {
  const [q, setQ] = useState("");
  const { loading, result, error, run } = useAnalysis();
  const d = result?.data;
  return (
    <>
      <div className="page-head">
        <h1>Construction knowledge</h1>
        <p>Ask a technical question. Answers name the standards to verify rather than quoting clauses.</p>
      </div>
      <div className="workbench">
        <form className="panel stack" onSubmit={(e) => { e.preventDefault(); run(() => postJson("/api/knowledge/ask", { question: q })); }}>
          <Field label="Your question"><textarea value={q} onChange={(e) => setQ(e.target.value)} maxLength={2000} /></Field>
          <div className="row" style={{ gap: 6 }}>
            {EXAMPLES.map((x) => <button type="button" key={x} className="btn ghost small" style={{ flex: "0 0 auto", textAlign: "left" }} onClick={() => setQ(x)}>{x}</button>)}
          </div>
          <button className="btn" disabled={loading || q.trim().length < 5}>{loading ? <Spinner text="Answering" /> : "Ask"}</button>
        </form>
        <div>
          <ErrorNote error={error} />
          {!d && !loading && !error ? <Empty>The answer appears here.</Empty> : null}
          {d ? (
            <section className="panel" aria-live="polite">
              <ResultHead title="Answer" meta={result.meta} />
              <p>{str(d.answer)}</p>
              <List title="Key points" items={d.key_points} />
              <List title="Standards to check" items={d.standards_to_check} />
              <List title="Follow-up questions" items={d.follow_up_questions} />
            </section>
          ) : null}
        </div>
      </div>
    </>
  );
}
