export const MODULES = [
  { id: "safety", title: "Site safety monitoring", text: "Hazards, PPE compliance and corrective actions from site photos and notes." },
  { id: "cracks", title: "Crack detection and analysis", text: "Crack type, severity, probable cause and repair guidance." },
  { id: "planning", title: "Project planning", text: "Floor layout, materials, cost and a dependency-checked schedule." },
  { id: "valuation", title: "Real estate valuation", text: "Indicative value range with the factors that drive it." },
  { id: "assistant", title: "Daily site assistant", text: "A prioritised checklist and warnings for today's work." },
  { id: "weather", title: "Weather advisory", text: "Live forecast turned into go, caution or hold calls." },
  { id: "knowledge", title: "Construction knowledge", text: "Technical answers with the standards to verify." },
];

export default function Overview({ go, health }) {
  return (
    <>
      <div className="page-head">
        <h1>Multimodal Construction Intelligence Platform</h1>
        <p>Decision support for construction professionals. Analyse photos, text and project data in one place, with structured reports your team can act on.</p>
      </div>
      {health?.demo_mode ? (
        <div className="warn">The backend is running in demo mode. Results come from a rule-based stand-in, not a vision model. Set LLM_PROVIDER and a key in backend/.env to use the real model.</div>
      ) : null}
      <div className="module-grid">
        {MODULES.map((m) => (
          <button key={m.id} className="module-card" onClick={() => go(m.id)}>
            <h3>{m.title}</h3>
            <p>{m.text}</p>
          </button>
        ))}
      </div>
    </>
  );
}
