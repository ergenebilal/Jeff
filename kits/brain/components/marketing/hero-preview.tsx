"use client";

import { Sparkles, ArrowUp, FileText } from "lucide-react";
import { SourceIcon } from "@/components/app/source-icon";
import { useLang } from "@/components/i18n/language-provider";
import { askExamples } from "@/lib/demo/data";

/* ── Hero product-preview: the ask bar with a cited answer rendered ────────── */
export function HeroPreview() {
  const { lang } = useLang();
  const ex = askExamples[0];

  return (
    <div className="w-full rounded-2xl border border-border bg-card p-3.5 shadow-pop sm:p-4">
      {/* ask input */}
      <div className="flex items-center gap-2.5 rounded-xl border border-border bg-muted/40 p-2.5">
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
          <Sparkles className="h-4 w-4" />
        </span>
        <span className="min-w-0 flex-1 truncate text-[13.5px] text-foreground">{ex.q[lang]}</span>
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-primary text-primary-foreground">
          <ArrowUp className="h-4 w-4" />
        </span>
      </div>

      {/* answer */}
      <div className="mt-3">
        <p className="label-mono mb-1.5 flex items-center gap-2 text-muted-foreground">
          {lang === "tr" ? "Brain yanıtı" : "Brain answer"}
          <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-1.5 py-0.5 text-[10px] font-semibold text-success">
            {ex.confidence}%
          </span>
        </p>
        <p className="text-[13px] leading-relaxed text-foreground/90">{ex.a[lang]}</p>
      </div>

      {/* citations */}
      <div className="mt-3 border-t border-border pt-3">
        <p className="label-mono mb-1.5 text-muted-foreground">{lang === "tr" ? "Kaynaklar" : "Sources"}</p>
        <div className="flex flex-wrap gap-1.5">
          {ex.citations.map((c, i) => (
            <span key={c.title} className="inline-flex items-center gap-1.5 rounded-lg border border-border bg-muted/40 py-1 pl-1.5 pr-2 text-[11.5px]">
              <span className="grid h-4 w-4 shrink-0 place-items-center rounded bg-card text-[9px] font-bold text-muted-foreground ring-1 ring-border">{i + 1}</span>
              <SourceIcon source={c.source} size={14} className="rounded-[4px]" />
              <span className="font-medium">{c.title}</span>
              <FileText className="h-2.5 w-2.5 text-muted-foreground" />
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
