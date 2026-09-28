"use client";

import { useState } from "react";
import Link from "next/link";
import {
  Plus,
  Upload,
  ArrowUpRight,
  ArrowDownRight,
  Mail,
  Clock,
  GitBranch,
  Check,
  ShieldCheck,
  ShieldAlert,
  Flame,
  Reply as ReplyIcon,
} from "lucide-react";
import { Icon } from "@/components/ui/icon";
import { Sparkline, VolumeChart, Gauge, ProgressBar } from "@/components/app/charts";
import { useLang } from "@/components/i18n/language-provider";
import { cn, formatRelative } from "@/lib/utils";
import {
  stats,
  campaigns,
  STATUS_META,
  sequenceMeta,
  sequenceSteps,
  replies,
  SENTIMENT_META,
  deliverability,
  volume,
  volumeMeta,
  mailboxes,
  MAILBOX_META,
  leads,
  LEAD_META,
  activity,
  type CampaignStatus,
} from "@/lib/demo/data";

const TONE_COLOR: Record<1 | 2 | 3 | 4, string> = {
  1: "var(--seg-1)",
  2: "var(--seg-2)",
  3: "var(--seg-3)",
  4: "var(--seg-4)",
};

const STEP_ICON = { email: Mail, wait: Clock, condition: GitBranch } as const;

const FILTERS: { key: CampaignStatus | "all"; tr: string; en: string }[] = [
  { key: "all", tr: "Tümü", en: "All" },
  { key: "active", tr: "Aktif", en: "Active" },
  { key: "warming", tr: "Isınıyor", en: "Warming" },
  { key: "paused", tr: "Duraklatıldı", en: "Paused" },
  { key: "draft", tr: "Taslak", en: "Draft" },
];

export default function DashboardPage() {
  const { t, lang } = useLang();
  const [filter, setFilter] = useState<CampaignStatus | "all">("all");
  const [activeReply, setActiveReply] = useState<string>("r1");

  const rows = campaigns.filter((c) => filter === "all" || c.status === filter);
  const totalSent = volume.reduce((s, v) => s + v.sent, 0);
  const unread = replies.filter((r) => r.unread).length;

  return (
    <div className="mx-auto max-w-[1500px] animate-fade-in space-y-6">
      {/* ── Page header ──────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <h1 className="font-display text-2xl font-bold tracking-tight">
            {lang === "tr" ? "Erişim paneli" : "Outreach"}
          </h1>
          <p className="mt-0.5 text-sm text-muted-foreground">
            {lang === "tr"
              ? "Kampanyalar, cevaplar ve teslimat tek bakışta."
              : "Campaigns, replies and deliverability at a glance."}
          </p>
        </div>
        <div className="ml-auto flex items-center gap-2">
          <button className="inline-flex h-9 items-center gap-2 rounded-lg border border-border bg-card px-3.5 text-[13px] font-medium text-foreground shadow-pill transition-colors hover:bg-muted">
            <Upload className="h-4 w-4 text-muted-foreground" />
            {lang === "tr" ? "Lead içe aktar" : "Import leads"}
          </button>
          <button className="inline-flex h-9 items-center gap-1.5 rounded-lg bg-primary px-3.5 text-[13px] font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90">
            <Plus className="h-4 w-4" />
            {lang === "tr" ? "Yeni kampanya" : "New campaign"}
          </button>
        </div>
      </div>

      {/* ── Stat row ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {stats.map((s) => {
          const up = (s.delta ?? 0) >= 0;
          const color = TONE_COLOR[s.tone];
          return (
            <div key={s.key} className="rounded-2xl border border-border bg-card p-4 shadow-soft">
              <div className="flex items-center justify-between">
                <p className="text-[12.5px] font-medium text-muted-foreground">{t(s.label)}</p>
                <span className="grid h-7 w-7 place-items-center rounded-lg" style={{ background: `color-mix(in oklch, ${color} 12%, transparent)`, color }}>
                  <Icon name={s.icon} className="h-3.5 w-3.5" />
                </span>
              </div>
              <div className="mt-2 flex items-end justify-between gap-2">
                <p className="tnum text-2xl font-bold leading-none">{s.value}</p>
                {s.delta !== undefined && (
                  <span className={cn("inline-flex items-center gap-0.5 text-[11px] font-semibold", up ? "text-success" : "text-destructive")}>
                    {up ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                    {Math.abs(s.delta).toFixed(1)}%
                  </span>
                )}
              </div>
              <div className="mt-3">
                <Sparkline data={s.spark} color={color} height={34} />
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Two-column body ──────────────────────────────────────────── */}
      <div className="grid gap-6 xl:grid-cols-[1fr_360px]">
        {/* ── Left main column ───────────────────────────────────────── */}
        <div className="min-w-0 space-y-6">
          {/* Campaigns / sequences list */}
          <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
            <div className="flex flex-wrap items-center gap-2.5 border-b border-border p-4">
              <h2 className="font-display text-[15px] font-semibold tracking-tight">
                {lang === "tr" ? "Kampanyalar" : "Campaigns"}
              </h2>
              <div className="ml-auto flex flex-wrap items-center gap-1.5">
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
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left">
                    <th className="label-mono py-2.5 pl-4 font-medium text-muted-foreground">{lang === "tr" ? "Kampanya" : "Campaign"}</th>
                    <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Durum" : "Status"}</th>
                    <th className="label-mono py-2.5 text-right font-medium text-muted-foreground">{lang === "tr" ? "Gönderilen" : "Sent"}</th>
                    <th className="label-mono py-2.5 text-right font-medium text-muted-foreground">{lang === "tr" ? "Açılma" : "Open"}</th>
                    <th className="label-mono py-2.5 text-right font-medium text-muted-foreground">{lang === "tr" ? "Cevap" : "Reply"}</th>
                    <th className="label-mono py-2.5 pr-4 font-medium text-muted-foreground">{lang === "tr" ? "İlerleme" : "Progress"}</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((c) => {
                    const st = STATUS_META[c.status];
                    return (
                      <tr key={c.id} className="border-b border-border/60 transition-colors last:border-0 hover:bg-muted/50">
                        <td className="py-3 pl-4">
                          <p className="font-semibold leading-tight">{c.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {c.steps} {lang === "tr" ? "adım" : "steps"} · {c.leads.toLocaleString("en-US")} {lang === "tr" ? "lead" : "leads"}
                          </p>
                        </td>
                        <td className="py-3">
                          <span className={cn("inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-semibold", st.tone)}>
                            <span className={cn("h-1.5 w-1.5 rounded-full", st.dot)} />
                            {lang === "tr" ? st.tr : st.en}
                          </span>
                        </td>
                        <td className="py-3 pr-3 text-right">
                          <span className="tnum font-semibold">{c.sent.toLocaleString("en-US")}</span>
                        </td>
                        <td className="py-3 pr-3 text-right">
                          <span className="tnum text-muted-foreground">{c.openPct ? `${c.openPct}%` : "—"}</span>
                        </td>
                        <td className="py-3 pr-3 text-right">
                          <span className={cn("tnum font-semibold", c.replyPct >= 9 ? "text-success" : "text-foreground")}>
                            {c.replyPct ? `${c.replyPct.toFixed(1)}%` : "—"}
                          </span>
                        </td>
                        <td className="py-3 pr-4">
                          <div className="flex items-center gap-2">
                            <ProgressBar value={c.progress} className="w-24" />
                            <span className="tnum w-9 text-right text-[11px] text-muted-foreground">{c.progress}%</span>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Sequence-step builder preview */}
          <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 className="font-display text-[15px] font-semibold tracking-tight">{t(sequenceMeta.title)}</h3>
                <p className="text-xs text-muted-foreground">{sequenceMeta.campaign} · {t(sequenceMeta.subtitle)}</p>
              </div>
              <button className="inline-flex h-8 items-center gap-1.5 rounded-lg border border-border bg-card px-3 text-[12.5px] font-medium text-foreground transition-colors hover:bg-muted">
                <Plus className="h-3.5 w-3.5 text-muted-foreground" />
                {lang === "tr" ? "Adım ekle" : "Add step"}
              </button>
            </div>

            <ol className="mt-5 space-y-0">
              {sequenceSteps.map((step, i) => {
                const I = STEP_ICON[step.kind];
                const isEmail = step.kind === "email";
                const isLast = i === sequenceSteps.length - 1;
                return (
                  <li key={i} className="relative flex gap-3.5 pb-3 last:pb-0">
                    {/* connector rail */}
                    {!isLast && <span className="absolute left-[15px] top-9 h-[calc(100%-1.5rem)] w-px bg-border" aria-hidden />}
                    <span
                      className={cn(
                        "z-10 mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full border",
                        isEmail
                          ? "border-primary/30 bg-primary/10 text-primary"
                          : step.kind === "wait"
                            ? "border-border bg-muted text-muted-foreground"
                            : "border-[var(--color-meeting)]/30 bg-[color-mix(in_oklch,var(--color-meeting)_10%,transparent)] text-[var(--color-meeting)]",
                      )}
                    >
                      <I className="h-4 w-4" />
                    </span>
                    <div className="min-w-0 flex-1 rounded-xl border border-border bg-card px-3.5 py-2.5">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-[13px] font-semibold leading-tight">{t(step.title)}</p>
                        {step.variant && (
                          <span className="rounded-md bg-secondary px-1.5 py-0.5 text-[10px] font-semibold text-secondary-foreground">{step.variant}</span>
                        )}
                      </div>
                      <p className="mt-0.5 truncate text-xs text-muted-foreground">{t(step.detail)}</p>
                      {isEmail && (
                        <div className="mt-2 flex items-center gap-4 text-[11px] text-muted-foreground">
                          <span className="inline-flex items-center gap-1">
                            <Mail className="h-3 w-3" /> {lang === "tr" ? "Açılma" : "Open"} <span className="tnum font-semibold text-foreground/80">{step.openPct}%</span>
                          </span>
                          <span className="inline-flex items-center gap-1">
                            <ReplyIcon className="h-3 w-3" /> {lang === "tr" ? "Cevap" : "Reply"} <span className="tnum font-semibold text-foreground/80">{step.replyPct}%</span>
                          </span>
                        </div>
                      )}
                    </div>
                  </li>
                );
              })}
            </ol>
          </div>

          {/* Sending volume over time */}
          <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-display text-[15px] font-semibold tracking-tight">{t(volumeMeta.title)}</h3>
                <p className="text-xs text-muted-foreground">{t(volumeMeta.subtitle)}</p>
              </div>
              <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success">
                <ArrowUpRight className="h-3 w-3" />
                {volumeMeta.delta}
              </span>
            </div>
            <div className="mt-2 flex items-baseline gap-4">
              <p className="tnum text-2xl font-bold leading-none">{totalSent.toLocaleString("en-US")}</p>
              <span className="inline-flex items-center gap-3 text-[11.5px] text-muted-foreground">
                <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-primary" />{lang === "tr" ? "Gönderilen" : "Sent"}</span>
                <span className="inline-flex items-center gap-1.5"><span className="h-2 w-2 rounded-full bg-success/40" />{lang === "tr" ? "Cevaplanan" : "Replied"}</span>
              </span>
            </div>
            <div className="mt-4">
              <VolumeChart data={volume} height={170} />
            </div>
          </div>

          {/* Leads table */}
          <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
            <div className="flex items-center justify-between border-b border-border p-4">
              <h3 className="font-display text-[15px] font-semibold tracking-tight">
                {lang === "tr" ? "Son lead'ler" : "Recent leads"}
              </h3>
              <Link href="/leads" className="inline-flex items-center gap-1 text-[13px] font-medium text-primary hover:underline">
                {lang === "tr" ? "Tümünü gör" : "View all"}
                <ArrowUpRight className="h-3.5 w-3.5" />
              </Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-left">
                    <th className="label-mono py-2.5 pl-4 font-medium text-muted-foreground">{lang === "tr" ? "Lead" : "Lead"}</th>
                    <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Şirket" : "Company"}</th>
                    <th className="label-mono py-2.5 font-medium text-muted-foreground">{lang === "tr" ? "Durum" : "Status"}</th>
                    <th className="label-mono py-2.5 pr-4 text-right font-medium text-muted-foreground">{lang === "tr" ? "Son adım" : "Last step"}</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.slice(0, 6).map((l) => {
                    const lm = LEAD_META[l.status];
                    return (
                      <tr key={l.id} className="border-b border-border/60 transition-colors last:border-0 hover:bg-muted/50">
                        <td className="py-3 pl-4">
                          <div className="flex items-center gap-2.5">
                            <span className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-secondary text-[11px] font-bold text-secondary-foreground">{l.initials}</span>
                            <div className="min-w-0">
                              <p className="truncate font-semibold leading-tight">{l.name}</p>
                              <p className="truncate text-xs text-muted-foreground">{l.title}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 text-[13px] text-muted-foreground">{l.company}</td>
                        <td className="py-3">
                          <span className={cn("inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold capitalize", lm.tone)}>
                            {lang === "tr" ? lm.tr : lm.en}
                          </span>
                        </td>
                        <td className="py-3 pr-4 text-right">
                          <span className="tnum text-[13px] text-muted-foreground">{l.lastStep}</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* ── Right column ───────────────────────────────────────────── */}
        <aside className="space-y-6 xl:sticky xl:top-2 xl:self-start">
          {/* Deliverability / warmup panel */}
          <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-[15px] font-semibold tracking-tight">
                {lang === "tr" ? "Teslimat" : "Deliverability"}
              </h3>
              <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success">
                <ShieldCheck className="h-3 w-3" />
                {lang === "tr" ? "Korumalı" : "Protected"}
              </span>
            </div>

            <div className="mt-4 flex items-center gap-5">
              <Gauge value={deliverability.health} size={108} stroke={9} color="var(--color-success)" label={`${deliverability.health}`} sub={lang === "tr" ? "sağlık" : "health"} />
              <div className="flex-1 space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground"><ShieldAlert className="h-3.5 w-3.5" />{lang === "tr" ? "Spam skoru" : "Spam score"}</span>
                  <span className="tnum text-sm font-semibold text-success">{deliverability.spamScore}/10</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground"><Flame className="h-3.5 w-3.5" />{lang === "tr" ? "Isıtma/gün" : "Warmup/day"}</span>
                  <span className="tnum text-sm font-semibold">{deliverability.warmupPerDay}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground"><Mail className="h-3.5 w-3.5" />{lang === "tr" ? "Gelen kutusu" : "Inbox rate"}</span>
                  <span className="tnum text-sm font-semibold text-success">{deliverability.inboxPlacement}%</span>
                </div>
              </div>
            </div>

            <div className="mt-4 space-y-1.5 border-t border-border pt-4">
              {deliverability.checks.map((ch) => (
                <div key={ch.key} className="flex items-center justify-between">
                  <span className="text-[12.5px] text-foreground/80">{t(ch.label)}</span>
                  {ch.ok ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-success">
                      <Check className="h-3.5 w-3.5" strokeWidth={3} /> {lang === "tr" ? "Geçti" : "Pass"}
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-warning-foreground">
                      <ShieldAlert className="h-3.5 w-3.5" /> {lang === "tr" ? "Eksik" : "Set up"}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Unified reply inbox panel */}
          <div className="rounded-2xl border border-border bg-card shadow-soft">
            <div className="flex items-center justify-between border-b border-border p-4">
              <div className="flex items-center gap-2">
                <h3 className="font-display text-[15px] font-semibold tracking-tight">
                  {lang === "tr" ? "Gelen kutusu" : "Inbox"}
                </h3>
                {unread > 0 && (
                  <span className="rounded-full bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">{unread} {lang === "tr" ? "yeni" : "new"}</span>
                )}
              </div>
              <Link href="/inbox" className="text-[13px] font-medium text-primary hover:underline">
                {lang === "tr" ? "Aç" : "Open"}
              </Link>
            </div>
            <div className="divide-y divide-border/60">
              {replies.slice(0, 5).map((r) => {
                const sm = SENTIMENT_META[r.sentiment];
                const active = r.id === activeReply;
                return (
                  <button
                    key={r.id}
                    onClick={() => setActiveReply(r.id)}
                    className={cn("flex w-full items-start gap-2.5 px-4 py-3 text-left transition-colors", active ? "bg-primary/[0.04]" : "hover:bg-muted/50")}
                  >
                    <span className="relative grid h-8 w-8 shrink-0 place-items-center rounded-full bg-secondary text-[11px] font-bold text-secondary-foreground">
                      {r.initials}
                      {r.unread && <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-primary ring-2 ring-card" />}
                    </span>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <p className={cn("truncate text-[13px] leading-tight", r.unread ? "font-bold" : "font-semibold")}>{r.name}</p>
                        <span className="shrink-0 text-[10.5px] text-muted-foreground">{formatRelative(r.at)}</span>
                      </div>
                      <p className="truncate text-[11.5px] text-muted-foreground">{t(r.preview)}</p>
                      <span className={cn("mt-1 inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 text-[10px] font-semibold", sm.cls)}>
                        <span className={cn("h-1.5 w-1.5 rounded-full", sm.dot)} />
                        {lang === "tr" ? sm.tr : sm.en}
                      </span>
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Sender accounts (mailboxes) health list */}
          <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-[15px] font-semibold tracking-tight">
                {lang === "tr" ? "Posta kutuları" : "Mailboxes"}
              </h3>
              <span className="text-[11px] text-muted-foreground">{mailboxes.length} {lang === "tr" ? "hesap" : "accounts"}</span>
            </div>
            <div className="mt-3.5 space-y-3">
              {mailboxes.map((mb) => {
                const mm = MAILBOX_META[mb.status];
                const pct = Math.round((mb.sentToday / mb.dailyLimit) * 100);
                return (
                  <div key={mb.id} className="rounded-xl border border-border p-3">
                    <div className="flex items-center gap-2">
                      <span className="grid h-7 w-7 shrink-0 place-items-center rounded-lg bg-muted text-[10px] font-bold text-muted-foreground">
                        {mb.provider === "Google" ? "G" : mb.provider === "Microsoft" ? "M" : "S"}
                      </span>
                      <p className="min-w-0 flex-1 truncate text-[12.5px] font-semibold">{mb.email}</p>
                      <span className={cn("shrink-0 rounded-full px-1.5 py-0.5 text-[10px] font-semibold capitalize", mm.tone)}>
                        {lang === "tr" ? mm.tr : mm.en}
                      </span>
                    </div>
                    <div className="mt-2 flex items-center gap-2">
                      <ProgressBar value={pct} className="flex-1" />
                      <span className="tnum w-16 shrink-0 text-right text-[10.5px] text-muted-foreground">
                        {mb.sentToday}/{mb.dailyLimit}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Activity feed */}
          <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
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
      </div>
    </div>
  );
}
