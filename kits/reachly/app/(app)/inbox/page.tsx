"use client";

import { useState } from "react";
import {
  Search,
  Filter,
  Reply as ReplyIcon,
  Forward,
  Check,
  Mail,
  Calendar,
  Archive,
} from "lucide-react";
import { useLang } from "@/components/i18n/language-provider";
import { cn, formatRelative } from "@/lib/utils";
import { replies, SENTIMENT_META, type Sentiment } from "@/lib/demo/data";

/* The unified reply inbox: a left list of replies + a right reading pane. All
   from demo data; selecting a reply updates the pane via useState. */

const FILTERS: { key: Sentiment | "all"; tr: string; en: string }[] = [
  { key: "all", tr: "Tümü", en: "All" },
  { key: "interested", tr: "İlgileniyor", en: "Interested" },
  { key: "meeting", tr: "Toplantı", en: "Meetings" },
  { key: "notnow", tr: "Şimdi değil", en: "Not now" },
];

export default function InboxPage() {
  const { t, lang, ui } = useLang();
  const [filter, setFilter] = useState<Sentiment | "all">("all");
  const [activeId, setActiveId] = useState<string>(replies[0]?.id ?? "");

  const list = replies.filter((r) => filter === "all" || r.sentiment === filter);
  const active = replies.find((r) => r.id === activeId) ?? list[0] ?? replies[0];
  const unread = replies.filter((r) => r.unread).length;

  return (
    <div className="mx-auto max-w-[1400px] animate-fade-in space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight">
            {lang === "tr" ? "Gelen kutusu" : "Inbox"}
          </h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {lang === "tr"
              ? "Tüm posta kutularından gelen cevaplar tek akışta."
              : "Replies from every mailbox in one stream."}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          {unread > 0 && (
            <span className="rounded-full bg-primary/10 px-2.5 py-1 text-[12px] font-semibold text-primary">
              {unread} {lang === "tr" ? "okunmamış" : "unread"}
            </span>
          )}
          <button className="inline-flex h-9 items-center gap-2 rounded-lg border border-border bg-card px-3.5 text-[13px] font-medium text-foreground shadow-pill transition-colors hover:bg-muted">
            <Archive className="h-4 w-4 text-muted-foreground" />
            {lang === "tr" ? "Arşiv" : "Archive"}
          </button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,380px)_1fr]">
        {/* ── Reply list ─────────────────────────────────────────── */}
        <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
          <div className="flex items-center gap-2 border-b border-border p-3">
            <div className="flex h-9 flex-1 items-center gap-2 rounded-lg border border-border bg-card px-3 text-sm">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input
                placeholder={ui.search}
                className="w-full bg-transparent placeholder:text-muted-foreground/70 focus:outline-none"
              />
            </div>
            <button className="grid h-9 w-9 place-items-center rounded-lg border border-border text-muted-foreground transition-colors hover:bg-muted">
              <Filter className="h-4 w-4" />
            </button>
          </div>

          <div className="flex flex-wrap gap-1.5 border-b border-border px-3 py-2">
            {FILTERS.map((f) => (
              <button
                key={f.key}
                onClick={() => setFilter(f.key)}
                className={cn(
                  "rounded-lg px-2.5 py-1 text-[12.5px] font-medium transition-colors",
                  filter === f.key ? "nav-pill-active text-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )}
              >
                {lang === "tr" ? f.tr : f.en}
              </button>
            ))}
          </div>

          <div className="max-h-[560px] divide-y divide-border/60 overflow-y-auto">
            {list.map((r) => {
              const sm = SENTIMENT_META[r.sentiment];
              const isActive = r.id === active?.id;
              return (
                <button
                  key={r.id}
                  onClick={() => setActiveId(r.id)}
                  className={cn(
                    "flex w-full items-start gap-2.5 px-4 py-3 text-left transition-colors",
                    isActive ? "bg-primary/[0.04]" : "hover:bg-muted/50",
                  )}
                >
                  <span className="relative grid h-9 w-9 shrink-0 place-items-center rounded-full bg-secondary text-[11px] font-bold text-secondary-foreground">
                    {r.initials}
                    {r.unread && <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-primary ring-2 ring-card" />}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className={cn("truncate text-[13px] leading-tight", r.unread ? "font-bold" : "font-semibold")}>{r.name}</p>
                      <span className="shrink-0 text-[10.5px] text-muted-foreground">{formatRelative(r.at)}</span>
                    </div>
                    <p className="truncate text-[12px] text-foreground/70">{r.subject}</p>
                    <p className="mt-0.5 truncate text-[11.5px] text-muted-foreground">{t(r.preview)}</p>
                    <span className={cn("mt-1 inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-semibold", sm.cls)}>
                      <span className={cn("h-1.5 w-1.5 rounded-full", sm.dot)} />
                      {lang === "tr" ? sm.tr : sm.en}
                    </span>
                  </div>
                </button>
              );
            })}
            {list.length === 0 && (
              <p className="px-4 py-10 text-center text-sm text-muted-foreground">
                {lang === "tr" ? "Bu filtrede cevap yok." : "No replies in this filter."}
              </p>
            )}
          </div>
        </div>

        {/* ── Reading pane ───────────────────────────────────────── */}
        {active && (
          <div className="flex flex-col rounded-2xl border border-border bg-card shadow-soft">
            <div className="flex flex-wrap items-center gap-3 border-b border-border p-5">
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full text-sm font-bold text-white" style={{ backgroundImage: "var(--grad-brand)" }}>
                {active.initials}
              </span>
              <div className="min-w-0">
                <p className="font-semibold leading-tight">{active.name}</p>
                <p className="truncate text-xs text-muted-foreground">{active.email} · {active.company}</p>
              </div>
              <span className={cn("ml-auto inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-semibold", SENTIMENT_META[active.sentiment].cls)}>
                <span className={cn("h-1.5 w-1.5 rounded-full", SENTIMENT_META[active.sentiment].dot)} />
                {lang === "tr" ? SENTIMENT_META[active.sentiment].tr : SENTIMENT_META[active.sentiment].en}
              </span>
            </div>

            <div className="flex-1 space-y-4 p-5">
              <div>
                <p className="text-[13px] font-semibold">{active.subject}</p>
                <p className="mt-0.5 text-[11px] text-muted-foreground">
                  {active.campaign} · {formatRelative(active.at)}
                </p>
              </div>
              <div className="rounded-xl border border-border bg-muted/30 p-4 text-[14px] leading-relaxed text-foreground/90">
                {t(active.preview)}
              </div>
              <div className="flex items-center gap-2 text-[12px] text-muted-foreground">
                <Mail className="h-3.5 w-3.5" />
                {lang === "tr" ? "Reachly bu cevabı duyguya göre etiketledi." : "Reachly auto-tagged this reply by sentiment."}
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-2 border-t border-border p-4">
              <button className="inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-[13px] font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90">
                <ReplyIcon className="h-4 w-4" />
                {ui.reply}
              </button>
              <button className="inline-flex h-10 items-center gap-2 rounded-lg border border-border bg-card px-4 text-[13px] font-medium text-foreground transition-colors hover:bg-muted">
                <Forward className="h-4 w-4 text-muted-foreground" />
                {ui.forward}
              </button>
              <button className="inline-flex h-10 items-center gap-2 rounded-lg border border-border bg-card px-4 text-[13px] font-medium text-foreground transition-colors hover:bg-muted">
                <Calendar className="h-4 w-4 text-muted-foreground" />
                {lang === "tr" ? "Toplantı ayarla" : "Book meeting"}
              </button>
              <button className="ml-auto inline-flex h-10 items-center gap-2 rounded-lg border border-border bg-card px-4 text-[13px] font-medium text-foreground transition-colors hover:bg-muted">
                <Check className="h-4 w-4 text-success" strokeWidth={3} />
                {ui.markDone}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
