"use client";

import { Avatar } from "@/components/app/avatar";
import { useLang } from "@/components/i18n/language-provider";
import { formatMoney } from "@/lib/utils";
import { stages, repById, type StageId } from "@/lib/demo/data";

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

/* ── Hero product-preview card: a mini pipeline kanban + stat row ──────────── */
export function ProductPreview() {
  const { t, lang } = useLang();

  const previewCols: { stage: StageId; cards: { company: string; value: number; ownerId: string }[] }[] = [
    { stage: "qualified", cards: [{ company: "Parable", value: 22500, ownerId: "r2" }, { company: "Meridian", value: 52000, ownerId: "r2" }] },
    { stage: "proposal", cards: [{ company: "Lumen", value: 64000, ownerId: "r3" }] },
    { stage: "negotiation", cards: [{ company: "Northwind", value: 41000, ownerId: "r1" }] },
  ];

  return (
    <div className="w-full rounded-2xl border border-border bg-card p-4 shadow-pop sm:p-5">
      {/* mini stat row */}
      <div className="grid grid-cols-3 gap-3">
        <Stat label={lang === "tr" ? "Pipeline" : "Pipeline"} value={formatMoney(439500)} />
        <Stat label={lang === "tr" ? "Açık" : "Open"} value="10" />
        <Stat label={lang === "tr" ? "Kazanma" : "Win rate"} value="38%" />
      </div>

      {/* mini kanban */}
      <div className="mt-4 grid grid-cols-3 gap-2.5">
        {previewCols.map((col) => {
          const st = stages.find((s) => s.id === col.stage)!;
          return (
            <div key={col.stage} className="rounded-xl border border-border bg-muted/40 p-2">
              <div className="mb-2 flex items-center gap-1.5 px-0.5">
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: st.color }} />
                <span className="truncate text-[10px] font-semibold text-muted-foreground">{t(st.label)}</span>
              </div>
              <div className="space-y-1.5">
                {col.cards.map((c, i) => {
                  const rep = repById[c.ownerId];
                  return (
                    <div key={i} className="rounded-lg border border-border bg-card p-2 shadow-pill">
                      <p className="truncate text-[11px] font-semibold leading-tight">{c.company}</p>
                      <div className="mt-1.5 flex items-center justify-between">
                        <span className="tnum text-[10.5px] font-semibold text-foreground">{formatMoney(c.value)}</span>
                        <Avatar initials={rep.initials} color={rep.color} size={16} />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-muted/40 p-3">
      <p className="text-[11px] font-medium text-muted-foreground">{label}</p>
      <p className="mt-1 tnum text-lg font-bold leading-none">{value}</p>
    </div>
  );
}
