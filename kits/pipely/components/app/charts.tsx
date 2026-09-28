"use client";

import { useId } from "react";

/* ── Mini line chart with a soft area fill (bespoke inline SVG) ────────────── */
export function MiniLineChart({
  data,
  color = "var(--color-primary)",
  height = 56,
  className,
}: {
  data: number[];
  color?: string;
  height?: number;
  className?: string;
}) {
  const id = useId().replace(/:/g, "");
  const w = 200;
  const h = height;
  const pad = 4;
  const max = Math.max(...data);
  const min = Math.min(...data);
  const span = max - min || 1;
  const step = (w - pad * 2) / (data.length - 1);
  const pts = data.map((v, i) => {
    const x = pad + i * step;
    const y = pad + (1 - (v - min) / span) * (h - pad * 2);
    return [x, y] as const;
  });
  const line = pts.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
  const area = `${line} L${pts[pts.length - 1][0].toFixed(1)} ${h - pad} L${pts[0][0].toFixed(1)} ${h - pad} Z`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className={className} preserveAspectRatio="none" style={{ width: "100%", height }}>
      <defs>
        <linearGradient id={`fill-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#fill-${id})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
      <circle cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]} r="2.6" fill={color} />
    </svg>
  );
}

/* ── Forecast chart — closed (solid) + weighted pipeline (faded) stacked bars,
   with a smooth target line over the top. All hand-rolled inline SVG. ─────── */
export function ForecastChart({
  closed,
  weighted,
  labels,
  height = 180,
}: {
  closed: number[];
  weighted: number[];
  labels: string[];
  height?: number;
}) {
  const id = useId().replace(/:/g, "");
  const w = 560;
  const h = height;
  const padX = 14;
  const padTop = 14;
  const padBottom = 24;
  const totals = closed.map((c, i) => c + weighted[i]);
  const max = Math.max(...totals) * 1.05 || 1;
  const innerH = h - padTop - padBottom;
  const slot = (w - padX * 2) / closed.length;
  const barW = Math.min(34, slot * 0.5);

  const yOf = (v: number) => padTop + (1 - v / max) * innerH;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", height }} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`wfill-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--color-primary)" stopOpacity="0.32" />
          <stop offset="100%" stopColor="var(--color-primary)" stopOpacity="0.08" />
        </linearGradient>
      </defs>
      {/* gridlines */}
      {[0.25, 0.5, 0.75, 1].map((g) => (
        <line key={g} x1={padX} x2={w - padX} y1={padTop + g * innerH} y2={padTop + g * innerH} stroke="var(--color-border)" strokeWidth="1" />
      ))}
      {closed.map((c, i) => {
        const cx = padX + slot * i + slot / 2;
        const x = cx - barW / 2;
        const cy = yOf(c);
        const wy = yOf(c + weighted[i]);
        return (
          <g key={i}>
            {/* weighted (open) portion on top — faded */}
            {weighted[i] > 0 && (
              <rect x={x} y={wy} width={barW} height={cy - wy} rx="3" fill={`url(#wfill-${id})`} stroke="var(--color-primary)" strokeOpacity="0.35" strokeDasharray="3 3" strokeWidth="1" />
            )}
            {/* closed (committed) portion */}
            {c > 0 && (
              <rect x={x} y={cy} width={barW} height={padTop + innerH - cy} rx="3" fill="var(--color-primary)" />
            )}
            <text x={cx} y={h - 7} textAnchor="middle" fontSize="9.5" fill="var(--color-muted-foreground)" fontFamily="var(--font-mono)">
              {labels[i]}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

/* ── Multi-color segmented bar (pipeline by stage / value split) ──────────── */
export function SegmentedBar({
  segments,
  className,
}: {
  segments: { label: string; value: number; color: string }[];
  className?: string;
}) {
  const total = segments.reduce((s, x) => s + x.value, 0) || 1;
  return (
    <div className={className}>
      <div className="flex h-2.5 w-full overflow-hidden rounded-full bg-muted">
        {segments.map((s, i) => (
          <span
            key={s.label}
            title={`${s.label} · ${Math.round((s.value / total) * 100)}%`}
            style={{ width: `${(s.value / total) * 100}%`, background: s.color, marginLeft: i === 0 ? 0 : 1.5 }}
            className="h-full first:rounded-l-full last:rounded-r-full"
          />
        ))}
      </div>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5">
        {segments.map((s) => (
          <span key={s.label} className="inline-flex items-center gap-1.5 text-[11.5px] text-muted-foreground">
            <span className="h-2 w-2 rounded-full" style={{ background: s.color }} />
            {s.label}
            <span className="tnum text-foreground/70">{Math.round((s.value / total) * 100)}%</span>
          </span>
        ))}
      </div>
    </div>
  );
}

/* ── Radial progress ring (quota attainment) ───────────────────────────────── */
export function RadialProgress({
  pct,
  size = 96,
  stroke = 9,
  color = "var(--color-primary)",
  label,
}: {
  pct: number;
  size?: number;
  stroke?: number;
  color?: string;
  label?: string;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const off = c * (1 - Math.min(pct, 100) / 100);
  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--color-muted)" strokeWidth={stroke} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={off}
        />
      </svg>
      <div className="absolute text-center">
        <p className="tnum text-lg font-bold leading-none">{Math.round(pct)}%</p>
        {label && <p className="mt-0.5 text-[9.5px] text-muted-foreground">{label}</p>}
      </div>
    </div>
  );
}
