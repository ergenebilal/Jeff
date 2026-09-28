"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  Plus,
  ChevronDown,
  Filter,
  Search,
  ArrowUpRight,
  ArrowDownRight,
  Phone,
  Mail,
  CalendarClock,
  CheckSquare,
  Check,
  Trophy,
  GripVertical,
  Clock,
} from "lucide-react";
import { Avatar } from "@/components/app/avatar";
import { ForecastChart, RadialProgress } from "@/components/app/charts";
import { useLang } from "@/components/i18n/language-provider";
import { cn, formatMoney } from "@/lib/utils";
import {
  stages,
  deals as seedDeals,
  kpis,
  summary,
  contacts,
  activities,
  forecast,
  forecastMeta,
  leaderboard,
  reps,
  repById,
  stageById,
  type Deal,
  type StageId,
  type ActivityKind,
} from "@/lib/demo/data";

const ACTIVITY_ICON: Record<ActivityKind, typeof Phone> = {
  call: Phone,
  email: Mail,
  meeting: CalendarClock,
  task: CheckSquare,
};

function fmtDate(iso: string, lang: "tr" | "en") {
  const d = new Date(iso);
  return d.toLocaleDateString(lang === "tr" ? "tr-TR" : "en-US", { day: "2-digit", month: "short" });
}

function fmtTime(iso: string) {
  const d = new Date(iso);
  const hh = String(d.getUTCHours()).padStart(2, "0");
  const mm = String(d.getUTCMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}

export default function DashboardPage() {
  const { t, lang } = useLang();
  const [deals, setDeals] = useState<Deal[]>(seedDeals);
  const [dragId, setDragId] = useState<string | null>(null);
  const [overStage, setOverStage] = useState<StageId | null>(null);
  const [justMoved, setJustMoved] = useState<string | null>(null);
  const [ownerFilter, setOwnerFilter] = useState<string | "all">("all");
  const [query, setQuery] = useState("");
  const [doneIds, setDoneIds] = useState<Set<string>>(
    () => new Set(activities.filter((a) => a.done).map((a) => a.id)),
  );

  // ── Derived stats (recompute as deals move / filter changes) ─────────────
  const visibleDeals = useMemo(
    () =>
      deals.filter(
        (d) =>
          (ownerFilter === "all" || d.ownerId === ownerFilter) &&
          (!query ||
            d.company.toLowerCase().includes(query.toLowerCase()) ||
            d.title.toLowerCase().includes(query.toLowerCase())),
      ),
    [deals, ownerFilter, query],
  );

  const openDeals = visibleDeals.filter((d) => d.stage !== "won");
  const wonDeals = visibleDeals.filter((d) => d.stage === "won");
  const pipelineValue = openDeals.reduce((s, d) => s + d.value, 0);
  const winRate = visibleDeals.length ? Math.round((wonDeals.length / visibleDeals.length) * 100) : 0;
  const avgDeal = visibleDeals.length ? Math.round(visibleDeals.reduce((s, d) => s + d.value, 0) / visibleDeals.length) : 0;

  const liveKpis = [
    { ...kpis[0], value: formatMoney(pipelineValue) },
    { ...kpis[1], value: String(openDeals.length) },
    { ...kpis[2], value: `${winRate}%` },
    { ...kpis[3], value: formatMoney(avgDeal) },
  ];

  function move(id: string, to: StageId) {
    setDeals((prev) => prev.map((d) => (d.id === id ? { ...d, stage: to, daysInStage: 0 } : d)));
    setJustMoved(id);
    setTimeout(() => setJustMoved((v) => (v === id ? null : v)), 600);
  }

  const wonValue = summary.wonThisMonth;
  const quotaPct = Math.round((wonValue / summary.quota) * 100);

  return (
    <div className="mx-auto max-w-[1500px] animate-fade-in space-y-6">
      {/* ── Page header ──────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight">
            {lang === "tr" ? "Satış paneli" : "Sales cockpit"}
          </h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {lang === "tr"
              ? "Pipeline'ını taşı, aktiviteleri kapat, tahmini takip et."
              : "Move your pipeline, clear activities, track the forecast."}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {/* owner filter */}
          <div className="relative">
            <select
              value={ownerFilter}
              onChange={(e) => setOwnerFilter(e.target.value)}
              className="h-9 appearance-none rounded-lg border border-border bg-card pl-3 pr-8 text-[13px] font-medium text-foreground shadow-pill transition-colors hover:bg-muted focus:outline-none"
            >
              <option value="all">{lang === "tr" ? "Tüm sahipler" : "All owners"}</option>
              {reps.map((r) => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
            <ChevronDown className="pointer-events-none absolute right-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          </div>
          <button className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3.5 text-[13px] font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90">
            <Plus className="h-4 w-4" />
            {lang === "tr" ? "Deal ekle" : "Add deal"}
          </button>
        </div>
      </div>

      {/* ── Stat row ─────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {liveKpis.map((k) => {
          const up = (k.delta ?? 0) >= 0;
          return (
            <div key={t(k.label)} className="rounded-2xl border border-border bg-card p-4 shadow-soft">
              <div className="flex items-center justify-between">
                <p className="text-[12.5px] font-medium text-muted-foreground">{t(k.label)}</p>
                {k.icon && (
                  <span className="grid h-7 w-7 place-items-center rounded-lg bg-primary/10 text-primary">
                    <KpiGlyph name={k.icon} />
                  </span>
                )}
              </div>
              <div className="mt-2 flex items-end justify-between">
                <p className="tnum text-2xl font-bold leading-none">{k.value}</p>
                {k.delta !== undefined && k.delta !== 0 && (
                  <span className={cn("inline-flex items-center gap-0.5 text-[11px] font-semibold", up ? "text-success" : "text-destructive")}>
                    {up ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                    {Math.abs(k.delta).toFixed(1)}%
                  </span>
                )}
              </div>
              {k.hint && <p className="mt-1.5 text-[11px] text-muted-foreground">{t(k.hint)}</p>}
            </div>
          );
        })}
      </div>

      {/* ── Pipeline kanban ──────────────────────────────────────────────── */}
      <div className="rounded-2xl border border-border bg-card p-4 shadow-soft sm:p-5">
        <div className="mb-4 flex flex-wrap items-center gap-2.5">
          <h2 className="font-display text-[15px] font-semibold tracking-tight">
            {lang === "tr" ? "Deal pipeline" : "Deal pipeline"}
          </h2>
          <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
            {lang === "tr" ? "sürükle-bırak" : "drag & drop"}
          </span>
          <div className="ml-auto flex items-center gap-2">
            <div className="flex h-9 items-center gap-2 rounded-lg border border-border bg-card px-3 text-sm">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={lang === "tr" ? "Deal ara…" : "Search deals…"}
                className="w-28 bg-transparent text-foreground placeholder:text-muted-foreground/70 focus:outline-none sm:w-36"
              />
            </div>
            <button className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-border bg-card px-3 text-[13px] font-medium text-foreground transition-colors hover:bg-muted">
              <Filter className="h-3.5 w-3.5 text-muted-foreground" />
              {lang === "tr" ? "Filtre" : "Filter"}
            </button>
          </div>
        </div>

        <div className="grid gap-3 lg:grid-cols-5">
          {stages.map((st) => {
            const colDeals = visibleDeals.filter((d) => d.stage === st.id);
            const colValue = colDeals.reduce((s, d) => s + d.value, 0);
            const isWon = st.id === "won";
            return (
              <div
                key={st.id}
                onDragOver={(e) => {
                  e.preventDefault();
                  setOverStage(st.id);
                }}
                onDragLeave={() => setOverStage((s) => (s === st.id ? null : s))}
                onDrop={() => {
                  if (dragId) move(dragId, st.id);
                  setDragId(null);
                  setOverStage(null);
                }}
                className={cn(
                  "flex min-h-[260px] flex-col rounded-xl border p-2 transition-colors",
                  isWon ? "border-success/40 bg-success/[0.04]" : "border-border bg-muted/40",
                  overStage === st.id && "border-primary/60 bg-primary/[0.06] ring-1 ring-primary/30",
                )}
              >
                {/* column header */}
                <div className="mb-2 flex items-center gap-2 px-1.5 pt-1">
                  {isWon ? (
                    <Trophy className="h-3.5 w-3.5 text-success" />
                  ) : (
                    <span className="h-2 w-2 rounded-full" style={{ background: st.color }} />
                  )}
                  <span className="text-[12px] font-semibold">{t(st.label)}</span>
                  <span className="ml-auto rounded-full bg-card px-1.5 py-0.5 text-[10px] font-semibold text-muted-foreground tnum">
                    {colDeals.length}
                  </span>
                </div>
                <p className="mb-2 px-1.5 tnum text-[11px] font-medium text-muted-foreground">{formatMoney(colValue)}</p>

                {/* cards */}
                <div className="flex-1 space-y-2">
                  {colDeals.map((d) => {
                    const rep = repById[d.ownerId];
                    const stalled = d.daysInStage >= 10 && !isWon;
                    return (
                      <div
                        key={d.id}
                        draggable
                        onDragStart={() => setDragId(d.id)}
                        onDragEnd={() => setDragId(null)}
                        className={cn(
                          "group cursor-grab rounded-lg border border-border bg-card p-2.5 shadow-pill transition-shadow hover:shadow-soft active:cursor-grabbing",
                          justMoved === d.id && "won-pop",
                        )}
                      >
                        <div className="flex items-start gap-1">
                          <GripVertical className="mt-0.5 h-3.5 w-3.5 shrink-0 text-muted-foreground/40" />
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-[12.5px] font-semibold leading-tight">{d.company}</p>
                            <p className="truncate text-[11px] text-muted-foreground">{d.title}</p>
                          </div>
                        </div>
                        <div className="mt-2 flex items-center justify-between pl-1">
                          <span className="tnum text-[13px] font-bold">{formatMoney(d.value)}</span>
                          <Avatar initials={rep.initials} color={rep.color} size={20} />
                        </div>
                        <div className="mt-1.5 flex items-center gap-1 pl-1">
                          <Clock className={cn("h-3 w-3", stalled ? "text-warning-foreground" : "text-muted-foreground")} />
                          <span className={cn("text-[10.5px]", stalled ? "font-semibold text-warning-foreground" : "text-muted-foreground")}>
                            {d.daysInStage}
                            {lang === "tr" ? " gün" : "d"} {lang === "tr" ? "bu aşamada" : "in stage"}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                  {colDeals.length === 0 && (
                    <div className="grid h-16 place-items-center rounded-lg border border-dashed border-border text-[11px] text-muted-foreground">
                      {lang === "tr" ? "buraya bırak" : "drop here"}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Two-column: forecast + leaderboard ───────────────────────────── */}
      <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
        {/* Forecast */}
        <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-display text-[15px] font-semibold tracking-tight">{t(forecastMeta.title)}</h3>
              <p className="text-xs text-muted-foreground">{t(forecastMeta.subtitle)}</p>
            </div>
            <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success">
              <ArrowUpRight className="h-3 w-3" />
              {forecastMeta.delta}
            </span>
          </div>
          <div className="mt-3 flex items-end gap-4">
            <p className="tnum text-2xl font-bold leading-none">{formatMoney(pipelineValue)}</p>
            <span className="mb-0.5 text-[12px] text-muted-foreground">
              {lang === "tr" ? "ağırlıklı açık pipeline" : "weighted open pipeline"}
            </span>
          </div>
          <div className="mt-4">
            <ForecastChart
              closed={forecast.map((f) => f.closed)}
              weighted={forecast.map((f) => f.weighted)}
              labels={forecast.map((f) => f.label)}
              height={180}
            />
          </div>
          <div className="mt-3 flex items-center gap-5 text-[11.5px] text-muted-foreground">
            <span className="inline-flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm bg-primary" />
              {lang === "tr" ? "Kapanan" : "Closed"}
            </span>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-sm border border-dashed border-primary/50 bg-primary/15" />
              {lang === "tr" ? "Ağırlıklı pipeline" : "Weighted pipeline"}
            </span>
          </div>
        </div>

        {/* Leaderboard */}
        <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <div className="flex items-center justify-between">
            <h3 className="font-display text-[15px] font-semibold tracking-tight">
              {lang === "tr" ? "Temsilci sıralaması" : "Rep leaderboard"}
            </h3>
            <span className="label-mono text-muted-foreground">{lang === "tr" ? "bu çeyrek" : "this qtr"}</span>
          </div>
          <div className="mt-4 space-y-3.5">
            {leaderboard.map((row, i) => {
              const rep = repById[row.repId];
              const pct = Math.min(100, Math.round((row.wonValue / row.quota) * 100));
              return (
                <div key={row.repId}>
                  <div className="mb-1.5 flex items-center gap-2.5">
                    <span className="w-4 text-center text-[11px] font-bold text-muted-foreground tnum">{i + 1}</span>
                    <Avatar initials={rep.initials} color={rep.color} size={26} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[13px] font-semibold leading-tight">{rep.name}</p>
                      <p className="text-[11px] text-muted-foreground">
                        {row.won} {lang === "tr" ? "kazanıldı" : "won"} · {row.winRate}% {lang === "tr" ? "oran" : "rate"}
                      </p>
                    </div>
                    <span className="tnum text-[13px] font-bold">{formatMoney(row.wonValue)}</span>
                  </div>
                  <div className="ml-[26px] h-1.5 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full" style={{ width: `${pct}%`, background: rep.color }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Two-column: deals list · right rail (quota, contacts, tasks) ─── */}
      <div className="grid gap-6 xl:grid-cols-[1.4fr_1fr]">
        {/* Deals list view */}
        <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
          <div className="flex items-center justify-between border-b border-border p-4">
            <h3 className="font-display text-[15px] font-semibold tracking-tight">
              {lang === "tr" ? "Açık deal'ler" : "Open deals"}
            </h3>
            <Link href="/deals" className="inline-flex items-center gap-1 text-[13px] font-medium text-primary hover:underline">
              {lang === "tr" ? "Pipeline'ı aç" : "Open pipeline"}
              <ArrowUpRight className="h-3.5 w-3.5" />
            </Link>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="label-mono py-2.5 pl-4 font-medium text-muted-foreground">{lang === "tr" ? "Deal" : "Deal"}</th>
                  <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Aşama" : "Stage"}</th>
                  <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Sahip" : "Owner"}</th>
                  <th className="label-mono py-2.5 pr-4 text-right font-medium text-muted-foreground">{lang === "tr" ? "Değer" : "Value"}</th>
                </tr>
              </thead>
              <tbody>
                {openDeals.slice(0, 7).map((d) => {
                  const rep = repById[d.ownerId];
                  const st = stageById[d.stage];
                  return (
                    <tr key={d.id} className="border-b border-border/60 transition-colors last:border-0 hover:bg-muted/50">
                      <td className="py-3 pl-4">
                        <p className="font-semibold leading-tight">{d.company}</p>
                        <p className="text-xs text-muted-foreground">{d.title} · {fmtDate(d.closeDate, lang)}</p>
                      </td>
                      <td className="py-3">
                        <span
                          className="inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-semibold"
                          style={{ background: `color-mix(in oklch, ${st.color} 14%, transparent)`, color: st.color }}
                        >
                          <span className="h-1.5 w-1.5 rounded-full" style={{ background: st.color }} />
                          {t(st.label)}
                        </span>
                      </td>
                      <td className="py-3">
                        <span className="inline-flex items-center gap-1.5">
                          <Avatar initials={rep.initials} color={rep.color} size={22} />
                          <span className="hidden text-[12px] text-muted-foreground sm:inline">{rep.name.split(" ")[0]}</span>
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-right">
                        <span className="tnum font-bold">{formatMoney(d.value)}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right rail: quota ring + contacts + activities */}
        <div className="space-y-6">
          {/* Quota card */}
          <div className="flex items-center gap-4 rounded-2xl border border-border bg-card p-5 shadow-soft">
            <RadialProgress pct={quotaPct} size={88} label={lang === "tr" ? "kota" : "of quota"} />
            <div className="min-w-0">
              <p className="text-[13px] font-medium text-muted-foreground">{lang === "tr" ? "Bu ay kazanılan" : "Won this month"}</p>
              <p className="mt-1 tnum text-xl font-bold leading-none">{formatMoney(wonValue)}</p>
              <p className="mt-1.5 text-[11.5px] text-muted-foreground">
                {formatMoney(summary.quota - wonValue)} {lang === "tr" ? "kotaya kaldı" : "to quota"}
              </p>
            </div>
          </div>

          {/* Contacts panel */}
          <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
            <div className="flex items-center justify-between border-b border-border p-4">
              <h3 className="font-display text-[15px] font-semibold tracking-tight">
                {lang === "tr" ? "Kişiler" : "Contacts"}
              </h3>
              <Link href="/contacts" className="inline-flex items-center gap-1 text-[13px] font-medium text-primary hover:underline">
                {lang === "tr" ? "Tümü" : "View all"}
                <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            </div>
            <div className="divide-y divide-border/60">
              {contacts.slice(0, 4).map((c) => (
                <div key={c.id} className="flex items-center gap-3 px-4 py-3">
                  <Avatar initials={c.initials} color={c.color} size={32} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] font-semibold">{c.name}</p>
                    <p className="truncate text-[11.5px] text-muted-foreground">{c.title} · {c.company}</p>
                  </div>
                  <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-semibold text-primary">
                    {c.openDeals} {lang === "tr" ? "deal" : "deals"}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Activities / tasks panel */}
          <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
            <div className="flex items-center justify-between border-b border-border p-4">
              <h3 className="font-display text-[15px] font-semibold tracking-tight">
                {lang === "tr" ? "Bugünkü görevler" : "Today's tasks"}
              </h3>
              <span className="rounded-full bg-warning/15 px-2 py-0.5 text-[11px] font-semibold text-warning-foreground">
                {activities.length - doneIds.size} {lang === "tr" ? "açık" : "due"}
              </span>
            </div>
            <div className="divide-y divide-border/60">
              {activities.map((a) => {
                const I = ACTIVITY_ICON[a.kind];
                const done = doneIds.has(a.id);
                return (
                  <button
                    key={a.id}
                    onClick={() =>
                      setDoneIds((prev) => {
                        const next = new Set(prev);
                        if (next.has(a.id)) next.delete(a.id);
                        else next.add(a.id);
                        return next;
                      })
                    }
                    className="flex w-full items-center gap-3 px-4 py-3 text-left transition-colors hover:bg-muted/50"
                  >
                    <span
                      className={cn(
                        "grid h-7 w-7 shrink-0 place-items-center rounded-lg transition-colors",
                        done ? "bg-success text-success-foreground" : "bg-muted text-muted-foreground",
                      )}
                    >
                      {done ? <Check className="h-3.5 w-3.5" strokeWidth={3} /> : <I className="h-3.5 w-3.5" />}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className={cn("truncate text-[13px] font-medium leading-tight", done && "text-muted-foreground line-through")}>
                        {t(a.title)}
                      </p>
                      <p className="truncate text-[11.5px] text-muted-foreground">{a.who} · {a.company}</p>
                    </div>
                    <span className="tnum shrink-0 text-[11.5px] text-muted-foreground">{fmtTime(a.due)}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/* Tiny inline icon glyphs for the KPI chips (avoids a dynamic import per card). */
function KpiGlyph({ name }: { name: string }) {
  const map: Record<string, React.ReactNode> = {
    layers: <path d="M12 2 2 7l10 5 10-5-10-5Z M2 12l10 5 10-5 M2 17l10 5 10-5" />,
    kanban: <path d="M6 5v11 M12 5v6 M18 5v9" />,
    trophy: <path d="M7 4h10v4a5 5 0 0 1-10 0V4Z M5 5H3v1a3 3 0 0 0 3 3 M19 5h2v1a3 3 0 0 1-3 3 M10 16h4v3h-4z M8 21h8" />,
    "dollar-sign": <path d="M12 2v20 M17 6.5a4 4 0 0 0-4-2.5h-1.5a3.5 3.5 0 0 0 0 7h3a3.5 3.5 0 0 1 0 7H10a4 4 0 0 1-4-2.5" />,
  };
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
      {map[name] ?? map.layers}
    </svg>
  );
}
