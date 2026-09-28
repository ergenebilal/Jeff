"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Search,
  Filter,
  ArrowUpDown,
  ArrowUpRight,
  ArrowDownRight,
  X,
  ThumbsUp,
  ThumbsDown,
  Plus,
  ShieldCheck,
  Clock,
  Eye,
  Quote,
  CheckCircle2,
} from "lucide-react";
import { AskBar } from "@/components/app/ask-bar";
import { SourceIcon, SourcePill, SOURCE_LABEL } from "@/components/app/source-icon";
import { AreaChart, GroupedBars, SegmentedBar, RadialGauge, MiniLineChart } from "@/components/app/charts";
import { Icon } from "@/components/ui/icon";
import { useLang } from "@/components/i18n/language-provider";
import { cn, formatNumber, formatCompact, formatRelative } from "@/lib/utils";
import {
  stats,
  documents,
  documentsMeta,
  STATUS_LABEL,
  docCitedIn,
  questions,
  questionsMeta,
  gaps,
  gapsMeta,
  verifications,
  verificationsMeta,
  usage,
  usageMeta,
  askedVsAnswered,
  sourceShare,
  activity,
  type DocRow,
} from "@/lib/demo/data";

function fmtDateTime(iso: string) {
  const d = new Date(iso);
  const day = d.getUTCDate();
  const mon = d.toLocaleString("en-US", { month: "short", timeZone: "UTC" });
  const hh = String(d.getUTCHours()).padStart(2, "0");
  const mm = String(d.getUTCMinutes()).padStart(2, "0");
  return `${day} ${mon} · ${hh}:${mm}`;
}

export default function DashboardPage() {
  const { t, lang } = useLang();
  const [selected, setSelected] = useState<string | null>("d1");
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [query, setQuery] = useState("");
  const [votes, setVotes] = useState<Record<string, "up" | "down" | null>>(
    Object.fromEntries(questions.map((q) => [q.id, q.vote])),
  );

  const rows = documents.filter(
    (d) =>
      !query ||
      d.title.toLowerCase().includes(query.toLowerCase()) ||
      SOURCE_LABEL[d.source].toLowerCase().includes(query.toLowerCase()),
  );
  const activeDoc = documents.find((d) => d.id === selected) ?? null;
  const docTitle = (id?: string) => documents.find((d) => d.id === id)?.title;

  function setVote(id: string, v: "up" | "down") {
    setVotes((prev) => ({ ...prev, [id]: prev[id] === v ? null : v }));
  }

  return (
    <div className="mx-auto max-w-[1500px] animate-fade-in">
      {/* Page header */}
      <div className="mb-6 flex flex-wrap items-end gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight">
            {lang === "tr" ? "Bilgi paneli" : "Knowledge cockpit"}
          </h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {lang === "tr"
              ? "Sor, kaynaklarını izle ve bilginin taze kalmasını sağla."
              : "Ask, monitor your sources and keep your knowledge fresh."}
          </p>
        </div>
        <Link
          href="/sources"
          className="ml-auto inline-flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3.5 text-[13px] font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90"
        >
          <Plus className="h-4 w-4" />
          {lang === "tr" ? "Kaynak bağla" : "Connect a source"}
        </Link>
      </div>

      {/* ── AI ask bar ────────────────────────────────────────────────── */}
      <div className="mb-6">
        <AskBar />
      </div>

      {/* ── Stat row ──────────────────────────────────────────────────── */}
      <div className="mb-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((k) => {
          const up = (k.delta ?? 0) >= 0;
          return (
            <div key={t(k.label)} className="rounded-2xl border border-border bg-card p-4 shadow-soft">
              <div className="flex items-center justify-between">
                <span className="grid h-9 w-9 place-items-center rounded-xl bg-primary/10 text-primary">
                  <Icon name={k.icon} className="h-[18px] w-[18px]" />
                </span>
                {k.delta !== undefined && k.delta !== 0 && (
                  <span className={cn("inline-flex items-center gap-0.5 text-[11px] font-semibold", up ? "text-success" : "text-destructive")}>
                    {up ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                    {Math.abs(k.delta).toFixed(1)}%
                  </span>
                )}
              </div>
              <p className="mt-3 tnum text-2xl font-bold leading-none">{k.value}</p>
              <p className="mt-1.5 text-[13px] font-medium text-foreground/90">{t(k.label)}</p>
              {k.hint && <p className="mt-0.5 line-clamp-1 text-[11.5px] text-muted-foreground">{t(k.hint)}</p>}
            </div>
          );
        })}
      </div>

      <div className={cn("grid gap-6", drawerOpen ? "xl:grid-cols-[1fr_360px]" : "grid-cols-1")}>
        {/* ── Main column ──────────────────────────────────────────── */}
        <div className="min-w-0 space-y-6">
          {/* Documents / sources list */}
          <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
            <div className="flex flex-wrap items-center gap-2.5 border-b border-border p-4">
              <div>
                <h2 className="font-display text-[15px] font-semibold tracking-tight">{t(documentsMeta.title)}</h2>
                <p className="text-xs text-muted-foreground">{t(documentsMeta.subtitle)}</p>
              </div>
              <div className="ml-auto flex flex-wrap items-center gap-2">
                <div className="flex h-9 items-center gap-2 rounded-lg border border-border bg-card px-3 text-sm">
                  <Search className="h-4 w-4 text-muted-foreground" />
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={lang === "tr" ? "Belge ara…" : "Search docs…"}
                    className="w-32 bg-transparent text-foreground placeholder:text-muted-foreground/70 focus:outline-none sm:w-40"
                  />
                </div>
                <button className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-border bg-card px-3 text-[13px] font-medium text-foreground transition-colors hover:bg-muted">
                  <Filter className="h-3.5 w-3.5 text-muted-foreground" />
                  {lang === "tr" ? "Filtre" : "Filter"}
                </button>
                <button className="inline-flex h-9 items-center gap-1.5 rounded-lg border border-border bg-card px-3 text-[13px] font-medium text-foreground transition-colors hover:bg-muted">
                  <ArrowUpDown className="h-3.5 w-3.5 text-muted-foreground" />
                  {lang === "tr" ? "Sırala" : "Sort"}
                </button>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left">
                    <th className="label-mono py-2.5 pl-4 font-medium text-muted-foreground">{lang === "tr" ? "Belge" : "Document"}</th>
                    <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Kaynak" : "Source"}</th>
                    <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Eşitlenme" : "Last synced"}</th>
                    <th className="label-mono py-2.5 text-right font-medium text-muted-foreground">{lang === "tr" ? "Görüntülenme" : "Views"}</th>
                    <th className="label-mono py-2.5 pr-4 text-right font-medium text-muted-foreground">{lang === "tr" ? "Durum" : "Status"}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((row) => {
                    const isSel = row.id === selected;
                    const st = STATUS_LABEL[row.status];
                    return (
                      <tr
                        key={row.id}
                        onClick={() => { setSelected(row.id); setDrawerOpen(true); }}
                        className={cn(
                          "cursor-pointer border-b border-border/60 transition-colors last:border-0",
                          isSel ? "bg-primary/[0.04]" : "hover:bg-muted/50",
                        )}
                      >
                        <td className="py-3 pl-4">
                          <div className="flex items-center gap-2.5">
                            <SourceIcon source={row.source} size={30} />
                            <div className="min-w-0">
                              <p className="truncate font-semibold leading-tight">{row.title}</p>
                              <p className="truncate text-xs text-muted-foreground">{row.path}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 pr-4"><SourcePill source={row.source} /></td>
                        <td className="py-3 pr-4">
                          <span className="tnum whitespace-nowrap text-[13px] text-muted-foreground">{fmtDateTime(row.lastSynced)}</span>
                        </td>
                        <td className="py-3 pr-4 text-right">
                          <p className="tnum font-semibold">{formatNumber(row.views)}</p>
                          <p className="tnum text-xs text-muted-foreground">{row.citedBy} {lang === "tr" ? "alıntı" : "cites"}</p>
                        </td>
                        <td className="py-3 pr-4 text-right">
                          <span className={cn("inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-semibold capitalize", st.tone)}>
                            {row.status === "syncing" && <span className="h-1.5 w-1.5 rounded-full bg-current pulse-dot" />}
                            {lang === "tr" ? st.tr : st.en}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Usage over time + sources breakdown */}
          <div className="grid gap-6 lg:grid-cols-[1.5fr_1fr]">
            <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-display text-[15px] font-semibold tracking-tight">{t(usageMeta.title)}</h3>
                  <p className="text-xs text-muted-foreground">{t(usageMeta.subtitle)}</p>
                </div>
                <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success">
                  <ArrowUpRight className="h-3 w-3" />
                  {usageMeta.delta}
                </span>
              </div>
              <p className="mt-3 tnum text-2xl font-bold leading-none">{formatNumber(usage[usage.length - 1].value)}</p>
              <div className="mt-4">
                <AreaChart data={usage.map((v) => v.value)} labels={usage.map((v) => v.label)} height={150} />
              </div>
            </div>

            <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
              <h3 className="font-display text-[15px] font-semibold tracking-tight">
                {lang === "tr" ? "Cevap kaynakları" : "Answer sources"}
              </h3>
              <p className="text-xs text-muted-foreground">{lang === "tr" ? "Yanıtların kaynaklara dağılımı" : "Share of answers by source"}</p>
              <div className="mt-4 space-y-3.5">
                {sourceShare.map((s) => (
                  <div key={s.label}>
                    <div className="mb-1.5 flex items-center justify-between text-sm">
                      <span className="inline-flex items-center gap-2 font-medium">
                        <SourceIcon source={s.source} size={18} className="rounded-[5px]" />
                        {s.label}
                      </span>
                      <span className="tnum text-muted-foreground">{s.value}%</span>
                    </div>
                    <div className="h-2 overflow-hidden rounded-full bg-muted">
                      <div className="h-full rounded-full" style={{ width: `${s.value}%`, background: s.color }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Asked vs answered + Knowledge gaps */}
          <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
            <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
              <div className="flex items-center justify-between">
                <h3 className="font-display text-[15px] font-semibold tracking-tight">
                  {lang === "tr" ? "Soruldu / yanıtlandı" : "Asked vs. answered"}
                </h3>
                <div className="flex items-center gap-3 text-[11px] text-muted-foreground">
                  <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full" style={{ background: "var(--seg-2)" }} />{lang === "tr" ? "soruldu" : "asked"}</span>
                  <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-primary" />{lang === "tr" ? "yanıtlandı" : "answered"}</span>
                </div>
              </div>
              <div className="mt-4">
                <GroupedBars
                  labels={askedVsAnswered.labels}
                  series={[
                    { name: "asked", color: "var(--seg-2)", data: askedVsAnswered.asked },
                    { name: "answered", color: "var(--color-primary)", data: askedVsAnswered.answered },
                  ]}
                  height={168}
                />
              </div>
            </div>

            {/* Knowledge gaps */}
            <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-display text-[15px] font-semibold tracking-tight">{t(gapsMeta.title)}</h3>
                  <p className="text-xs text-muted-foreground">{t(gapsMeta.subtitle)}</p>
                </div>
              </div>
              <div className="mt-3.5 space-y-2.5">
                {gaps.map((g) => (
                  <div key={g.id} className="group flex items-center gap-3 rounded-xl border border-border p-2.5 transition-colors hover:bg-muted/40">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-warning/15 text-warning-foreground">
                      <Search className="h-4 w-4" />
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[13px] font-medium leading-tight">{g.q}</p>
                      <p className="text-[11px] text-muted-foreground">
                        {g.asks} {lang === "tr" ? "kez soruldu" : "asks"} ·{" "}
                        <span className={g.trend >= 0 ? "text-destructive" : "text-success"}>
                          {g.trend >= 0 ? "+" : ""}{g.trend}%
                        </span>
                      </p>
                    </div>
                    <button className="inline-flex shrink-0 items-center gap-1 rounded-lg bg-primary/10 px-2 py-1 text-[11px] font-semibold text-primary transition-colors hover:bg-primary hover:text-primary-foreground">
                      <Plus className="h-3 w-3" />
                      {lang === "tr" ? "Kart" : "Card"}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Questions feed */}
          <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
            <div className="flex items-center justify-between border-b border-border p-4">
              <h3 className="font-display text-[15px] font-semibold tracking-tight">{t(questionsMeta.title)}</h3>
              <Link href="/questions" className="inline-flex items-center gap-1 text-[13px] font-medium text-primary hover:underline">
                {lang === "tr" ? "Tümünü gör" : "View all"}
                <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            </div>
            <div className="divide-y divide-border/60">
              {questions.slice(0, 6).map((q) => (
                <div key={q.id} className="flex items-center gap-3 px-4 py-3">
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-[11px] font-bold text-white" style={{ backgroundImage: "var(--grad-brand)" }}>
                    {q.asker.split(" ").map((p) => p[0]).join("").slice(0, 2)}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{q.q}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {q.asker} · {t(q.channel)} ·{" "}
                      {q.answeredBy ? (
                        <span className="inline-flex items-center gap-1 text-success">
                          <CheckCircle2 className="h-3 w-3" />
                          {docTitle(q.answeredBy)}
                        </span>
                      ) : (
                        <span className="text-warning-foreground">{lang === "tr" ? "yanıtsız" : "unanswered"}</span>
                      )}
                    </p>
                  </div>
                  <span className="hidden shrink-0 text-xs text-muted-foreground sm:inline">{formatRelative(q.at)}</span>
                  <div className="flex shrink-0 items-center gap-1">
                    <button
                      onClick={() => setVote(q.id, "up")}
                      aria-label="thumbs up"
                      className={cn("grid h-7 w-7 place-items-center rounded-md transition-colors hover:bg-muted", votes[q.id] === "up" ? "text-success" : "text-muted-foreground")}
                    >
                      <ThumbsUp className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => setVote(q.id, "down")}
                      aria-label="thumbs down"
                      className={cn("grid h-7 w-7 place-items-center rounded-md transition-colors hover:bg-muted", votes[q.id] === "down" ? "text-destructive" : "text-muted-foreground")}
                    >
                      <ThumbsDown className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Verification panel */}
          <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
            <div className="flex items-center justify-between border-b border-border p-4">
              <div className="flex items-center gap-2">
                <ShieldCheck className="h-4 w-4 text-primary" />
                <div>
                  <h3 className="font-display text-[15px] font-semibold tracking-tight">{t(verificationsMeta.title)}</h3>
                  <p className="text-xs text-muted-foreground">{t(verificationsMeta.subtitle)}</p>
                </div>
              </div>
              <span className="rounded-full bg-warning/15 px-2 py-0.5 text-[11px] font-semibold text-warning-foreground">
                {verifications.length} {lang === "tr" ? "bekliyor" : "pending"}
              </span>
            </div>
            <div className="divide-y divide-border/60">
              {verifications.map((v) => (
                <div key={v.id} className="flex items-center gap-3 px-4 py-3">
                  <SourceIcon source={v.source} size={28} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{v.title}</p>
                    <p className="truncate text-xs text-muted-foreground">
                      {t(v.reason)} · {lang === "tr" ? "uzman" : "expert"}: {v.expert}
                    </p>
                  </div>
                  <button className="shrink-0 rounded-lg border border-border bg-card px-2.5 py-1 text-[12px] font-medium transition-colors hover:bg-muted">
                    {lang === "tr" ? "İncele" : "Review"}
                  </button>
                  <button className="hidden shrink-0 rounded-lg bg-primary px-2.5 py-1 text-[12px] font-semibold text-primary-foreground transition-opacity hover:opacity-90 sm:inline">
                    {lang === "tr" ? "Doğrula" : "Verify"}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Right detail drawer ──────────────────────────────────── */}
        {drawerOpen && activeDoc && (
          <DocDrawer doc={activeDoc} onClose={() => setDrawerOpen(false)} />
        )}
      </div>
    </div>
  );
}

/* ── Document detail drawer ──────────────────────────────────────────────── */
function DocDrawer({ doc, onClose }: { doc: DocRow; onClose: () => void }) {
  const { t, lang } = useLang();
  const st = STATUS_LABEL[doc.status];
  const citedIn = docCitedIn[doc.id] ?? [];
  const freshTone = doc.freshness >= 70 ? "var(--color-success)" : doc.freshness >= 45 ? "var(--color-warning)" : "var(--color-destructive)";
  const sparkline = [doc.views * 0.6, doc.views * 0.72, doc.views * 0.68, doc.views * 0.85, doc.views * 0.92, doc.views].map((v) => Math.round(v / 30));

  return (
    <aside className="animate-float-up xl:sticky xl:top-2 xl:self-start">
      <div className="space-y-5 rounded-2xl border border-border bg-card p-5 shadow-soft">
        <div className="flex items-center justify-between">
          <h2 className="font-display text-[15px] font-semibold tracking-tight">
            {lang === "tr" ? "Belge detayı" : "Document detail"}
          </h2>
          <button
            onClick={onClose}
            aria-label={lang === "tr" ? "Kapat" : "Close"}
            className="grid h-7 w-7 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Doc header */}
        <div className="flex items-start gap-3 rounded-xl border border-border bg-muted/40 p-3">
          <SourceIcon source={doc.source} size={38} />
          <div className="min-w-0">
            <p className="font-semibold leading-tight">{doc.title}</p>
            <p className="text-xs text-muted-foreground">{doc.path}</p>
            <span className={cn("mt-1.5 inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-semibold capitalize", st.tone)}>
              {lang === "tr" ? st.tr : st.en}
            </span>
          </div>
        </div>

        {/* Preview snippet */}
        <div>
          <p className="label-mono mb-1.5 text-muted-foreground">{lang === "tr" ? "Önizleme" : "Preview"}</p>
          <p className="rounded-xl border border-border bg-card p-3 text-[13px] leading-relaxed text-foreground/80">
            {t(doc.snippet)}
          </p>
        </div>

        {/* Stats: views sparkline + freshness gauge */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl border border-border p-3">
            <p className="flex items-center gap-1 text-[11px] font-medium text-muted-foreground">
              <Eye className="h-3 w-3" /> {lang === "tr" ? "Görüntülenme" : "Views"}
            </p>
            <p className="mt-1 tnum text-lg font-bold leading-none">{formatCompact(doc.views)}</p>
            <MiniLineChart data={sparkline} height={36} className="mt-1.5" />
          </div>
          <div className="grid place-items-center rounded-xl border border-border p-3">
            <RadialGauge value={doc.freshness} size={80} color={freshTone} />
            <p className="mt-1 text-[11px] text-muted-foreground">{lang === "tr" ? "Tazelik" : "Freshness"}</p>
          </div>
        </div>

        {/* Owner + last synced */}
        <div className="grid grid-cols-2 gap-3 text-[13px]">
          <div>
            <p className="text-[11px] text-muted-foreground">{lang === "tr" ? "Sahip" : "Owner"}</p>
            <p className="font-medium">{doc.owner}</p>
          </div>
          <div>
            <p className="flex items-center gap-1 text-[11px] text-muted-foreground"><Clock className="h-3 w-3" /> {lang === "tr" ? "Son eşitlenme" : "Last synced"}</p>
            <p className="tnum font-medium">{fmtDateTime(doc.lastSynced)}</p>
          </div>
        </div>

        {/* Where it's cited */}
        <div>
          <p className="label-mono mb-2 flex items-center gap-1.5 text-muted-foreground">
            <Quote className="h-3 w-3" /> {lang === "tr" ? "Nerede alıntılandı" : "Where it's cited"}
          </p>
          {citedIn.length > 0 ? (
            <div className="space-y-2">
              {citedIn.map((c) => (
                <div key={c.q} className="flex items-center gap-2 rounded-lg border border-border p-2.5">
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[13px] font-medium leading-tight">{c.q}</p>
                    <p className="text-[11px] text-muted-foreground">{formatRelative(c.at)}</p>
                  </div>
                  <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-1.5 py-0.5 text-[10px] font-semibold text-success">
                    <ThumbsUp className="h-2.5 w-2.5" /> {c.votes}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="rounded-lg border border-dashed border-border p-3 text-center text-[12px] text-muted-foreground">
              {lang === "tr" ? "Son 30 günde alıntılanmadı." : "Not cited in the last 30 days."}
            </p>
          )}
        </div>

        <button className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-primary py-2.5 text-[13px] font-semibold text-primary-foreground transition-opacity hover:opacity-90">
          <ShieldCheck className="h-4 w-4" />
          {lang === "tr" ? "Doğrulanmış işaretle" : "Mark verified"}
        </button>
      </div>

      {/* Activity feed */}
      <div className="mt-5 rounded-2xl border border-border bg-card p-5 shadow-soft">
        <h3 className="font-display text-[15px] font-semibold tracking-tight">
          {lang === "tr" ? "Son hareketler" : "Recent activity"}
        </h3>
        <div className="mt-3.5 space-y-3.5">
          {activity.map((a) => (
            <div key={a.id} className="flex items-start gap-2.5">
              <span
                className={cn(
                  "mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full",
                  a.tone === "success" ? "bg-success" : a.tone === "warning" ? "bg-warning" : a.tone === "info" ? "bg-info" : "bg-muted-foreground",
                )}
              />
              <div className="min-w-0 text-[13px]">
                <p className="leading-snug">
                  <span className="font-semibold">{a.who}</span>{" "}
                  <span className="text-muted-foreground">{t(a.action)}</span>{" "}
                  <span className="font-medium">{a.target}</span>
                </p>
                <p className="text-[11px] text-muted-foreground">{formatRelative(a.at)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
