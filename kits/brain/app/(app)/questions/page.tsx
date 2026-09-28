"use client";

import { useState } from "react";
import { Search, ThumbsUp, ThumbsDown, CheckCircle2, Plus } from "lucide-react";
import { useLang } from "@/components/i18n/language-provider";
import { cn, formatRelative } from "@/lib/utils";
import { questions, documents, gaps } from "@/lib/demo/data";

type Tab = "all" | "answered" | "unanswered";

export default function QuestionsPage() {
  const { t, lang } = useLang();
  const [query, setQuery] = useState("");
  const [tab, setTab] = useState<Tab>("all");
  const [votes, setVotes] = useState<Record<string, "up" | "down" | null>>(
    Object.fromEntries(questions.map((q) => [q.id, q.vote])),
  );

  const docTitle = (id?: string) => documents.find((d) => d.id === id)?.title;

  const rows = questions.filter((q) => {
    if (tab === "answered" && !q.answeredBy) return false;
    if (tab === "unanswered" && q.answeredBy) return false;
    return !query || q.q.toLowerCase().includes(query.toLowerCase()) || q.asker.toLowerCase().includes(query.toLowerCase());
  });

  const answeredCount = questions.filter((q) => q.answeredBy).length;
  const upCount = Object.values(votes).filter((v) => v === "up").length;

  function setVote(id: string, v: "up" | "down") {
    setVotes((prev) => ({ ...prev, [id]: prev[id] === v ? null : v }));
  }

  return (
    <div className="mx-auto max-w-[1100px] animate-fade-in space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold tracking-tight">{lang === "tr" ? "Sorular" : "Questions"}</h1>
        <p className="mt-0.5 text-sm text-muted-foreground">
          {lang === "tr" ? "Ekibinin Brain'e sorduğu her şey — ve hangi belgenin yanıtladığı." : "Everything your team asked Brain — and which doc answered it."}
        </p>
      </div>

      {/* mini stats */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: lang === "tr" ? "Toplam soru" : "Total questions", value: questions.length },
          { label: lang === "tr" ? "Yanıtlandı" : "Answered", value: answeredCount },
          { label: lang === "tr" ? "Olumlu oy" : "Upvotes", value: upCount },
        ].map((s) => (
          <div key={s.label} className="rounded-2xl border border-border bg-card p-4 shadow-soft">
            <p className="tnum text-2xl font-bold leading-none">{s.value}</p>
            <p className="mt-1.5 text-[13px] text-muted-foreground">{s.label}</p>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.6fr_1fr]">
        {/* Questions list */}
        <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
          <div className="flex flex-wrap items-center gap-2.5 border-b border-border p-4">
            <div className="flex items-center gap-1">
              {(["all", "answered", "unanswered"] as const).map((tt) => (
                <button
                  key={tt}
                  onClick={() => setTab(tt)}
                  className={cn(
                    "rounded-full px-2.5 py-1 text-[12px] font-medium transition-colors",
                    tab === tt ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted",
                  )}
                >
                  {tt === "all" ? (lang === "tr" ? "Tümü" : "All") : tt === "answered" ? (lang === "tr" ? "Yanıtlandı" : "Answered") : lang === "tr" ? "Yanıtsız" : "Unanswered"}
                </button>
              ))}
            </div>
            <div className="ml-auto flex h-9 items-center gap-2 rounded-lg border border-border bg-card px-3 text-sm">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={lang === "tr" ? "Soru ara…" : "Search questions…"}
                className="w-32 bg-transparent text-foreground placeholder:text-muted-foreground/70 focus:outline-none sm:w-44"
              />
            </div>
          </div>
          <div className="divide-y divide-border/60">
            {rows.map((q) => (
              <div key={q.id} className="px-4 py-3.5">
                <div className="flex items-start gap-3">
                  <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-[11px] font-bold text-white" style={{ backgroundImage: "var(--grad-brand)" }}>
                    {q.asker.split(" ").map((p) => p[0]).join("").slice(0, 2)}
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium leading-snug">{q.q}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {q.asker} · {t(q.channel)} · {formatRelative(q.at)}
                    </p>
                    {q.answeredBy ? (
                      <span className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-border bg-muted/40 px-2 py-1 text-[12px] text-foreground/80">
                        <CheckCircle2 className="h-3.5 w-3.5 text-success" />
                        {lang === "tr" ? "Yanıtladı:" : "Answered by:"} <span className="font-medium">{docTitle(q.answeredBy)}</span>
                      </span>
                    ) : (
                      <span className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-dashed border-warning/40 bg-warning/10 px-2 py-1 text-[12px] text-warning-foreground">
                        {lang === "tr" ? "Yanıtsız — kart oluştur" : "Unanswered — create a card"}
                      </span>
                    )}
                  </div>
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
              </div>
            ))}
          </div>
        </div>

        {/* Gaps rail */}
        <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
          <h3 className="font-display text-[15px] font-semibold tracking-tight">{lang === "tr" ? "Yanıtsız boşluklar" : "Unanswered gaps"}</h3>
          <p className="text-xs text-muted-foreground">{lang === "tr" ? "Sık sorulan, dokümante edilmemiş." : "Frequently asked, undocumented."}</p>
          <div className="mt-3.5 space-y-2.5">
            {gaps.map((g) => (
              <div key={g.id} className="flex items-center gap-3 rounded-xl border border-border p-2.5 transition-colors hover:bg-muted/40">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] font-medium leading-tight">{g.q}</p>
                  <p className="text-[11px] text-muted-foreground">{g.asks} {lang === "tr" ? "kez soruldu" : "asks"}</p>
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
    </div>
  );
}
