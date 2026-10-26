import { useState } from "react";
import { postJson } from "../api.js";
import { useAnalysis } from "../hooks.js";
import { arr, num, str } from "../safe.js";
import { Chip, Empty, ErrorNote, Field, List, ResultHead, Spinner } from "../components/ui.jsx";

const DEFAULTS = ["Concrete pouring", "Crane operations", "Roofing", "Excavation", "Painting"];

export default function Weather() {
  const [loc, setLoc] = useState("");
  const [acts, setActs] = useState(DEFAULTS.slice(0, 4));
  const { loading, result, error, run } = useAnalysis();
  const d = result?.data;
  const toggle = (a) => setActs(acts.includes(a) ? acts.filter((x) => x !== a) : [...acts, a]);

  return (
    <>
      <div className="page-head">
        <h1>Weather advisory</h1>
        <p>Live five-day forecast for the site location, with a go, caution or hold call for each activity.</p>
      </div>
      <div className="workbench">
        <form className="panel stack" onSubmit={(e) => { e.preventDefault(); run(() => postJson("/api/weather/advisory", { location: loc, activities: acts })); }}>
          <Field label="Site location"><input type="text" value={loc} onChange={(e) => setLoc(e.target.value)} placeholder="City or town" /></Field>
          <fieldset style={{ border: 0, padding: 0, margin: 0 }}>
            <legend style={{ fontWeight: 500, fontSize: 14, marginBottom: 6 }}>Activities to assess</legend>
            {DEFAULTS.map((a) => (
              <label key={a} style={{ display: "block", padding: "3px 0" }}><input type="checkbox" checked={acts.includes(a)} onChange={() => toggle(a)} style={{ marginRight: 8 }} />{a}</label>
            ))}
          </fieldset>
          <button className="btn" disabled={loading || loc.trim().length < 2 || !acts.length}>{loading ? <Spinner text="Fetching forecast" /> : "Get advisory"}</button>
        </form>
        <div>
          <ErrorNote error={error} />
          {!d && !loading && !error ? <Empty>Enter a location to see the forecast and advisory.</Empty> : null}
          {d ? (
            <section className="panel" aria-live="polite">
              <ResultHead title={str(d.location)} meta={result.meta} />
              <p><Chip kind="ov" value={d.overall} /> {str(d.summary)}</p>
              <div className="stat-grid">
                <div className="stat"><span>Temperature now</span><strong>{num(d.current?.temperature_c)} C</strong></div>
                <div className="stat"><span>Humidity</span><strong>{num(d.current?.humidity_pct)}%</strong></div>
                <div className="stat"><span>Wind</span><strong>{num(d.current?.wind_kph)} km/h</strong></div>
                <div className="stat"><span>Rain now</span><strong>{num(d.current?.precipitation_mm)} mm</strong></div>
              </div>
              <div className="section-title">Forecast</div>
              <div className="table-scroll"><table className="data">
                <thead><tr><th>Date</th><th className="n">High C</th><th className="n">Low C</th><th className="n">Rain mm</th><th className="n">Wind km/h</th></tr></thead>
                <tbody>{arr(d.forecast).map((x, i) => <tr key={i}><td>{str(x.date)}</td><td className="n">{num(x.temp_max_c)}</td><td className="n">{num(x.temp_min_c)}</td><td className="n">{num(x.precipitation_mm)}</td><td className="n">{num(x.wind_max_kph)}</td></tr>)}</tbody>
              </table></div>
              <div className="section-title">Activities</div>
              {arr(d.activities).map((a, i) => (
                <div className="item" key={i}><div className="item-top"><strong>{str(a.activity)}</strong><Chip kind="go" value={a.suitability} /></div><p style={{ margin: 0 }}>{str(a.reason)}</p><p style={{ margin: 0 }}><strong>{str(a.recommendation)}</strong></p></div>
              ))}
              <List title="Precautions" items={d.precautions} />
            </section>
          ) : null}
        </div>
      </div>
    </>
  );
}
