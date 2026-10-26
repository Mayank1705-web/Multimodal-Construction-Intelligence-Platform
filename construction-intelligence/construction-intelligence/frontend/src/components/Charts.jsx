import { arr, num, str } from "../safe.js";

export function FloorPlanView({ plan }) {
  const rooms = arr(plan?.rooms).filter((r) => num(r.w) > 0 && num(r.h) > 0);
  const W = num(plan?.width_ft), D = num(plan?.depth_ft);
  if (!rooms.length || W <= 0 || D <= 0) return <div className="empty">No floor plan was produced for this project.</div>;

  const scale = Math.min(560 / W, 440 / D);
  const pad = 34;
  const vw = W * scale + pad * 2, vh = D * scale + pad * 2;
  return (
    <div className="blueprint">
      <svg viewBox={`0 0 ${vw} ${vh}`} role="img" aria-label={`Floor plan, ${W} by ${D} feet`} width={vw}>
        <defs>
          <pattern id="grid" width={scale * 5} height={scale * 5} patternUnits="userSpaceOnUse">
            <path d={`M ${scale * 5} 0 L 0 0 0 ${scale * 5}`} fill="none" stroke="#ffffff" strokeOpacity="0.12" />
          </pattern>
        </defs>
        <rect x={pad} y={pad} width={W * scale} height={D * scale} fill="url(#grid)" />
        {rooms.map((r, i) => {
          const x = pad + num(r.x) * scale, y = pad + num(r.y) * scale, w = num(r.w) * scale, h = num(r.h) * scale;
          const small = w < 70 || h < 40;
          return (
            <g key={i}>
              <rect x={x} y={y} width={w} height={h} fill="#ffffff" fillOpacity="0.07" stroke="#ffffff" strokeWidth="2" />
              <text x={x + w / 2} y={y + h / 2 - 3} textAnchor="middle" fill="#fff" fontSize={small ? 10 : 13} fontFamily="IBM Plex Sans, sans-serif">
                {str(r.name)}
              </text>
              <text x={x + w / 2} y={y + h / 2 + 13} textAnchor="middle" fill="#cfe0ef" fontSize="10" fontFamily="IBM Plex Sans, sans-serif">
                {num(r.w).toFixed(0)} x {num(r.h).toFixed(0)} ft
              </text>
            </g>
          );
        })}
        <text x={pad + (W * scale) / 2} y={pad - 12} textAnchor="middle" fill="#cfe0ef" fontSize="12">{W} ft</text>
        <text x={pad - 12} y={pad + (D * scale) / 2} textAnchor="middle" fill="#cfe0ef" fontSize="12" transform={`rotate(-90 ${pad - 12} ${pad + (D * scale) / 2})`}>{D} ft</text>
      </svg>
    </div>
  );
}

const PHASE_COLORS = ["#2b5c8a", "#c2570c", "#2e7d4f", "#7a5600", "#6b4c9a", "#1f7a80", "#8a1c15"];

export function GanttChart({ tasks }) {
  const list = arr(tasks).filter((t) => num(t.end_day) > num(t.start_day));
  if (!list.length) return <div className="empty">No schedule was produced.</div>;
  const total = Math.max(...list.map((t) => num(t.end_day)), 1);
  const labelW = 230, rowH = 30, chartW = 560, top = 28;
  const phases = [...new Set(list.map((t) => t.phase))];
  const x = (d) => labelW + (d / total) * chartW;
  const ticks = Array.from({ length: 6 }, (_, i) => Math.round((total / 5) * i));
  return (
    <div className="chart-wrap">
      <svg width={labelW + chartW + 20} height={top + list.length * rowH + 8} role="img" aria-label="Project schedule">
        {ticks.map((d) => (
          <g key={d}>
            <line x1={x(d)} x2={x(d)} y1={top - 6} y2={top + list.length * rowH} stroke="#d9dde0" />
            <text x={x(d)} y={14} textAnchor="middle" fontSize="11" fill="#5b646b">day {d}</text>
          </g>
        ))}
        {list.map((t, i) => {
          const y = top + i * rowH;
          const color = PHASE_COLORS[phases.indexOf(t.phase) % PHASE_COLORS.length];
          return (
            <g key={t.id}>
              <text x={labelW - 8} y={y + 18} textAnchor="end" fontSize="12.5" fill="#1d2125">
                {str(t.name).length > 32 ? `${str(t.name).slice(0, 31)}...` : str(t.name)}
              </text>
              <rect x={x(num(t.start_day))} y={y + 5} width={Math.max(x(num(t.end_day)) - x(num(t.start_day)), 3)} height={rowH - 11} rx="3" fill={color}>
                <title>{`${t.name}: day ${t.start_day} to ${t.end_day} (${t.duration_days} days)`}</title>
              </rect>
            </g>
          );
        })}
      </svg>
      <div className="row" style={{ padding: "6px 8px", fontSize: 13 }}>
        {phases.map((p, i) => (
          <span key={p} style={{ flex: "0 0 auto" }}>
            <span style={{ display: "inline-block", width: 12, height: 12, background: PHASE_COLORS[i % PHASE_COLORS.length], marginRight: 6, borderRadius: 2 }} />
            {p}
          </span>
        ))}
      </div>
    </div>
  );
}
