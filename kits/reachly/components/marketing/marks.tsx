"use client";

import { Mail, Clock } from "lucide-react";
import { useLang } from "@/components/i18n/language-provider";
import { replies, SENTIMENT_META } from "@/lib/demo/data";

/* ── Inline-SVG fake-company wordmarks for the trusted-by row ───────────────── */
export function CompanyMark({ name }: { name: string }) {
  const glyphs: Record<string, React.ReactNode> = {
    Northwind: <path d="M3 17 L9 4 L12 11 L15 4 L21 17" />,
    Parable: <circle cx="12" cy="11" r="7" />,
    Formwork: <path d="M4 5 h16 v4 h-6 v9 h-4 v-9 h-6 z" />,
    Cedarworks: <path d="M12 3 L20 18 H4 Z M12 9 L16 17 H8 Z" />,
    Lumen: <path d="M6 4 v14 h10" />,
    Harvest: <path d="M12 4 c5 4 5 10 0 14 c-5 -4 -5 -10 0 -14 z" />,
    Brightline: <path d="M4 12 h16 M12 5 v14" />,
    Meridian: <path d="M4 18 L9 6 L12 14 L15 6 L20 18" />,
    Cadence: <path d="M4 14 q4 -10 8 0 q4 10 8 0" />,
    Orbit: <><circle cx="12" cy="12" r="3" /><ellipse cx="12" cy="12" rx="9" ry="4" /></>,
  };
  return (
    <span className="inline-flex items-center gap-2 text-muted-foreground/70">
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        {glyphs[name]}
      </svg>
      <span className="text-[15px] font-semibold tracking-tight">{name}</span>
    </span>
  );
}

/* ── Hero product-preview card: a mini campaign + reply inbox panel ─────────── */
export function ProductPreview() {
  const { lang, t } = useLang();
  const campaignRows = [
    { name: "Q3 SaaS Founders", sent: "6,120", open: "64%", reply: "9.2%", progress: 72 },
    { name: "Agency Owners", sent: "2,480", open: "71%", reply: "11.4%", progress: 58 },
    { name: "Series A CTOs", sent: "1,880", open: "59%", reply: "7.8%", progress: 81 },
  ];

  return (
    <div className="w-full rounded-2xl border border-border bg-card p-4 shadow-pop sm:p-5">
      {/* mini stat row */}
      <div className="grid grid-cols-3 gap-2.5">
        {[
          { label: lang === "tr" ? "Gönderilen" : "Sent", value: "48.2k" },
          { label: lang === "tr" ? "Açılma" : "Open", value: "61.8%" },
          { label: lang === "tr" ? "Cevap" : "Reply", value: "8.4%" },
        ].map((s) => (
          <div key={s.label} className="rounded-xl border border-border bg-muted/40 p-2.5">
            <p className="text-[10px] font-medium text-muted-foreground">{s.label}</p>
            <p className="mt-1 tnum text-base font-bold leading-none">{s.value}</p>
          </div>
        ))}
      </div>

      {/* mini campaigns table */}
      <div className="mt-3.5 overflow-hidden rounded-xl border border-border">
        <div className="grid grid-cols-[1.6fr_0.8fr_0.8fr] gap-2 border-b border-border bg-muted/40 px-3 py-2 label-mono text-muted-foreground">
          <span>{lang === "tr" ? "Kampanya" : "Campaign"}</span>
          <span className="text-right">{lang === "tr" ? "Açılma" : "Open"}</span>
          <span className="text-right">{lang === "tr" ? "Cevap" : "Reply"}</span>
        </div>
        {campaignRows.map((r, i) => (
          <div
            key={r.name}
            className={`px-3 py-2 ${i === 0 ? "bg-primary/[0.04]" : ""} ${i < campaignRows.length - 1 ? "border-b border-border/60" : ""}`}
          >
            <div className="grid grid-cols-[1.6fr_0.8fr_0.8fr] items-center gap-2">
              <p className="truncate text-[12px] font-semibold">{r.name}</p>
              <p className="tnum text-right text-[11px] text-muted-foreground">{r.open}</p>
              <p className="tnum text-right text-[11px] font-semibold text-success">{r.reply}</p>
            </div>
            <div className="mt-1.5 h-1 w-full overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full" style={{ width: `${r.progress}%`, background: "var(--grad-brand)" }} />
            </div>
          </div>
        ))}
      </div>

      {/* mini reply inbox */}
      <div className="mt-3.5 rounded-xl border border-border p-3">
        <div className="flex items-center justify-between">
          <p className="label-mono text-muted-foreground">{lang === "tr" ? "Gelen kutusu" : "Inbox"}</p>
          <span className="rounded-full bg-primary/10 px-1.5 py-0.5 text-[9px] font-semibold text-primary">3 {lang === "tr" ? "yeni" : "new"}</span>
        </div>
        <div className="mt-2 space-y-2">
          {replies.slice(0, 2).map((rp) => {
            const sm = SENTIMENT_META[rp.sentiment];
            return (
              <div key={rp.id} className="flex items-center gap-2">
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-secondary text-[9px] font-bold text-secondary-foreground">{rp.initials}</span>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[11.5px] font-semibold leading-tight">{rp.name}</p>
                  <p className="truncate text-[10px] text-muted-foreground">{t(rp.preview)}</p>
                </div>
                <span className={`shrink-0 rounded-full px-1.5 py-0.5 text-[9px] font-semibold ${sm.cls}`}>{lang === "tr" ? sm.tr : sm.en}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ── A small "send" pulse glyph used by the hero floating motif ────────────── */
export function StepGlyph({ kind }: { kind: "email" | "wait" }) {
  return (
    <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary/10 text-primary">
      {kind === "email" ? <Mail className="h-4 w-4" /> : <Clock className="h-4 w-4" />}
    </span>
  );
}

/* ── Integration glyphs for the strip ──────────────────────────────────────── */
export function IntegrationGlyph({ glyph }: { glyph: "ses" | "smtp" | "db" | "verify" }) {
  const color =
    glyph === "ses" ? "var(--seg-2)" : glyph === "smtp" ? "var(--color-primary)" : glyph === "verify" ? "var(--color-success)" : "var(--seg-4)";
  return (
    <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl" style={{ background: color }}>
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="#fff" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
        {glyph === "ses" && <path d="M3 6 h18 v12 h-18 z M3 7 l9 6 l9 -6" />}
        {glyph === "smtp" && <path d="M3 6 h18 v12 h-18 z M3 7 l9 6 l9 -6 M7 18 l3 -3 M17 18 l-3 -3" />}
        {glyph === "verify" && <path d="M4 12 l4 4 l8 -9 M14 5 h6 v6" />}
        {glyph === "db" && <path d="M4 6 c0 -1.7 3.6 -3 8 -3 s8 1.3 8 3 v12 c0 1.7 -3.6 3 -8 3 s-8 -1.3 -8 -3 z M4 6 c0 1.7 3.6 3 8 3 s8 -1.3 8 -3 M4 12 c0 1.7 3.6 3 8 3 s8 -1.3 8 -3" />}
      </svg>
    </span>
  );
}
