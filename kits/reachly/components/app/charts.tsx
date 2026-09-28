"use client";

import { useId } from "react";

/* ── Mini sparkline with a soft area fill (bespoke inline SVG) ──────────────── */
export function Sparkline({
  data,
  color = "var(--color-primary)",
  height = 40,
  className,
}: {
  data: number[];
  color?: string;
  height?: number;
  className?: string;
}) {
  const id = useId().replace(/:/g, "");
  const w = 120;
  const h = height;
  const pad = 3;
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
        <linearGradient id={`spark-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.22" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#spark-${id})`} />
      <path d={line} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
      <circle cx={pts[pts.length - 1][0]} cy={pts[pts.length - 1][1]} r="2.4" fill={color} />
    </svg>
  );
}

/* ── Mini line chart (warmup / inflow style) ───────────────────────────────── */
export function MiniLineChart({
  data,
  color = "var(--color-primary)",
  height = 48,
  className,
}: {
  data: number[];
  color?: string;
  height?: number;
  className?: string;
}) {
  return <Sparkline data={data} color={color} height={height} className={className} />;
}

/* ── Dual-series area+bar chart (sending volume: sent vs replied) ───────────── */
export function VolumeChart({
  data,
  height = 170,
  sentColor = "var(--color-primary)",
  repliedColor = "var(--color-success)",
}: {
  data: { label: string; sent: number; replied: number }[];
  height?: number;
  sentColor?: string;
  repliedColor?: string;
}) {
  const id = useId().replace(/:/g, "");
  const w = 560;
  const h = height;
  const padX = 8;
  const padTop = 12;
  const padBottom = 24;
  const innerH = h - padTop - padBottom;
  const sent = data.map((d) => d.sent);
  const max = Math.max(...sent) * 1.08;
  const min = 0;
  const span = max - min || 1;
  const step = (w - padX * 2) / (data.length - 1);

  const sy = (v: number) => padTop + (1 - (v - min) / span) * innerH;
  const pts = data.map((d, i) => [padX + i * step, sy(d.sent)] as const);
  const line = pts.map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`).join(" ");
  const baseY = h - padBottom;
  const area = `${line} L${pts[pts.length - 1][0].toFixed(1)} ${baseY} L${pts[0][0].toFixed(1)} ${baseY} Z`;

  // replied = thin bars at the bottom, scaled to their own max for visibility
  const repliedMax = Math.max(...data.map((d) => d.replied)) || 1;
  const barW = Math.min(10, step * 0.42);

  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: "100%", height }} preserveAspectRatio="none">
      <defs>
        <linearGradient id={`vol-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={sentColor} stopOpacity="0.20" />
          <stop offset="100%" stopColor={sentColor} stopOpacity="0" />
        </linearGradient>
      </defs>
      {/* faint gridlines */}
      {[0.25, 0.5, 0.75].map((g) => (
        <line key={g} x1={padX} x2={w - padX} y1={padTop + g * innerH} y2={padTop + g * innerH} stroke="var(--color-border)" strokeWidth="1" />
      ))}
      {/* replied bars */}
      {data.map((d, i) => {
        const bh = (d.replied / repliedMax) * (innerH * 0.34);
        const x = padX + i * step - barW / 2;
        return <rect key={i} x={x} y={baseY - bh} width={barW} height={bh} rx={barW / 2} fill={repliedColor} opacity={0.32} />;
      })}
      {/* sent area + line */}
      <path d={area} fill={`url(#vol-${id})`} />
      <path d={line} fill="none" stroke={sentColor} strokeWidth="2.25" strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
      {pts.map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r={i === pts.length - 1 ? 3.2 : 2} fill="var(--color-card)" stroke={sentColor} strokeWidth="1.6" />
      ))}
      {data.map((d, i) =>
        i % 2 === 0 ? (
          <text key={d.label} x={padX + i * step} y={h - 7} textAnchor="middle" fontSize="9.5" fill="var(--color-muted-foreground)" fontFamily="var(--font-mono)">
            {d.label}
          </text>
        ) : null,
      )}
    </svg>
  );
}

/* ── Radial gauge (mailbox health / spam score) ────────────────────────────── */
export function Gauge({
  value,
  size = 120,
  stroke = 10,
  color = "var(--color-primary)",
  track = "var(--color-muted)",
  label,
  sub,
}: {
  value: number; // 0–100
  size?: number;
  stroke?: number;
  color?: string;
  track?: string;
  label?: string;
  sub?: string;
}) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  // 270° arc (3/4 circle), starting bottom-left
  const arc = 0.75;
  const dash = c * arc;
  const filled = (value / 100) * dash;

  return (
    <div className="relative grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-[135deg]">
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={track} strokeWidth={stroke} strokeLinecap="round" strokeDasharray={`${dash} ${c}`} />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${filled} ${c}`}
          style={{ transition: "stroke-dasharray 0.7s cubic-bezier(0.22,1,0.36,1)" }}
        />
      </svg>
      <div className="absolute inset-0 grid place-items-center text-center">
        <div>
          <p className="tnum text-2xl font-bold leading-none text-foreground">{label ?? `${value}`}</p>
          {sub && <p className="mt-1 text-[10.5px] text-muted-foreground">{sub}</p>}
        </div>
      </div>
    </div>
  );
}

/* ── Multi-color segmented bar ─────────────────────────────────────────────── */
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
            title={`${s.label} · ${s.value}`}
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
            <span className="tnum text-foreground/70">{s.value}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

/* ── Thin progress bar (campaign send progress) ────────────────────────────── */
export function ProgressBar({ value, className }: { value: number; className?: string }) {
  return (
    <div className={`h-1.5 w-full overflow-hidden rounded-full bg-muted ${className ?? ""}`}>
      <div className="h-full rounded-full" style={{ width: `${Math.max(0, Math.min(100, value))}%`, background: "var(--grad-brand)" }} />
    </div>
  );
}
