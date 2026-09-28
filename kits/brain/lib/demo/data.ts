/**
 * Demo data — what makes the kit feel alive with zero API keys. Labels are
 * bilingual ({ tr, en }); the UI resolves them to the active language. Proper
 * nouns and free text (doc titles, names) stay as-is. Replace with real RAG
 * queries once setup wires your LLM + vector DB + source connectors.
 *
 * Brain is an AI knowledge base / internal answer engine: connect your docs
 * (Notion / Drive / Slack / Confluence), ask a question, get a cited answer.
 */
import type { L } from "@/lib/i18n/config";
import type { SourceKey } from "@/components/app/source-icon";

/* ── KPI / stat row ─────────────────────────────────────────────────────────── */
export interface DStat {
  label: L;
  value: string;
  delta?: number;
  icon: string;
  hint?: L;
}

const vsLast: L = { tr: "geçen aya göre", en: "vs last month" };

export const stats: DStat[] = [
  { label: { tr: "Belge", en: "Documents" }, value: "8,420", delta: 6.2, icon: "file-text", hint: { tr: "5 kaynaktan indekslendi", en: "indexed from 5 sources" } },
  { label: { tr: "Yanıtlanan soru", en: "Questions answered" }, value: "12,981", delta: 18.4, icon: "messages-square", hint: vsLast },
  { label: { tr: "Bağlı kaynak", en: "Sources connected" }, value: "5", delta: 0, icon: "plug", hint: { tr: "Notion, Drive, Slack…", en: "Notion, Drive, Slack…" } },
  { label: { tr: "Yönlendirme", en: "Deflection" }, value: "73%", delta: 4.1, icon: "shield-check", hint: { tr: "destek talebine düşmeden", en: "before hitting support" } },
];

/* ── AI ask bar — preloaded example Q&As ───────────────────────────────────── */
export interface Citation {
  title: string;
  source: SourceKey;
  /** Doc id this citation points at (matches a row in `documents`). */
  doc?: string;
}
export interface AnswerExample {
  q: L;
  a: L;
  citations: Citation[];
  /** confidence 0–100 */
  confidence: number;
}

export const askExamples: AnswerExample[] = [
  {
    q: { tr: "PTO politikamız nedir?", en: "What's our PTO policy?" },
    a: {
      tr: "Tam zamanlı çalışanlar yılda 25 gün ücretli izin (PTO) ve 10 resmi tatil alır. İzinler yılın başında devreder; en fazla 5 gün bir sonraki yıla aktarılabilir. İzin talepleri en az 2 hafta önceden yöneticine bildirilmeli.",
      en: "Full-time employees get 25 days of PTO per year plus 10 public holidays. PTO accrues at the start of the year; up to 5 unused days roll over. Requests should be filed at least 2 weeks ahead with your manager.",
    },
    citations: [
      { title: "People Handbook — Time Off", source: "notion", doc: "d1" },
      { title: "2026 Holiday Calendar", source: "drive", doc: "d6" },
    ],
    confidence: 96,
  },
  {
    q: { tr: "Bir üretim olayını nasıl bildiririm?", en: "How do I report a production incident?" },
    a: {
      tr: "#incidents kanalında /incident komutuyla bir olay aç, ardından önem derecesini (SEV1–SEV3) seç. SEV1 için nöbetçi mühendis otomatik çağrılır. Çözüm sonrası 48 saat içinde bir postmortem dokümanı doldurulması zorunludur.",
      en: "Open an incident with the /incident command in #incidents, then pick a severity (SEV1–SEV3). For SEV1 the on-call engineer is paged automatically. A postmortem doc is required within 48 hours of resolution.",
    },
    citations: [
      { title: "Incident Response Runbook", source: "confluence", doc: "d2" },
      { title: "#incidents — pinned", source: "slack", doc: "d8" },
    ],
    confidence: 92,
  },
  {
    q: { tr: "Enterprise planında SSO var mı?", en: "Does the Enterprise plan include SSO?" },
    a: {
      tr: "Evet. SAML ve OIDC tabanlı SSO yalnızca Enterprise planında bulunur; SCIM ile kullanıcı sağlama da dahildir. Kurulum, müşteri başarı ekibiyle yapılan bir onboarding çağrısı gerektirir.",
      en: "Yes. SAML- and OIDC-based SSO is available only on the Enterprise plan, including SCIM user provisioning. Setup requires a short onboarding call with the customer success team.",
    },
    citations: [
      { title: "Pricing & Plans (internal)", source: "notion", doc: "d3" },
      { title: "Security Whitepaper", source: "drive", doc: "d7" },
    ],
    confidence: 89,
  },
];

/* ── Documents / sources list ──────────────────────────────────────────────── */
export type SyncStatus = "synced" | "syncing" | "stale";

export interface DocRow {
  id: string;
  title: string;
  source: SourceKey;
  /** human path/space within the source */
  path: string;
  owner: string;
  lastSynced: string; // ISO
  status: SyncStatus;
  views: number;
  /** how many answers cited this doc in the last 30d */
  citedBy: number;
  /** freshness 0–100 (100 = fresh) */
  freshness: number;
  snippet: L;
}

export const documents: DocRow[] = [
  { id: "d1", title: "People Handbook — Time Off", source: "notion", path: "People / Policies", owner: "Dana Ortiz", lastSynced: "2026-06-13T22:40:00Z", status: "synced", views: 1840, citedBy: 142, freshness: 94, snippet: { tr: "PTO, resmi tatiller, devir kuralları ve izin talep akışı.", en: "PTO, public holidays, rollover rules and the request workflow." } },
  { id: "d2", title: "Incident Response Runbook", source: "confluence", path: "Engineering / On-call", owner: "Sam Reeves", lastSynced: "2026-06-13T18:05:00Z", status: "synced", views: 1210, citedBy: 98, freshness: 88, snippet: { tr: "Önem dereceleri, çağrı zinciri, iletişim şablonları ve postmortem.", en: "Severities, the paging chain, comms templates and postmortems." } },
  { id: "d3", title: "Pricing & Plans (internal)", source: "notion", path: "Revenue / GTM", owner: "Priya Nair", lastSynced: "2026-06-12T09:30:00Z", status: "stale", views: 980, citedBy: 76, freshness: 41, snippet: { tr: "Plan matrisi, ek paketler, indirim politikası ve SSO yer alır.", en: "Plan matrix, add-ons, discount policy and SSO availability." } },
  { id: "d4", title: "Brand Voice & Style Guide", source: "drive", path: "Marketing / Brand", owner: "Leo Marsh", lastSynced: "2026-06-13T20:15:00Z", status: "synced", views: 742, citedBy: 53, freshness: 90, snippet: { tr: "Ton, terminoloji, yapılması ve yapılmaması gerekenler.", en: "Tone, terminology, do's and don'ts for all written copy." } },
  { id: "d5", title: "Onboarding Checklist — New Hires", source: "confluence", path: "People / Onboarding", owner: "Dana Ortiz", lastSynced: "2026-06-11T14:00:00Z", status: "synced", views: 661, citedBy: 47, freshness: 72, snippet: { tr: "İlk gün, ilk hafta ve 30/60/90 gün kilometre taşları.", en: "Day one, first week and 30/60/90-day milestones." } },
  { id: "d6", title: "2026 Holiday Calendar", source: "drive", path: "People / Calendars", owner: "Dana Ortiz", lastSynced: "2026-06-10T08:00:00Z", status: "synced", views: 1502, citedBy: 61, freshness: 80, snippet: { tr: "Bölgelere göre resmi tatiller ve şirket kapanış günleri.", en: "Public holidays by region and company shutdown days." } },
  { id: "d7", title: "Security Whitepaper", source: "drive", path: "Trust / Security", owner: "Sam Reeves", lastSynced: "2026-06-09T16:20:00Z", status: "stale", views: 533, citedBy: 38, freshness: 36, snippet: { tr: "SOC 2, şifreleme, SSO/SCIM ve veri saklama politikaları.", en: "SOC 2, encryption, SSO/SCIM and data-retention policies." } },
  { id: "d8", title: "#incidents — pinned messages", source: "slack", path: "#incidents", owner: "On-call bot", lastSynced: "2026-06-13T23:10:00Z", status: "syncing", views: 905, citedBy: 44, freshness: 86, snippet: { tr: "Olay komutları, dashboard bağlantıları ve eskalasyon notları.", en: "Incident commands, dashboard links and escalation notes." } },
  { id: "d9", title: "Expense & Reimbursement Policy", source: "notion", path: "Finance / Policies", owner: "Marco Bianchi", lastSynced: "2026-06-12T11:45:00Z", status: "synced", views: 612, citedBy: 31, freshness: 70, snippet: { tr: "Harcama limitleri, onay zinciri ve fiş yükleme akışı.", en: "Spend limits, the approval chain and the receipt-upload flow." } },
  { id: "d10", title: "Engineering Style Guide (TS)", source: "github", path: "handbook / engineering.md", owner: "Aisha Khan", lastSynced: "2026-06-13T19:50:00Z", status: "synced", views: 1188, citedBy: 67, freshness: 91, snippet: { tr: "TypeScript kuralları, PR şablonu ve gözden geçirme beklentileri.", en: "TypeScript conventions, PR template and review expectations." } },
  { id: "d11", title: "Refund & Cancellation FAQ", source: "confluence", path: "Support / Billing", owner: "Tom Reilly", lastSynced: "2026-06-08T10:30:00Z", status: "stale", views: 1320, citedBy: 88, freshness: 33, snippet: { tr: "İade pencereleri, oran düşürme ve fatura uyuşmazlıkları.", en: "Refund windows, plan downgrades and billing disputes." } },
  { id: "d12", title: "Remote Work Guidelines", source: "notion", path: "People / Ways of Working", owner: "Dana Ortiz", lastSynced: "2026-06-13T07:25:00Z", status: "synced", views: 870, citedBy: 40, freshness: 84, snippet: { tr: "Çalışma saatleri, ekipman ödeneği ve çakışma pencereleri.", en: "Working hours, equipment stipend and overlap windows." } },
];

export const documentsMeta = {
  title: { tr: "Belgeler & Kaynaklar", en: "Documents & Sources" } as L,
  subtitle: { tr: "Bağlı kaynaklardan indekslenen bilgi tabanı.", en: "Knowledge base indexed from connected sources." } as L,
};

export const STATUS_LABEL: Record<SyncStatus, { tr: string; en: string; tone: string }> = {
  synced: { tr: "eşitlendi", en: "synced", tone: "text-success bg-success/10" },
  syncing: { tr: "eşitleniyor", en: "syncing", tone: "text-info bg-info/10" },
  stale: { tr: "eskimiş", en: "stale", tone: "text-warning-foreground bg-warning/15" },
};

/* ── Detail drawer: where a doc is cited + freshness ───────────────────────── */
export const docCitedIn: Record<string, { q: string; at: string; votes: number }[]> = {
  d1: [
    { q: "What's our PTO policy?", at: "2026-06-13T21:50:00Z", votes: 12 },
    { q: "How many days off do I get in my first year?", at: "2026-06-13T15:10:00Z", votes: 5 },
    { q: "Can I roll over unused vacation?", at: "2026-06-12T17:30:00Z", votes: 3 },
  ],
  d2: [
    { q: "How do I report a production incident?", at: "2026-06-13T20:05:00Z", votes: 9 },
    { q: "Who gets paged for a SEV1?", at: "2026-06-13T11:42:00Z", votes: 7 },
  ],
  d3: [
    { q: "Does the Enterprise plan include SSO?", at: "2026-06-13T09:20:00Z", votes: 6 },
    { q: "What add-ons can I buy on Pro?", at: "2026-06-11T13:15:00Z", votes: 2 },
  ],
};

/* ── Questions feed ────────────────────────────────────────────────────────── */
export interface QuestionRow {
  id: string;
  q: string;
  asker: string;
  answeredBy?: string; // doc id
  at: string;
  vote: "up" | "down" | null;
  channel: L;
}

export const questions: QuestionRow[] = [
  { id: "q1", q: "What's our PTO policy?", asker: "Maria Gomez", answeredBy: "d1", at: "2026-06-13T21:50:00Z", vote: "up", channel: { tr: "Slack", en: "Slack" } },
  { id: "q2", q: "How do I report a production incident?", asker: "Liam Chen", answeredBy: "d2", at: "2026-06-13T20:05:00Z", vote: "up", channel: { tr: "Web", en: "Web" } },
  { id: "q3", q: "Does the Enterprise plan include SSO?", asker: "Nadia Park", answeredBy: "d3", at: "2026-06-13T09:20:00Z", vote: "up", channel: { tr: "Eklenti", en: "Extension" } },
  { id: "q4", q: "What's the laptop refresh cycle?", asker: "Diego Santos", answeredBy: undefined, at: "2026-06-13T08:40:00Z", vote: "down", channel: { tr: "Slack", en: "Slack" } },
  { id: "q5", q: "Where is the brand font hosted?", asker: "Leo Marsh", answeredBy: "d4", at: "2026-06-12T16:12:00Z", vote: "up", channel: { tr: "Web", en: "Web" } },
  { id: "q6", q: "How long do refunds take to process?", asker: "Emma Wright", answeredBy: "d11", at: "2026-06-12T11:48:00Z", vote: null, channel: { tr: "Eklenti", en: "Extension" } },
  { id: "q7", q: "Can contractors expense a coworking desk?", asker: "Aisha Khan", answeredBy: undefined, at: "2026-06-12T10:02:00Z", vote: "down", channel: { tr: "Slack", en: "Slack" } },
];

export const questionsMeta = {
  title: { tr: "Son sorular", en: "Recent questions" } as L,
};

/* ── Knowledge gaps ────────────────────────────────────────────────────────── */
export interface GapRow {
  id: string;
  q: string;
  asks: number; // times asked, unanswered
  trend: number; // % change
}

export const gaps: GapRow[] = [
  { id: "g1", q: "What's the laptop refresh cycle?", asks: 34, trend: 22 },
  { id: "g2", q: "Can contractors expense a coworking desk?", asks: 21, trend: 11 },
  { id: "g3", q: "Do we have a referral bonus program?", asks: 18, trend: 40 },
  { id: "g4", q: "Which VPN do I use for the staging cluster?", asks: 13, trend: -6 },
];

export const gapsMeta = {
  title: { tr: "Bilgi boşlukları", en: "Knowledge gaps" } as L,
  subtitle: { tr: "Sık sorulan ama yanıtsız kalan sorular.", en: "Frequently asked, but unanswered." } as L,
};

/* ── Verification queue — cards needing expert review ──────────────────────── */
export interface VerifyRow {
  id: string;
  title: string;
  source: SourceKey;
  reason: L;
  expert: string;
  age: string; // ISO
}

export const verifications: VerifyRow[] = [
  { id: "v1", title: "Pricing & Plans (internal)", source: "notion", reason: { tr: "90 gündür doğrulanmadı", en: "unverified for 90 days" }, expert: "Priya Nair", age: "2026-03-15T00:00:00Z" },
  { id: "v2", title: "Refund & Cancellation FAQ", source: "confluence", reason: { tr: "düşük oy aldı", en: "received downvotes" }, expert: "Tom Reilly", age: "2026-06-08T00:00:00Z" },
  { id: "v3", title: "Security Whitepaper", source: "drive", reason: { tr: "kaynak güncellendi", en: "source changed" }, expert: "Sam Reeves", age: "2026-06-09T00:00:00Z" },
];

export const verificationsMeta = {
  title: { tr: "Doğrulama", en: "Verification" } as L,
  subtitle: { tr: "Uzman incelemesi bekleyen kartlar.", en: "Cards awaiting expert review." } as L,
};

/* ── Usage over time (questions/week) ──────────────────────────────────────── */
export const usage = [
  { label: "W1", value: 1840 },
  { label: "W2", value: 2110 },
  { label: "W3", value: 1980 },
  { label: "W4", value: 2460 },
  { label: "W5", value: 2890 },
  { label: "W6", value: 3120 },
  { label: "W7", value: 3480 },
  { label: "W8", value: 3910 },
];

export const usageMeta = {
  title: { tr: "Zaman içinde kullanım", en: "Usage over time" } as L,
  subtitle: { tr: "Haftada sorulan sorular", en: "Questions asked per week" } as L,
  delta: "+18.4%",
};

/* Asked vs. answered (grouped bars) */
export const askedVsAnswered = {
  labels: ["W4", "W5", "W6", "W7", "W8"],
  asked: [2460, 2890, 3120, 3480, 3910],
  answered: [1980, 2360, 2640, 2980, 3410],
};

/* ── Sources breakdown (share of answers) ──────────────────────────────────── */
export const sourceShare: { source: SourceKey; label: string; value: number; color: string }[] = [
  { source: "notion", label: "Notion", value: 38, color: "var(--seg-1)" },
  { source: "confluence", label: "Confluence", value: 27, color: "var(--seg-2)" },
  { source: "drive", label: "Google Drive", value: 21, color: "var(--seg-3)" },
  { source: "slack", label: "Slack", value: 14, color: "var(--seg-4)" },
];

/* ── Activity feed (right rail) ────────────────────────────────────────────── */
export interface DActivity {
  id: string;
  who: string;
  action: L;
  target: string;
  at: string;
  tone: "neutral" | "success" | "warning" | "info";
}

export const activity: DActivity[] = [
  { id: "a1", who: "Brain", action: { tr: "yanıtladı:", en: "answered" }, target: "“PTO policy?”", at: "2026-06-13T21:50:00Z", tone: "success" },
  { id: "a2", who: "Dana Ortiz", action: { tr: "doğruladı:", en: "verified" }, target: "People Handbook", at: "2026-06-13T20:30:00Z", tone: "info" },
  { id: "a3", who: "System", action: { tr: "eskimiş işaretledi:", en: "flagged stale" }, target: "Pricing & Plans", at: "2026-06-13T18:00:00Z", tone: "warning" },
  { id: "a4", who: "Aisha Khan", action: { tr: "kart oluşturdu:", en: "created a card" }, target: "Laptop refresh", at: "2026-06-13T13:20:00Z", tone: "success" },
  { id: "a5", who: "Slack sync", action: { tr: "indeksledi:", en: "indexed" }, target: "120 new messages", at: "2026-06-13T11:05:00Z", tone: "neutral" },
];
