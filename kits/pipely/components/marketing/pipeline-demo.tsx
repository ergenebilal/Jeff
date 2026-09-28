"use client";

import { useMemo, useState } from "react";
import { Check, Trophy, GripVertical, RotateCcw } from "lucide-react";
import { Avatar } from "@/components/app/avatar";
import { useLang } from "@/components/i18n/language-provider";
import { cn, formatMoney } from "@/lib/utils";
import { stages, repById, pipelineDemo, type StageId } from "@/lib/demo/data";

/**
 * Interactive landing demo: a small pipeline you can play with. Drag a deal
 * card to the "Won" column (or click it) and the pipeline value + win rate
 * stats recompute live. Pure useState, no deps.
 */
export function PipelineDemo() {
  const { t, lang } = useLang();
  const [cards, setCards] = useState(pipelineDemo);
  const [dragId, setDragId] = useState<string | null>(null);
  const [overStage, setOverStage] = useState<StageId | null>(null);
  const [justWon, setJustWon] = useState<string | null>(null);

  // Show four columns ending in Won.
  const cols: StageId[] = ["qualified", "proposal", "negotiation", "won"];

  const openValue = useMemo(
    () => cards.filter((c) => c.stage !== "won").reduce((s, c) => s + c.value, 0),
    [cards],
  );
  const wonCount = cards.filter((c) => c.stage === "won").length;
  const winRate = Math.round((wonCount / cards.length) * 100);
  const wonValue = cards.filter((c) => c.stage === "won").reduce((s, c) => s + c.value, 0);

  function move(id: string, to: StageId) {
    setCards((prev) => prev.map((c) => (c.id === id ? { ...c, stage: to } : c)));
    if (to === "won") {
      setJustWon(id);
      setTimeout(() => setJustWon((v) => (v === id ? null : v)), 600);
    }
  }

  function reset() {
    setCards(pipelineDemo);
  }

  const allWon = wonCount === cards.length;

  return (
    <div className="rounded-2xl border border-border bg-card p-5 shadow-pop">
      {/* live stat row */}
      <div className="mb-4 grid grid-cols-3 gap-3">
        <DemoStat label={lang === "tr" ? "Açık pipeline" : "Open pipeline"} value={formatMoney(openValue)} />
        <DemoStat label={lang === "tr" ? "Kazanma oranı" : "Win rate"} value={`${winRate}%`} accent />
        <DemoStat label={lang === "tr" ? "Kazanılan" : "Won"} value={formatMoney(wonValue)} />
      </div>

      <p className="mb-3 text-[12px] text-muted-foreground">
        {lang === "tr"
          ? "İpucu: bir deal'i Kazanıldı'ya sürükle (ya da tıkla) — istatistikler anında güncellenir."
          : "Tip: drag a deal into Won (or tap it) — the stats update instantly."}
      </p>

      {/* board */}
      <div className="grid grid-cols-4 gap-2.5">
        {cols.map((stageId) => {
          const st = stages.find((s) => s.id === stageId)!;
          const colCards = cards.filter((c) => c.stage === stageId);
          const isWon = stageId === "won";
          return (
            <div
              key={stageId}
              onDragOver={(e) => {
                e.preventDefault();
                setOverStage(stageId);
              }}
              onDragLeave={() => setOverStage((s) => (s === stageId ? null : s))}
              onDrop={() => {
                if (dragId) move(dragId, stageId);
                setDragId(null);
                setOverStage(null);
              }}
              className={cn(
                "min-h-[150px] rounded-xl border p-1.5 transition-colors",
                isWon ? "border-success/40 bg-success/[0.05]" : "border-border bg-muted/40",
                overStage === stageId && "border-primary/60 bg-primary/[0.06] ring-1 ring-primary/30",
              )}
            >
              <div className="mb-1.5 flex items-center gap-1.5 px-1.5 pt-1">
                {isWon ? (
                  <Trophy className="h-3 w-3 text-success" />
                ) : (
                  <span className="h-1.5 w-1.5 rounded-full" style={{ background: st.color }} />
                )}
                <span className="truncate text-[10.5px] font-semibold text-muted-foreground">{t(st.label)}</span>
                <span className="ml-auto text-[10px] tnum text-muted-foreground">{colCards.length}</span>
              </div>
              <div className="space-y-1.5">
                {colCards.map((c) => {
                  const rep = repById[c.ownerId];
                  return (
                    <button
                      key={c.id}
                      draggable
                      onDragStart={() => setDragId(c.id)}
                      onDragEnd={() => setDragId(null)}
                      onClick={() => {
                        // tap fallback: advance toward / into Won
                        const order: StageId[] = ["lead", "qualified", "proposal", "negotiation", "won"];
                        const next = order[Math.min(order.indexOf(c.stage) + 1, order.length - 1)];
                        move(c.id, next);
                      }}
                      className={cn(
                        "group block w-full cursor-grab rounded-lg border border-border bg-card p-2 text-left shadow-pill transition-shadow hover:shadow-soft active:cursor-grabbing",
                        justWon === c.id && "won-pop",
                      )}
                    >
                      <div className="flex items-center gap-1">
                        <GripVertical className="h-3 w-3 shrink-0 text-muted-foreground/50" />
                        <p className="truncate text-[11px] font-semibold leading-tight">{c.company}</p>
                      </div>
                      <div className="mt-1.5 flex items-center justify-between pl-1">
                        <span className="tnum text-[10.5px] font-semibold">{formatMoney(c.value)}</span>
                        <Avatar initials={rep.initials} color={rep.color} size={16} />
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      {/* footer: celebration / reset */}
      <div className="mt-3 flex items-center justify-between">
        <span className={cn("inline-flex items-center gap-1.5 text-[12px] font-medium transition-opacity", allWon ? "text-success opacity-100" : "opacity-0")}>
          <Check className="h-3.5 w-3.5" strokeWidth={3} />
          {lang === "tr" ? "Tüm deal'ler kapandı!" : "Every deal closed!"}
        </span>
        <button
          onClick={reset}
          className="inline-flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1 text-[11px] font-medium text-muted-foreground transition-colors hover:text-foreground"
        >
          <RotateCcw className="h-3 w-3" />
          {lang === "tr" ? "Sıfırla" : "Reset"}
        </button>
      </div>
    </div>
  );
}

function DemoStat({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className={cn("rounded-xl border p-3", accent ? "border-primary/30 bg-primary/[0.05]" : "border-border bg-muted/40")}>
      <p className="text-[10.5px] font-medium text-muted-foreground">{label}</p>
      <p className={cn("mt-1 tnum text-lg font-bold leading-none", accent && "text-primary")}>{value}</p>
    </div>
  );
}
