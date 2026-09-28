"use client";

import { useEffect, useRef, useState } from "react";
import { Mail, Clock, GitBranch, Plus, Play, Check, RotateCcw } from "lucide-react";
import { useLang } from "@/components/i18n/language-provider";
import { cn } from "@/lib/utils";
import { launchDemo } from "@/lib/demo/data";
import type { L, Lang } from "@/lib/i18n/config";
import type { StepKind } from "@/lib/demo/data";

/* ─────────────────────────────────────────────────────────────────────────────
   FlowDemo — the interactive landing demo. The visitor assembles a 3-step email
   sequence (toggle steps on/off, reorder is implied), hits "Launch", then watches
   sent / open / reply / positive counters tick up to the demo totals. All client-
   side via useState; no network, no keys. Restrained motion only.
   ───────────────────────────────────────────────────────────────────────────── */

const STEP_ICON: Record<StepKind, typeof Mail> = {
  email: Mail,
  wait: Clock,
  condition: GitBranch,
};

type Phase = "build" | "sending" | "done";

/* A small easing tween hook that animates a number from 0 → target. */
function useCountUp(target: number, run: boolean, durationMs = 1400) {
  const [value, setValue] = useState(0);
  const raf = useRef<number | null>(null);
  useEffect(() => {
    if (!run) {
      setValue(0);
      return;
    }
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / durationMs);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - p, 3);
      setValue(Math.round(target * eased));
      if (p < 1) raf.current = requestAnimationFrame(tick);
    };
    raf.current = requestAnimationFrame(tick);
    return () => {
      if (raf.current) cancelAnimationFrame(raf.current);
    };
  }, [target, run, durationMs]);
  return value;
}

export function FlowDemo() {
  const { lang } = useLang();
  const tt = (v: L | string) => (typeof v === "string" ? v : v[lang as Lang]);

  const [phase, setPhase] = useState<Phase>("build");
  // each step can be toggled on/off while building
  const [enabled, setEnabled] = useState<boolean[]>(launchDemo.steps.map(() => true));

  const activeSteps = enabled.filter(Boolean).length;
  const running = phase === "sending" || phase === "done";

  // counters scale with how many steps are enabled (so toggling matters)
  const factor = activeSteps / launchDemo.steps.length || 0.34;
  const sent = useCountUp(Math.round(launchDemo.result.sent * factor), running, 1200);
  const opens = useCountUp(Math.round(launchDemo.result.opens * factor), running, 1500);
  const replies = useCountUp(Math.round(launchDemo.result.replies * factor), running, 1800);
  const positive = useCountUp(Math.round(launchDemo.result.positive * factor), running, 2100);

  useEffect(() => {
    if (phase !== "sending") return;
    const id = setTimeout(() => setPhase("done"), 2200);
    return () => clearTimeout(id);
  }, [phase]);

  const launch = () => {
    if (activeSteps === 0) return;
    setPhase("sending");
  };
  const reset = () => {
    setPhase("build");
    setEnabled(launchDemo.steps.map(() => true));
  };

  const counters: { key: string; label: L; value: number; tone: string }[] = [
    { key: "sent", label: { tr: "Gönderildi", en: "Sent" }, value: sent, tone: "var(--seg-1)" },
    { key: "open", label: { tr: "Açıldı", en: "Opens" }, value: opens, tone: "var(--seg-2)" },
    { key: "reply", label: { tr: "Cevap", en: "Replies" }, value: replies, tone: "var(--seg-3)" },
    { key: "pos", label: { tr: "Olumlu", en: "Positive" }, value: positive, tone: "var(--seg-4)" },
  ];

  return (
    <div className="relative w-full rounded-2xl border border-border bg-card p-5 shadow-pop">
      {/* sweep line while sending */}
      {phase === "sending" && (
        <div className="pointer-events-none absolute inset-x-0 top-0 h-0.5 overflow-hidden rounded-t-2xl">
          <span className="block h-full w-1/4 bg-primary sweep-flow" />
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <p className="label-mono text-primary">{lang === "tr" ? "Dizi kurucu" : "Sequence builder"}</p>
          <h3 className="mt-1 font-display text-[15px] font-semibold tracking-tight">
            {lang === "tr" ? "3 adımlı kampanya" : "3-step campaign"}
          </h3>
        </div>
        <span
          className={cn(
            "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-semibold",
            phase === "done"
              ? "bg-success/12 text-success"
              : phase === "sending"
                ? "bg-info/10 text-info"
                : "bg-secondary text-secondary-foreground",
          )}
        >
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              phase === "done" ? "bg-success" : phase === "sending" ? "bg-info pulse-dot" : "bg-muted-foreground",
            )}
          />
          {phase === "done"
            ? lang === "tr"
              ? "Tamamlandı"
              : "Live"
            : phase === "sending"
              ? lang === "tr"
                ? "Gönderiliyor…"
                : "Sending…"
              : lang === "tr"
                ? "Taslak"
                : "Draft"}
        </span>
      </div>

      {/* The step list */}
      <ol className="mt-5 space-y-0">
        {launchDemo.steps.map((step, i) => {
          const I = STEP_ICON[step.kind];
          const isLast = i === launchDemo.steps.length - 1;
          const on = enabled[i];
          return (
            <li key={i} className="relative flex gap-3.5 pb-3 last:pb-0">
              {!isLast && <span className="absolute left-[15px] top-9 h-[calc(100%-1.5rem)] w-px bg-border" aria-hidden />}
              <span
                className={cn(
                  "z-10 mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full border transition-colors",
                  !on
                    ? "border-border bg-muted text-muted-foreground/50"
                    : step.kind === "email"
                      ? "border-primary/30 bg-primary/10 text-primary"
                      : "border-border bg-muted text-muted-foreground",
                )}
              >
                <I className="h-4 w-4" />
              </span>
              <button
                type="button"
                disabled={running}
                onClick={() => setEnabled((p) => p.map((v, idx) => (idx === i ? !v : v)))}
                className={cn(
                  "min-w-0 flex-1 rounded-xl border px-3.5 py-2.5 text-left transition-all",
                  on ? "border-border bg-card" : "border-dashed border-border bg-muted/40 opacity-60",
                  !running && "hover:border-primary/40",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <p className="text-[13px] font-semibold leading-tight">{tt(step.label)}</p>
                  <span
                    className={cn(
                      "grid h-4 w-4 shrink-0 place-items-center rounded-full border text-[9px]",
                      on ? "border-primary bg-primary text-primary-foreground" : "border-border text-transparent",
                    )}
                  >
                    <Check className="h-2.5 w-2.5" strokeWidth={3} />
                  </span>
                </div>
                <p className="mt-0.5 truncate text-xs text-muted-foreground">{tt(step.sub)}</p>
              </button>
            </li>
          );
        })}
      </ol>

      {phase === "build" && (
        <div className="mt-1 flex items-center gap-2 pl-[46px] text-[11px] text-muted-foreground">
          <Plus className="h-3 w-3" />
          {lang === "tr" ? "Adımları aç/kapat — sonra başlat" : "Toggle steps — then launch"}
        </div>
      )}

      {/* Counters */}
      <div className="mt-5 grid grid-cols-4 gap-2.5 border-t border-border pt-4">
        {counters.map((c) => (
          <div key={c.key} className="rounded-xl border border-border bg-muted/30 p-2.5 text-center">
            <p
              className="tnum text-lg font-bold leading-none transition-opacity"
              style={{ color: running ? c.tone : "var(--color-muted-foreground)" }}
            >
              {c.value.toLocaleString("en-US")}
            </p>
            <p className="mt-1 text-[10px] text-muted-foreground">{tt(c.label)}</p>
          </div>
        ))}
      </div>

      {/* Action row */}
      <div className="mt-4">
        {phase === "done" ? (
          <button
            onClick={reset}
            className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl border border-border bg-card text-[14px] font-semibold text-foreground transition-colors hover:bg-muted"
          >
            <RotateCcw className="h-4 w-4 text-muted-foreground" />
            {lang === "tr" ? "Yeniden kur" : "Build another"}
          </button>
        ) : (
          <button
            onClick={launch}
            disabled={phase === "sending" || activeSteps === 0}
            className="inline-flex h-11 w-full items-center justify-center gap-2 rounded-xl bg-primary text-[14px] font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            <Play className="h-4 w-4 fill-current" />
            {phase === "sending"
              ? lang === "tr"
                ? "Gönderiliyor…"
                : "Sending…"
              : lang === "tr"
                ? "Kampanyayı başlat"
                : "Launch campaign"}
          </button>
        )}
      </div>
    </div>
  );
}
