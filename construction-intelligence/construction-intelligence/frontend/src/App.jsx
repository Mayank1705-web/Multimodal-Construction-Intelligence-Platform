import { Component, useEffect, useState } from "react";
import { getJson } from "./api.js";
import Overview, { MODULES } from "./pages/Overview.jsx";
import Safety from "./pages/Safety.jsx";
import Cracks from "./pages/Cracks.jsx";
import Planning from "./pages/Planning.jsx";
import Valuation from "./pages/Valuation.jsx";
import Assistant from "./pages/Assistant.jsx";
import Weather from "./pages/Weather.jsx";
import Knowledge from "./pages/Knowledge.jsx";
import History from "./pages/History.jsx";
import Architecture from "./pages/Architecture.jsx";

const PAGES = { safety: Safety, cracks: Cracks, planning: Planning, valuation: Valuation, assistant: Assistant, weather: Weather, knowledge: Knowledge, history: History, architecture: Architecture };

class Boundary extends Component {
  state = { failed: false };
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidCatch(err) { console.error(err); }
  render() {
    if (this.state.failed) {
      return (
        <div className="error" role="alert">
          <strong>This page failed to display.</strong>
          <div>The rest of the app still works. Choose another module, or reload and try again.</div>
          <button className="btn small" style={{ marginTop: 10 }} onClick={() => this.setState({ failed: false })}>Retry</button>
        </div>
      );
    }
    return this.props.children;
  }
}

const NAV = [
  ["Overview", [["overview", "Dashboard"], ["architecture", "Architecture"]]],
  ["Analysis", [["safety", "Site safety"], ["cracks", "Crack analysis"]]],
  ["Planning", [["planning", "Project planning"], ["valuation", "Valuation"]]],
  ["Daily work", [["assistant", "Daily assistant"], ["weather", "Weather advisory"], ["knowledge", "Knowledge"]]],
  ["Records", [["history", "History"]]],
];

export default function App() {
  const [page, setPage] = useState(() => window.location.hash.slice(1) || "overview");
  const [health, setHealth] = useState(null);

  useEffect(() => { getJson("/api/health").catch(() => null).then(setHealth); }, []);
  useEffect(() => {
    const onHash = () => setPage(window.location.hash.slice(1) || "overview");
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const go = (id) => { window.location.hash = id; setPage(id); window.scrollTo(0, 0); };

  const Page = PAGES[page];
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-bar" />
          <div className="brand-name">Construction Intelligence</div>
          <div className="brand-sub">Multimodal decision support</div>
        </div>
        <nav className="nav" aria-label="Modules">
          {NAV.map(([group, items]) => (
            <div key={group} style={{ display: "contents" }}>
              <div className="nav-group">{group}</div>
              {items.map(([id, label]) => (
                <button key={id} aria-current={page === id ? "page" : undefined} onClick={() => go(id)}>{label}</button>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-foot">
          {health === null ? "Checking server" : health?.status === "ok" ? (health.demo_mode ? "Server online, demo mode" : `Server online, ${health.provider}`) : "Server offline"}
        </div>
      </aside>
      <main className="main" id="content">
        <Boundary key={page}>{Page ? <Page /> : <Overview go={go} health={health} />}</Boundary>
      </main>
    </div>
  );
}
export { MODULES };
