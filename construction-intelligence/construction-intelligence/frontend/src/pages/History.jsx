import { useCallback, useEffect, useState } from "react";
import { del, getJson } from "../api.js";
import { arr, str } from "../safe.js";
import { Empty, ErrorNote, Spinner } from "../components/ui.jsx";

const KINDS = ["", "safety", "cracks", "planning", "valuation", "assistant", "weather", "knowledge"];

export default function History() {
  const [kind, setKind] = useState("");
  const [items, setItems] = useState(null);
  const [open, setOpen] = useState(null);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      const body = await getJson(`/api/history${kind ? `?kind=${kind}` : ""}`);
      setItems(arr(body.data));
    } catch (e) {
      setItems([]);
      setError({ title: "History unavailable", message: e.message });
    }
  }, [kind]);
  useEffect(() => { load(); }, [load]);

  async function view(id) {
    try { setOpen((await getJson(`/api/history/${id}`)).data); } catch (e) { setError({ title: "Record unavailable", message: e.message }); }
  }
  async function remove(id) {
    try { await del(`/api/history/${id}`); if (open?.id === id) setOpen(null); load(); } catch (e) { setError({ title: "Delete failed", message: e.message }); }
  }

  return (
    <>
      <div className="page-head"><h1>Analysis history</h1><p>Every analysis is stored in the platform database so reports can be reviewed later.</p></div>
      <div className="workbench">
        <div className="panel">
          <label className="field">Module
            <select value={kind} onChange={(e) => { setKind(e.target.value); setOpen(null); }}>
              {KINDS.map((k) => <option key={k} value={k}>{k || "All modules"}</option>)}
            </select>
          </label>
          <div style={{ marginTop: 12 }}>
            {items === null ? <Spinner text="Loading" /> : items.length === 0 ? <Empty>No saved analyses yet.</Empty> : items.map((it) => (
              <div className="item" key={it.id}>
                <div className="item-top"><strong>{str(it.title)}</strong></div>
                <div className="meta">{str(it.kind)} - {str(it.created_at).replace("T", " ").slice(0, 16)} UTC</div>
                <div className="row" style={{ marginTop: 8 }}>
                  <button className="btn small" style={{ flex: "0 0 auto" }} onClick={() => view(it.id)}>Open</button>
                  <button className="btn small ghost" style={{ flex: "0 0 auto" }} onClick={() => remove(it.id)}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div>
          <ErrorNote error={error} />
          {open ? (
            <section className="panel">
              <h2>{str(open.title)}</h2>
              <p className="meta">Provider: {str(open.provider)}</p>
              <div className="section-title">Request</div>
              <pre style={{ overflow: "auto", background: "#fff", border: "1px solid var(--line)", padding: 10, borderRadius: 4 }}>{JSON.stringify(open.request, null, 2)}</pre>
              <div className="section-title">Result</div>
              <pre style={{ overflow: "auto", background: "#fff", border: "1px solid var(--line)", padding: 10, borderRadius: 4, maxHeight: 520 }}>{JSON.stringify(open.result, null, 2)}</pre>
            </section>
          ) : <Empty>Select a record to see its request and result.</Empty>}
        </div>
      </div>
    </>
  );
}
