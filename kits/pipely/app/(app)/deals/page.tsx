"use client";

import { useMemo, useState } from "react";
import {
  Plus,
  Search,
  Filter,
  LayoutGrid,
  List,
  Trophy,
  GripVertical,
  Clock,
  ChevronDown,
} from "lucide-react";
import { Avatar } from "@/components/app/avatar";
import { useLang } from "@/components/i18n/language-provider";
import { cn, formatMoney } from "@/lib/utils";
import {
  stages,
  deals as seedDeals,
  reps,
  repById,
  stageById,
  type Deal,
  type StageId,
} from "@/lib/demo/data";

function fmtDate(iso: string, lang: "tr" | "en") {
  return new Date(iso).toLocaleDateString(lang === "tr" ? "tr-TR" : "en-US", { day: "2-digit", month: "short" });
}

export default function DealsPage() {
  const { t, lang } = useLang();
  const [deals, setDeals] = useState<Deal[]>(seedDeals);
  const [view, setView] = useState<"board" | "list">("board");
  const [dragId, setDragId] = useState<string | null>(null);
  const [overStage, setOverStage] = useState<StageId | null>(null);
  const [justMoved, setJustMoved] = useState<string | null>(null);
  const [ownerFilter, setOwnerFilter] = useState<string | "all">("all");
  const [query, setQuery] = useState("");

  const visible = useMemo(
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

  const totalOpen = visible.filter((d) => d.stage !== "won").reduce((s, d) => s + d.value, 0);

  function move(id: string, to: StageId) {
    setDeals((prev) => prev.map((d) => (d.id === id ? { ...d, stage: to, daysInStage: 0 } : d)));
    setJustMoved(id);
    setTimeout(() => setJustMoved((v) => (v === id ? null : v)), 600);
  }

  return (
    <div className="mx-auto max-w-[1500px] animate-fade-in space-y-6">
      {/* header */}
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight">{lang === "tr" ? "Pipeline" : "Pipeline"}</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {lang === "tr" ? "Açık pipeline" : "Open pipeline"}: <span className="tnum font-semibold text-foreground">{formatMoney(totalOpen)}</span> · {visible.length} {lang === "tr" ? "deal" : "deals"}
          </p>
        </div>
        <div className="ml-auto flex flex-wrap items-center gap-2">
          {/* view toggle */}
          <div className="inline-flex items-center rounded-lg border border-border bg-card p-0.5 shadow-pill">
            <button
              onClick={() => setView("board")}
              className={cn("inline-flex h-8 items-center gap-1.5 rounded-md px-2.5 text-[13px] font-medium transition-colors", view === "board" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground")}
            >
              <LayoutGrid className="h-3.5 w-3.5" /> {lang === "tr" ? "Pano" : "Board"}
            </button>
            <button
              onClick={() => setView("list")}
              className={cn("inline-flex h-8 items-center gap-1.5 rounded-md px-2.5 text-[13px] font-medium transition-colors", view === "list" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:text-foreground")}
            >
              <List className="h-3.5 w-3.5" /> {lang === "tr" ? "Liste" : "List"}
            </button>
          </div>
          <button className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3.5 text-[13px] font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90">
            <Plus className="h-4 w-4" /> {lang === "tr" ? "Deal ekle" : "Add deal"}
          </button>
        </div>
      </div>

      {/* toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex h-9 items-center gap-2 rounded-lg border border-border bg-card px-3 text-sm">
          <Search className="h-4 w-4 text-muted-foreground" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={lang === "tr" ? "Deal ya da şirket ara…" : "Search deals or companies…"}
            className="w-44 bg-transparent text-foreground placeholder:text-muted-foreground/70 focus:outline-none sm:w-56"
          />
        </div>
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
        <button className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-border bg-card px-3 text-[13px] font-medium text-foreground transition-colors hover:bg-muted">
          <Filter className="h-3.5 w-3.5 text-muted-foreground" /> {lang === "tr" ? "Filtre" : "Filter"}
        </button>
      </div>

      {/* board view */}
      {view === "board" ? (
        <div className="grid gap-3 lg:grid-cols-5">
          {stages.map((st) => {
            const colDeals = visible.filter((d) => d.stage === st.id);
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
                  "flex min-h-[400px] flex-col rounded-xl border p-2 transition-colors",
                  isWon ? "border-success/40 bg-success/[0.04]" : "border-border bg-muted/40",
                  overStage === st.id && "border-primary/60 bg-primary/[0.06] ring-1 ring-primary/30",
                )}
              >
                <div className="mb-2 flex items-center gap-2 px-1.5 pt-1">
                  {isWon ? <Trophy className="h-3.5 w-3.5 text-success" /> : <span className="h-2 w-2 rounded-full" style={{ background: st.color }} />}
                  <span className="text-[12px] font-semibold">{t(st.label)}</span>
                  <span className="ml-auto rounded-full bg-card px-1.5 py-0.5 text-[10px] font-semibold text-muted-foreground tnum">{colDeals.length}</span>
                </div>
                <p className="mb-2 px-1.5 tnum text-[11px] font-medium text-muted-foreground">{formatMoney(colValue)}</p>
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
                            {d.daysInStage}{lang === "tr" ? " gün" : "d"} · {fmtDate(d.closeDate, lang)}
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
      ) : (
        /* list view */
        <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border text-left">
                  <th className="label-mono py-2.5 pl-4 font-medium text-muted-foreground">{lang === "tr" ? "Deal" : "Deal"}</th>
                  <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Şirket" : "Company"}</th>
                  <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Aşama" : "Stage"}</th>
                  <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Sahip" : "Owner"}</th>
                  <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Kapanış" : "Close"}</th>
                  <th className="label-mono py-2.5 pr-4 text-right font-medium text-muted-foreground">{lang === "tr" ? "Değer" : "Value"}</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((d) => {
                  const rep = repById[d.ownerId];
                  const st = stageById[d.stage];
                  return (
                    <tr key={d.id} className="border-b border-border/60 transition-colors last:border-0 hover:bg-muted/50">
                      <td className="py-3 pl-4 font-semibold">{d.title}</td>
                      <td className="py-3 text-muted-foreground">{d.company}</td>
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
                      <td className="py-3 tnum text-[13px] text-muted-foreground">{fmtDate(d.closeDate, lang)}</td>
                      <td className="py-3 pr-4 text-right tnum font-bold">{formatMoney(d.value)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
