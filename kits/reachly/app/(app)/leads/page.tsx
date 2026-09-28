"use client";

import { useState } from "react";
import { Search, Filter, Upload, Plus, Check, X } from "lucide-react";
import { useLang } from "@/components/i18n/language-provider";
import { cn } from "@/lib/utils";
import { leads, LEAD_META, type LeadStatus } from "@/lib/demo/data";

/* Leads table — searchable + status-filterable list of every contact across
   campaigns. Demo data; filter/search via useState. */

const FILTERS: { key: LeadStatus | "all"; tr: string; en: string }[] = [
  { key: "all", tr: "Tümü", en: "All" },
  { key: "new", tr: "Yeni", en: "New" },
  { key: "contacted", tr: "Ulaşıldı", en: "Contacted" },
  { key: "opened", tr: "Açtı", en: "Opened" },
  { key: "replied", tr: "Cevapladı", en: "Replied" },
  { key: "bounced", tr: "Geri döndü", en: "Bounced" },
];

export default function LeadsPage() {
  const { lang, ui } = useLang();
  const [filter, setFilter] = useState<LeadStatus | "all">("all");
  const [query, setQuery] = useState("");

  const rows = leads.filter((l) => {
    const matchesFilter = filter === "all" || l.status === filter;
    const q = query.trim().toLowerCase();
    const matchesQuery =
      q === "" ||
      l.name.toLowerCase().includes(q) ||
      l.email.toLowerCase().includes(q) ||
      l.company.toLowerCase().includes(q);
    return matchesFilter && matchesQuery;
  });

  const verified = leads.filter((l) => l.verified).length;

  const counts: { label: { tr: string; en: string }; value: string; sub: { tr: string; en: string } }[] = [
    { label: { tr: "Toplam lead", en: "Total leads" }, value: leads.length.toLocaleString("en-US"), sub: { tr: "tüm kampanyalar", en: "all campaigns" } },
    { label: { tr: "Doğrulanmış", en: "Verified" }, value: `${Math.round((verified / leads.length) * 100)}%`, sub: { tr: "e-posta doğrulaması", en: "email verified" } },
    { label: { tr: "Cevapladı", en: "Replied" }, value: leads.filter((l) => l.status === "replied").length.toLocaleString("en-US"), sub: { tr: "olumlu sinyal", en: "positive signal" } },
  ];

  return (
    <div className="mx-auto max-w-[1400px] animate-fade-in space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight">
            {lang === "tr" ? "Lead'ler" : "Leads"}
          </h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {lang === "tr"
              ? "Tüm kampanyalardaki kişiler, durumlarıyla birlikte."
              : "Every contact across your campaigns, with status."}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <button className="inline-flex h-9 items-center gap-2 rounded-lg border border-border bg-card px-3.5 text-[13px] font-medium text-foreground shadow-pill transition-colors hover:bg-muted">
            <Upload className="h-4 w-4 text-muted-foreground" />
            {ui.importLeads}
          </button>
          <button className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3.5 text-[13px] font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90">
            <Plus className="h-4 w-4" />
            {lang === "tr" ? "Lead ekle" : "Add lead"}
          </button>
        </div>
      </div>

      {/* count cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        {counts.map((c) => (
          <div key={c.label.en} className="rounded-2xl border border-border bg-card p-5 shadow-soft">
            <p className="text-[13px] font-medium text-muted-foreground">{lang === "tr" ? c.label.tr : c.label.en}</p>
            <div className="mt-2 flex items-end justify-between">
              <p className="tnum text-2xl font-bold leading-none">{c.value}</p>
              <span className="text-xs text-muted-foreground">{lang === "tr" ? c.sub.tr : c.sub.en}</span>
            </div>
          </div>
        ))}
      </div>

      {/* table */}
      <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
        <div className="flex flex-wrap items-center gap-2.5 border-b border-border p-4">
          <h2 className="font-display text-[15px] font-semibold tracking-tight">
            {lang === "tr" ? "Tüm lead'ler" : "All leads"}
          </h2>
          <span className="text-[12px] text-muted-foreground">· {rows.length}</span>
          <div className="ml-auto flex items-center gap-2">
            <div className="flex h-9 items-center gap-2 rounded-lg border border-border bg-card px-3 text-sm">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={lang === "tr" ? "İsim, e-posta, şirket…" : "Name, email, company…"}
                className="w-36 bg-transparent placeholder:text-muted-foreground/70 focus:outline-none sm:w-48"
              />
            </div>
            <button className="grid h-9 w-9 place-items-center rounded-lg border border-border text-muted-foreground transition-colors hover:bg-muted">
              <Filter className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="flex flex-wrap gap-1.5 border-b border-border px-4 py-2.5">
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

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left">
                <th className="label-mono py-2.5 pl-4 font-medium text-muted-foreground">{lang === "tr" ? "Lead" : "Lead"}</th>
                <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Şirket" : "Company"}</th>
                <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Kampanya" : "Campaign"}</th>
                <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Durum" : "Status"}</th>
                <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Doğrulama" : "Verified"}</th>
                <th className="label-mono py-2.5 pr-4 text-right font-medium text-muted-foreground">{lang === "tr" ? "Son adım" : "Last step"}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((l) => {
                const lm = LEAD_META[l.status];
                return (
                  <tr key={l.id} className="border-b border-border/60 transition-colors last:border-0 hover:bg-muted/50">
                    <td className="py-3 pl-4">
                      <div className="flex items-center gap-2.5">
                        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-secondary text-[11px] font-bold text-secondary-foreground">{l.initials}</span>
                        <div className="min-w-0">
                          <p className="truncate font-semibold leading-tight">{l.name}</p>
                          <p className="truncate text-xs text-muted-foreground">{l.email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 text-[13px]">
                      <p className="font-medium leading-tight">{l.company}</p>
                      <p className="text-xs text-muted-foreground">{l.title}</p>
                    </td>
                    <td className="py-3 pr-3 text-[12.5px] text-muted-foreground">{l.campaign}</td>
                    <td className="py-3">
                      <span className={cn("inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize", lm.tone)}>
                        {lang === "tr" ? lm.tr : lm.en}
                      </span>
                    </td>
                    <td className="py-3">
                      {l.verified ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-success">
                          <Check className="h-3.5 w-3.5" strokeWidth={3} /> {lang === "tr" ? "Geçti" : "Pass"}
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-muted-foreground">
                          <X className="h-3.5 w-3.5" /> {lang === "tr" ? "Yok" : "—"}
                        </span>
                      )}
                    </td>
                    <td className="py-3 pr-4 text-right">
                      <span className="tnum text-[13px] text-muted-foreground">{l.lastStep}</span>
                    </td>
                  </tr>
                );
              })}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-10 text-center text-sm text-muted-foreground">
                    {lang === "tr" ? "Eşleşen lead yok." : "No matching leads."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
