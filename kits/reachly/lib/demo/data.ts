/**
 * Demo data — what makes the kit feel alive with zero API keys. Labels are
 * bilingual ({ tr, en }); the dashboard resolves them to the active language.
 * Proper nouns and free text (names, emails, subjects) stay as-is. Replace with
 * real queries once setup wires your integrations.
 *
 * Domain: cold email outreach — campaigns, sequences, a unified reply inbox,
 * sender mailboxes, deliverability/warmup, sending volume, and leads.
 */
import type { L } from "@/lib/i18n/config";

const vsLast: L = { tr: "geçen haftaya göre", en: "vs last week" };

/* ── Stat row (Sent · Open · Reply · Positive) ─────────────────────────────── */
export interface StatCard {
  key: string;
  label: L;
  value: string;
  delta?: number;
  icon: string;
  hint?: L;
  spark: number[];
  tone: 1 | 2 | 3 | 4;
}

export const stats: StatCard[] = [
  { key: "sent", label: { tr: "Gönderilen", en: "Sent" }, value: "48,210", delta: 9.4, icon: "send", hint: vsLast, tone: 1, spark: [3100, 3400, 3300, 3900, 4200, 4600, 4810] },
  { key: "open", label: { tr: "Açılma oranı", en: "Open rate" }, value: "61.8%", delta: 3.2, icon: "mail-open", hint: vsLast, tone: 2, spark: [54, 56, 55, 58, 59, 61, 61.8] },
  { key: "reply", label: { tr: "Cevap oranı", en: "Reply rate" }, value: "8.4%", delta: 1.1, icon: "reply", hint: vsLast, tone: 3, spark: [6.2, 6.8, 6.6, 7.2, 7.9, 8.1, 8.4] },
  { key: "positive", label: { tr: "Olumlu cevap", en: "Positive replies" }, value: "312", delta: 14.6, icon: "thumbs-up", hint: vsLast, tone: 4, spark: [180, 205, 198, 232, 266, 290, 312] },
];

/* ── Campaigns / sequences list ────────────────────────────────────────────── */
export type CampaignStatus = "active" | "paused" | "warming" | "draft" | "completed";

export interface Campaign {
  id: string;
  name: string;
  status: CampaignStatus;
  steps: number;
  leads: number;
  sent: number;
  openPct: number;
  replyPct: number;
  positive: number;
  /** 0–100 send progress through the lead list. */
  progress: number;
  mailbox: string;
}

export const campaigns: Campaign[] = [
  { id: "cm1", name: "Q3 SaaS Founders — US", status: "active", steps: 4, leads: 1840, sent: 6120, openPct: 64, replyPct: 9.2, positive: 88, progress: 72, mailbox: "alex@reachly.io" },
  { id: "cm2", name: "Agency Owners — Warm Intro", status: "active", steps: 3, leads: 920, sent: 2480, openPct: 71, replyPct: 11.4, positive: 64, progress: 58, mailbox: "alex@getreachly.com" },
  { id: "cm3", name: "E-commerce DTC — Black Friday", status: "warming", steps: 5, leads: 2600, sent: 0, openPct: 0, replyPct: 0, positive: 0, progress: 4, mailbox: "ops@reachly.io" },
  { id: "cm4", name: "Series A CTOs — Hiring", status: "active", steps: 4, leads: 640, sent: 1880, openPct: 59, replyPct: 7.8, positive: 41, progress: 81, mailbox: "alex@reachly.io" },
  { id: "cm5", name: "Marketing Leaders — Webinar", status: "paused", steps: 3, leads: 1120, sent: 3340, openPct: 55, replyPct: 6.1, positive: 29, progress: 64, mailbox: "team@reachly.io" },
  { id: "cm6", name: "Cold Re-engage — Q1 No-shows", status: "completed", steps: 2, leads: 480, sent: 940, openPct: 48, replyPct: 5.2, positive: 18, progress: 100, mailbox: "alex@getreachly.com" },
  { id: "cm7", name: "Local Restaurants — Demo", status: "draft", steps: 4, leads: 0, sent: 0, openPct: 0, replyPct: 0, positive: 0, progress: 0, mailbox: "—" },
];

export const STATUS_META: Record<CampaignStatus, { tr: string; en: string; tone: string; dot: string }> = {
  active:    { tr: "aktif", en: "active", tone: "text-success bg-success/10", dot: "bg-success" },
  paused:    { tr: "duraklatıldı", en: "paused", tone: "text-warning-foreground bg-warning/15", dot: "bg-warning" },
  warming:   { tr: "ısınıyor", en: "warming", tone: "text-info bg-info/10", dot: "bg-info" },
  draft:     { tr: "taslak", en: "draft", tone: "text-muted-foreground bg-muted", dot: "bg-muted-foreground" },
  completed: { tr: "tamamlandı", en: "completed", tone: "text-foreground/70 bg-secondary", dot: "bg-foreground/40" },
};

/* ── Sequence-step builder preview ─────────────────────────────────────────── */
export type StepKind = "email" | "wait" | "condition";

export interface SequenceStep {
  kind: StepKind;
  title: L;
  detail: L;
  /** for email steps */
  openPct?: number;
  replyPct?: number;
  variant?: string;
}

export const sequenceMeta = {
  campaign: "Q3 SaaS Founders — US",
  title: { tr: "Dizi adımları", en: "Sequence steps" } as L,
  subtitle: { tr: "4 adım · cevap gelince durur", en: "4 steps · stops on reply" } as L,
};

export const sequenceSteps: SequenceStep[] = [
  { kind: "email", title: { tr: "Adım 1 · İlk dokunuş", en: "Step 1 · First touch" }, detail: { tr: "“{firstName}, {company} için hızlı bir fikir”", en: "“Quick idea for {company}, {firstName}”" }, openPct: 64, replyPct: 5.1, variant: "A/B" },
  { kind: "wait", title: { tr: "Bekle 2 gün", en: "Wait 2 days" }, detail: { tr: "Hafta içi, çalışma saatleri", en: "Weekdays, business hours" } },
  { kind: "email", title: { tr: "Adım 2 · Takip", en: "Step 2 · Follow-up" }, detail: { tr: "“Yukarıdakini gördün mü?”", en: "“Did you get a chance to see this?”" }, openPct: 58, replyPct: 3.4 },
  { kind: "wait", title: { tr: "Bekle 3 gün", en: "Wait 3 days" }, detail: { tr: "Açmayanları atla", en: "Skip non-openers" } },
  { kind: "condition", title: { tr: "Koşul · Açtıysa", en: "Condition · If opened" }, detail: { tr: "Açanlar → vaka çalışması dalı", en: "Openers → case-study branch" } },
  { kind: "email", title: { tr: "Adım 3 · Vaka çalışması", en: "Step 3 · Case study" }, detail: { tr: "“{company} gibi 3 ekibin sonuçları”", en: "“Results from 3 teams like {company}”" }, openPct: 52, replyPct: 2.8 },
  { kind: "wait", title: { tr: "Bekle 4 gün", en: "Wait 4 days" }, detail: { tr: "Son dokunuş öncesi", en: "Before the breakup" } },
  { kind: "email", title: { tr: "Adım 4 · Kapanış", en: "Step 4 · Breakup" }, detail: { tr: "“Bunu kapatayım mı?”", en: "“Should I close this out?”" }, openPct: 49, replyPct: 4.2 },
];

/* ── Unified reply inbox ───────────────────────────────────────────────────── */
export type Sentiment = "interested" | "meeting" | "notnow" | "ooo" | "unsubscribe";

export interface Reply {
  id: string;
  name: string;
  email: string;
  company: string;
  campaign: string;
  subject: string;
  preview: L;
  sentiment: Sentiment;
  at: string;
  unread: boolean;
  initials: string;
}

export const SENTIMENT_META: Record<Sentiment, { tr: string; en: string; cls: string; dot: string }> = {
  interested:  { tr: "İlgileniyor", en: "Interested", cls: "text-[var(--color-interested)] bg-[color-mix(in_oklch,var(--color-interested)_12%,transparent)]", dot: "bg-[var(--color-interested)]" },
  meeting:     { tr: "Toplantı", en: "Meeting booked", cls: "text-[var(--color-meeting)] bg-[color-mix(in_oklch,var(--color-meeting)_12%,transparent)]", dot: "bg-[var(--color-meeting)]" },
  notnow:      { tr: "Şimdi değil", en: "Not now", cls: "text-[var(--color-notnow)] bg-[color-mix(in_oklch,var(--color-notnow)_18%,transparent)]", dot: "bg-[var(--color-notnow)]" },
  ooo:         { tr: "Ofis dışı", en: "Out of office", cls: "text-[var(--color-ooo)] bg-[color-mix(in_oklch,var(--color-ooo)_12%,transparent)]", dot: "bg-[var(--color-ooo)]" },
  unsubscribe: { tr: "Çıkış", en: "Unsubscribe", cls: "text-[var(--color-unsub)] bg-[color-mix(in_oklch,var(--color-unsub)_12%,transparent)]", dot: "bg-[var(--color-unsub)]" },
};

export const replies: Reply[] = [
  { id: "r1", name: "Maria Gomez", email: "maria@northwind.co", company: "Northwind", campaign: "Q3 SaaS Founders — US", subject: "Re: Quick idea for Northwind", preview: { tr: "Bu ilginç görünüyor — perşembe 30 dk konuşabilir miyiz?", en: "This looks interesting — can we hop on a 30-min call Thursday?" }, sentiment: "meeting", at: "2026-06-13T09:24:00Z", unread: true, initials: "MG" },
  { id: "r2", name: "Liam Chen", email: "liam@parable.io", company: "Parable", campaign: "Agency Owners — Warm Intro", subject: "Re: Quick idea for Parable", preview: { tr: "Evet, daha fazla bilgi gönder. Fiyatlandırma sayfan var mı?", en: "Yes, send me more info. Do you have a pricing page?" }, sentiment: "interested", at: "2026-06-13T08:51:00Z", unread: true, initials: "LC" },
  { id: "r3", name: "Nadia Park", email: "nadia@formwork.studio", company: "Formwork", campaign: "Series A CTOs — Hiring", subject: "Re: Results from 3 teams like Formwork", preview: { tr: "Şu an Q4'e kadar dolu değiliz, ama Ocak'ta tekrar yaz.", en: "We're heads-down until Q4, but circle back in January." }, sentiment: "notnow", at: "2026-06-13T08:12:00Z", unread: true, initials: "NP" },
  { id: "r4", name: "Tom Reilly", email: "tom@cedarworks.com", company: "Cedarworks", campaign: "Q3 SaaS Founders — US", subject: "Automatic reply: Out of office", preview: { tr: "20 Haziran'a kadar ofis dışındayım, sınırlı erişim.", en: "I'm out of office until June 20 with limited access." }, sentiment: "ooo", at: "2026-06-13T07:40:00Z", unread: false, initials: "TR" },
  { id: "r5", name: "Aisha Khan", email: "aisha@lumen.app", company: "Lumen", campaign: "Marketing Leaders — Webinar", subject: "Re: Did you get a chance to see this?", preview: { tr: "Bizim için çok uygun. Demo'ya nasıl başlarız?", en: "This is a great fit for us. How do we start a demo?" }, sentiment: "interested", at: "2026-06-12T19:08:00Z", unread: false, initials: "AK" },
  { id: "r6", name: "Diego Santos", email: "diego@harvest.farm", company: "Harvest", campaign: "Q3 SaaS Founders — US", subject: "Re: Quick idea for Harvest", preview: { tr: "Lütfen beni listeden çıkar, teşekkürler.", en: "Please remove me from your list, thanks." }, sentiment: "unsubscribe", at: "2026-06-12T17:33:00Z", unread: false, initials: "DS" },
  { id: "r7", name: "Emma Wright", email: "emma@brightline.dev", company: "Brightline", campaign: "Agency Owners — Warm Intro", subject: "Re: Quick idea for Brightline", preview: { tr: "Cuma sabah 10:00 uygun. Davet gönderir misin?", en: "Friday 10am works. Can you send a calendar invite?" }, sentiment: "meeting", at: "2026-06-12T15:20:00Z", unread: false, initials: "EW" },
  { id: "r8", name: "Owen Mills", email: "owen@meridian.co", company: "Meridian", campaign: "Series A CTOs — Hiring", subject: "Re: Should I close this out?", preview: { tr: "Yakala beni! Detayları konuşalım.", en: "Don't close it! Let's talk details." }, sentiment: "interested", at: "2026-06-12T11:46:00Z", unread: false, initials: "OM" },
];

/* ── Deliverability / warmup panel ─────────────────────────────────────────── */
export const deliverability = {
  health: 92, // mailbox health gauge (0–100)
  spamScore: 0.6, // lower is better (out of 10)
  warmupPerDay: 38,
  inboxPlacement: 98,
  checks: [
    { key: "spf", label: { tr: "SPF kaydı", en: "SPF record" } as L, ok: true },
    { key: "dkim", label: { tr: "DKIM imzası", en: "DKIM signature" } as L, ok: true },
    { key: "dmarc", label: { tr: "DMARC politikası", en: "DMARC policy" } as L, ok: true },
    { key: "blacklist", label: { tr: "Kara liste taraması", en: "Blacklist scan" } as L, ok: true },
    { key: "custom", label: { tr: "Özel takip alanı", en: "Custom tracking domain" } as L, ok: false },
  ],
};

/* ── Sending volume over time (last 14 days) ───────────────────────────────── */
export const volumeMeta = {
  title: { tr: "Gönderim hacmi", en: "Sending volume" } as L,
  subtitle: { tr: "Son 14 gün · gönderilen vs cevaplanan", en: "Last 14 days · sent vs replied" } as L,
  delta: "+9.4%",
};

export const volume: { label: string; sent: number; replied: number }[] = [
  { label: "31", sent: 2980, replied: 210 },
  { label: "01", sent: 3120, replied: 232 },
  { label: "02", sent: 3060, replied: 224 },
  { label: "03", sent: 3340, replied: 261 },
  { label: "04", sent: 2480, replied: 198 },
  { label: "05", sent: 1240, replied: 96 },
  { label: "06", sent: 980, replied: 71 },
  { label: "07", sent: 3410, replied: 268 },
  { label: "08", sent: 3680, replied: 291 },
  { label: "09", sent: 3520, replied: 279 },
  { label: "10", sent: 3900, replied: 318 },
  { label: "11", sent: 4120, replied: 342 },
  { label: "12", sent: 4480, replied: 366 },
  { label: "13", sent: 4810, replied: 401 },
];

/* ── Sender accounts (mailboxes) health list ───────────────────────────────── */
export type MailboxStatus = "healthy" | "warming" | "limited" | "paused";

export interface Mailbox {
  id: string;
  email: string;
  provider: "Google" | "Microsoft" | "SMTP";
  status: MailboxStatus;
  health: number;
  sentToday: number;
  dailyLimit: number;
  warmupPerDay: number;
  domain: string;
}

export const MAILBOX_META: Record<MailboxStatus, { tr: string; en: string; tone: string }> = {
  healthy: { tr: "sağlıklı", en: "healthy", tone: "text-success bg-success/10" },
  warming: { tr: "ısınıyor", en: "warming", tone: "text-info bg-info/10" },
  limited: { tr: "sınırlı", en: "limited", tone: "text-warning-foreground bg-warning/15" },
  paused:  { tr: "duraklatıldı", en: "paused", tone: "text-muted-foreground bg-muted" },
};

export const mailboxes: Mailbox[] = [
  { id: "mb1", email: "alex@reachly.io", provider: "Google", status: "healthy", health: 96, sentToday: 184, dailyLimit: 250, warmupPerDay: 40, domain: "reachly.io" },
  { id: "mb2", email: "alex@getreachly.com", provider: "Google", status: "healthy", health: 91, sentToday: 142, dailyLimit: 250, warmupPerDay: 38, domain: "getreachly.com" },
  { id: "mb3", email: "ops@reachly.io", provider: "Microsoft", status: "warming", health: 74, sentToday: 22, dailyLimit: 80, warmupPerDay: 44, domain: "reachly.io" },
  { id: "mb4", email: "team@reachly.io", provider: "SMTP", status: "limited", health: 63, sentToday: 96, dailyLimit: 120, warmupPerDay: 30, domain: "reachly.io" },
  { id: "mb5", email: "hello@reachly.app", provider: "Google", status: "paused", health: 58, sentToday: 0, dailyLimit: 200, warmupPerDay: 0, domain: "reachly.app" },
];

/* ── Leads table ───────────────────────────────────────────────────────────── */
export type LeadStatus = "new" | "contacted" | "opened" | "replied" | "bounced" | "unsubscribed";

export interface Lead {
  id: string;
  name: string;
  email: string;
  title: string;
  company: string;
  campaign: string;
  status: LeadStatus;
  lastStep: string;
  verified: boolean;
  initials: string;
}

export const LEAD_META: Record<LeadStatus, { tr: string; en: string; tone: string }> = {
  new:          { tr: "yeni", en: "new", tone: "text-muted-foreground bg-muted" },
  contacted:    { tr: "ulaşıldı", en: "contacted", tone: "text-info bg-info/10" },
  opened:       { tr: "açtı", en: "opened", tone: "text-[var(--color-meeting)] bg-[color-mix(in_oklch,var(--color-meeting)_10%,transparent)]" },
  replied:      { tr: "cevapladı", en: "replied", tone: "text-success bg-success/10" },
  bounced:      { tr: "geri döndü", en: "bounced", tone: "text-warning-foreground bg-warning/15" },
  unsubscribed: { tr: "çıktı", en: "unsubscribed", tone: "text-destructive bg-destructive/10" },
};

export const leads: Lead[] = [
  { id: "l1", name: "Maria Gomez", email: "maria@northwind.co", title: "CEO", company: "Northwind", campaign: "Q3 SaaS Founders — US", status: "replied", lastStep: "Step 1", verified: true, initials: "MG" },
  { id: "l2", name: "Liam Chen", email: "liam@parable.io", title: "Founder", company: "Parable", campaign: "Agency Owners — Warm Intro", status: "replied", lastStep: "Step 1", verified: true, initials: "LC" },
  { id: "l3", name: "Nadia Park", email: "nadia@formwork.studio", title: "VP Eng", company: "Formwork", campaign: "Series A CTOs — Hiring", status: "opened", lastStep: "Step 3", verified: true, initials: "NP" },
  { id: "l4", name: "Tom Reilly", email: "tom@cedarworks.com", title: "COO", company: "Cedarworks", campaign: "Q3 SaaS Founders — US", status: "contacted", lastStep: "Step 2", verified: true, initials: "TR" },
  { id: "l5", name: "Aisha Khan", email: "aisha@lumen.app", title: "Head of Growth", company: "Lumen", campaign: "Marketing Leaders — Webinar", status: "replied", lastStep: "Step 2", verified: true, initials: "AK" },
  { id: "l6", name: "Diego Santos", email: "diego@harvest.farm", title: "Owner", company: "Harvest", campaign: "Q3 SaaS Founders — US", status: "unsubscribed", lastStep: "Step 1", verified: true, initials: "DS" },
  { id: "l7", name: "Emma Wright", email: "emma@brightline.dev", title: "CTO", company: "Brightline", campaign: "Agency Owners — Warm Intro", status: "opened", lastStep: "Step 2", verified: true, initials: "EW" },
  { id: "l8", name: "Owen Mills", email: "owen@meridian.co", title: "Co-founder", company: "Meridian", campaign: "Series A CTOs — Hiring", status: "replied", lastStep: "Step 4", verified: true, initials: "OM" },
  { id: "l9", name: "Priya Nair", email: "priya@cadence.io", title: "VP Sales", company: "Cadence", campaign: "Q3 SaaS Founders — US", status: "new", lastStep: "—", verified: false, initials: "PN" },
  { id: "l10", name: "Marco Bianchi", email: "marco@volta.studio", title: "Director", company: "Volta", campaign: "Marketing Leaders — Webinar", status: "bounced", lastStep: "Step 1", verified: false, initials: "MB" },
  { id: "l11", name: "Hana Suzuki", email: "hana@orbit.team", title: "Founder", company: "Orbit", campaign: "Agency Owners — Warm Intro", status: "contacted", lastStep: "Step 1", verified: true, initials: "HS" },
  { id: "l12", name: "Felix Braun", email: "felix@northstar.co", title: "Head of Ops", company: "Northstar", campaign: "Series A CTOs — Hiring", status: "new", lastStep: "—", verified: true, initials: "FB" },
];

/* ── Activity feed ─────────────────────────────────────────────────────────── */
export interface ActivityItem {
  id: string;
  who: string;
  action: L;
  target: string;
  at: string;
  tone: "neutral" | "success" | "warning" | "info";
}

export const activity: ActivityItem[] = [
  { id: "a1", who: "Maria Gomez", action: { tr: "toplantı ayarladı:", en: "booked a meeting from" }, target: "Q3 SaaS Founders", at: "2026-06-13T09:24:00Z", tone: "success" },
  { id: "a2", who: "Reachly", action: { tr: "posta kutusunu ısıttı:", en: "warmed up mailbox" }, target: "ops@reachly.io", at: "2026-06-13T08:55:00Z", tone: "info" },
  { id: "a3", who: "Diego Santos", action: { tr: "abonelikten çıktı:", en: "unsubscribed from" }, target: "Q3 SaaS Founders", at: "2026-06-12T17:33:00Z", tone: "warning" },
  { id: "a4", who: "Liam Chen", action: { tr: "cevapladı:", en: "replied to" }, target: "Step 1", at: "2026-06-12T16:05:00Z", tone: "success" },
  { id: "a5", who: "Reachly", action: { tr: "diziyi tamamladı:", en: "completed sequence" }, target: "Cold Re-engage — Q1", at: "2026-06-12T11:48:00Z", tone: "neutral" },
];

/* ── Landing interactive demo — a 3-step sequence the visitor "launches" ───── */
export const launchDemo = {
  steps: [
    { kind: "email" as StepKind, label: { tr: "Adım 1 · İlk dokunuş", en: "Step 1 · First touch" } as L, sub: "“Quick idea for {company}”" },
    { kind: "wait" as StepKind, label: { tr: "Bekle 2 gün", en: "Wait 2 days" } as L, sub: { tr: "hafta içi", en: "weekdays" } },
    { kind: "email" as StepKind, label: { tr: "Adım 2 · Takip", en: "Step 2 · Follow-up" } as L, sub: "“Did you get a chance to see this?”" },
  ],
  // animated counters the demo ticks up to after "launch"
  result: { sent: 1840, opens: 1137, replies: 154, positive: 41 },
};
