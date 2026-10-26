import { useEffect, useRef, useState } from "react";
import { str } from "../safe.js";

export function Field({ label, hint, children }) {
  return (
    <label className="field">
      <span>{label}</span>
      {children}
      {hint ? <small>{hint}</small> : null}
    </label>
  );
}

export function Spinner({ text = "Working" }) {
  return (
    <span role="status">
      <span className="spinner" aria-hidden="true" />
      {text}
    </span>
  );
}

export function ErrorNote({ error }) {
  if (!error) return null;
  return (
    <div className="error" role="alert">
      <strong>{error.title || "Something went wrong"}</strong>
      <div>{error.message}</div>
    </div>
  );
}

export function Chip({ kind, value }) {
  const v = str(value, "Unknown");
  return <span className={`chip ${kind}-${v}`}>{v}</span>;
}

export function Empty({ children }) {
  return <div className="empty">{children}</div>;
}

export function Warnings({ items }) {
  const list = Array.isArray(items) ? items : [];
  return list.map((w, i) => (
    <div className="warn" key={i}>
      {w}
    </div>
  ));
}

export function ResultHead({ title, meta, critical }) {
  return (
    <div className={`result-head ${critical ? "critical" : ""}`}>
      <h2>{title}</h2>
      <div className="meta">
        {meta?.provider === "mock" ? <span className="badge-demo">Demo output</span> : null}{" "}
        {meta?.latency_ms != null ? `${(meta.latency_ms / 1000).toFixed(1)} s` : ""}
        {meta?.record_id ? ` - saved as record ${meta.record_id}` : ""}
      </div>
    </div>
  );
}

export function List({ items, title }) {
  const list = Array.isArray(items) ? items.filter(Boolean) : [];
  if (!list.length) return null;
  return (
    <>
      {title ? <div className="section-title">{title}</div> : null}
      <ul className="plain">
        {list.map((x, i) => (
          <li key={i}>{str(x)}</li>
        ))}
      </ul>
    </>
  );
}

const MAX_FILES = 4;
const TYPES = ["image/jpeg", "image/png", "image/webp"];

export function Dropzone({ files, onChange, label = "Drop site photos here or click to choose" }) {
  const input = useRef(null);
  const [over, setOver] = useState(false);
  const [problem, setProblem] = useState("");
  const [urls, setUrls] = useState([]);

  useEffect(() => {
    const next = files.map((f) => URL.createObjectURL(f));
    setUrls(next);
    return () => next.forEach((u) => URL.revokeObjectURL(u));
  }, [files]);

  function add(list) {
    const incoming = Array.from(list || []);
    const bad = incoming.filter((f) => !TYPES.includes(f.type));
    const good = incoming.filter((f) => TYPES.includes(f.type));
    let msg = bad.length ? `${bad.length} file(s) skipped. Use JPEG, PNG or WebP.` : "";
    const merged = [...files, ...good];
    if (merged.length > MAX_FILES) msg = `Only ${MAX_FILES} images are allowed per analysis.`;
    setProblem(msg);
    onChange(merged.slice(0, MAX_FILES));
  }

  return (
    <div>
      <div
        className={`drop ${over ? "over" : ""}`}
        role="button"
        tabIndex={0}
        aria-label={label}
        onClick={() => input.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), input.current?.click())}
        onDragOver={(e) => (e.preventDefault(), setOver(true))}
        onDragLeave={() => setOver(false)}
        onDrop={(e) => (e.preventDefault(), setOver(false), add(e.dataTransfer.files))}
      >
        <p>{label}</p>
        <p>
          <small>JPEG, PNG or WebP, up to {MAX_FILES} images, 8 MB each</small>
        </p>
        <input ref={input} type="file" accept={TYPES.join(",")} multiple hidden onChange={(e) => (add(e.target.files), (e.target.value = ""))} />
      </div>
      {problem ? <div className="warn" style={{ marginTop: 8 }}>{problem}</div> : null}
      {files.length ? (
        <div className="thumbs">
          {files.map((f, i) => (
            <div className="thumb" key={`${f.name}-${i}`}>
              <img src={urls[i]} alt={f.name} />
              <button type="button" aria-label={`Remove ${f.name}`} onClick={() => onChange(files.filter((_, j) => j !== i))}>
                x
              </button>
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}
