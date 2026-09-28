"use client";

import { useState } from "react";
import { Plus, Search, RefreshCw, Check } from "lucide-react";
import { SourceIcon, SOURCE_LABEL, type SourceKey } from "@/components/app/source-icon";
import { useLang } from "@/components/i18n/language-provider";
import { cn, formatNumber, formatRelative } from "@/lib/utils";
import { documents, STATUS_LABEL } from "@/lib/demo/data";

interface Connector {
  source: SourceKey;
  connected: boolean;
  docs: number;
  lastSync: string;
}

const connectors: Connector[] = [
  { source: "notion", connected: true, docs: 1240, lastSync: "2026-06-13T22:40:00Z" },
  { source: "drive", connected: true, docs: 3180, lastSync: "2026-06-13T21:10:00Z" },
  { source: "slack", connected: true, docs: 2640, lastSync: "2026-06-13T23:10:00Z" },
  { source: "confluence", connected: true, docs: 980, lastSync: "2026-06-13T18:05:00Z" },
  { source: "github", connected: true, docs: 380, lastSync: "2026-06-13T19:50:00Z" },
  { source: "web", connected: false, docs: 0, lastSync: "" },
];

function fmtDateTime(iso: string) {
  const d = new Date(iso);
  return `${d.getUTCDate()} ${d.toLocaleString("en-US", { month: "short", timeZone: "UTC" })} · ${String(d.getUTCHours()).padStart(2, "0")}:${String(d.getUTCMinutes()).padStart(2, "0")}`;
}

export default function SourcesPage() {
  const { lang } = useLang();
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<SourceKey | "all">("all");

  const rows = documents.filter(
    (d) =>
      (filter === "all" || d.source === filter) &&
      (!query || d.title.toLowerCase().includes(query.toLowerCase()) || SOURCE_LABEL[d.source].toLowerCase().includes(query.toLowerCase())),
  );

  return (
    <div className="mx-auto max-w-[1300px] animate-fade-in space-y-6">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight">{lang === "tr" ? "Kaynaklar" : "Sources"}</h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {lang === "tr" ? "Bağlı konnektörleri ve indekslenen belgeleri yönet." : "Manage connected connectors and indexed documents."}
          </p>
        </div>
        <button className="ml-auto inline-flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3.5 text-[13px] font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90">
          <Plus className="h-4 w-4" />
          {lang === "tr" ? "Konnektör ekle" : "Add connector"}
        </button>
      </div>

      {/* Connector cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {connectors.map((c) => (
          <div key={c.source} className="rounded-2xl border border-border bg-card p-4 shadow-soft">
            <div className="flex items-center gap-3">
              <SourceIcon source={c.source} size={40} />
              <div className="min-w-0 flex-1">
                <p className="font-semibold leading-tight">{SOURCE_LABEL[c.source]}</p>
                <p className="text-xs text-muted-foreground">
                  {c.connected ? `${formatNumber(c.docs)} ${lang === "tr" ? "belge" : "docs"}` : lang === "tr" ? "bağlı değil" : "not connected"}
                </p>
              </div>
              {c.connected ? (
                <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success">
                  <Check className="h-3 w-3" /> {lang === "tr" ? "Bağlı" : "Connected"}
                </span>
              ) : (
                <button className="rounded-lg bg-primary px-2.5 py-1 text-[12px] font-semibold text-primary-foreground transition-opacity hover:opacity-90">
                  {lang === "tr" ? "Bağla" : "Connect"}
                </button>
              )}
            </div>
            {c.connected && (
              <div className="mt-3 flex items-center justify-between border-t border-border pt-3 text-[12px] text-muted-foreground">
                <span className="inline-flex items-center gap-1.5">
                  <RefreshCw className="h-3 w-3" /> {lang === "tr" ? "Eşitlendi" : "Synced"} {formatRelative(c.lastSync)}
                </span>
                <button className="font-medium text-primary hover:underline">{lang === "tr" ? "Yapılandır" : "Configure"}</button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Indexed documents */}
      <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
        <div className="flex flex-wrap items-center gap-2.5 border-b border-border p-4">
          <h2 className="font-display text-[15px] font-semibold tracking-tight">{lang === "tr" ? "İndekslenen belgeler" : "Indexed documents"}</h2>
          <div className="ml-auto flex flex-wrap items-center gap-2">
            <div className="flex flex-wrap items-center gap-1">
              {(["all", "notion", "drive", "slack", "confluence", "github"] as const).map((f) => (
                <button
                  key={f}
                  onClick={() => setFilter(f)}
                  className={cn(
                    "rounded-full px-2.5 py-1 text-[12px] font-medium transition-colors",
                    filter === f ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted",
                  )}
                >
                  {f === "all" ? (lang === "tr" ? "Tümü" : "All") : SOURCE_LABEL[f]}
                </button>
              ))}
            </div>
            <div className="flex h-9 items-center gap-2 rounded-lg border border-border bg-card px-3 text-sm">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={lang === "tr" ? "Ara…" : "Search…"}
                className="w-28 bg-transparent text-foreground placeholder:text-muted-foreground/70 focus:outline-none sm:w-36"
              />
            </div>
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left">
                <th className="label-mono py-2.5 pl-4 font-medium text-muted-foreground">{lang === "tr" ? "Belge" : "Document"}</th>
                <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Sahip" : "Owner"}</th>
                <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Eşitlenme" : "Synced"}</th>
                <th className="label-mono py-2.5 text-right font-medium text-muted-foreground">{lang === "tr" ? "Görüntülenme" : "Views"}</th>
                <th className="label-mono py-2.5 pr-4 text-right font-medium text-muted-foreground">{lang === "tr" ? "Durum" : "Status"}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const st = STATUS_LABEL[row.status];
                return (
                  <tr key={row.id} className="border-b border-border/60 transition-colors last:border-0 hover:bg-muted/40">
                    <td className="py-3 pl-4">
                      <div className="flex items-center gap-2.5">
                        <SourceIcon source={row.source} size={28} />
                        <div className="min-w-0">
                          <p className="truncate font-semibold leading-tight">{row.title}</p>
                          <p className="truncate text-xs text-muted-foreground">{row.path}</p>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-[13px]">{row.owner}</td>
                    <td className="py-3 pr-4"><span className="tnum whitespace-nowrap text-[13px] text-muted-foreground">{fmtDateTime(row.lastSynced)}</span></td>
                    <td className="py-3 pr-4 text-right tnum font-semibold">{formatNumber(row.views)}</td>
                    <td className="py-3 pr-4 text-right">
                      <span className={cn("inline-flex rounded-full px-1.5 py-0.5 text-[10px] font-semibold capitalize", st.tone)}>
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
    </div>
  );
}
