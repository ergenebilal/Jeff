import type { L } from "@/lib/i18n/config";

export type StageId = "lead" | "qualified" | "proposal" | "negotiation" | "won";

export interface Stage {
  id: StageId;
  label: L;
  prob: number;
  color: string;
}

export const stages: Stage[] = [
  { id: "lead", label: { tr: "Lead", en: "Lead" }, prob: 0.1, color: "var(--stage-lead)" },
  { id: "qualified", label: { tr: "Nitelikli", en: "Qualified" }, prob: 0.3, color: "var(--stage-qualified)" },
  { id: "proposal", label: { tr: "Teklif", en: "Proposal" }, prob: 0.55, color: "var(--stage-proposal)" },
  { id: "negotiation", label: { tr: "Müzakere", en: "Negotiation" }, prob: 0.8, color: "var(--stage-negotiation)" },
  { id: "won", label: { tr: "Kazanıldı", en: "Won" }, prob: 1, color: "var(--stage-won)" },
];

export const stageById = Object.fromEntries(stages.map((s) => [s.id, s])) as Record<StageId, Stage>;

export interface Rep {
  id: string;
  name: string;
  initials: string;
  color: string;
}

export const reps: Rep[] = [
  { id: "r1", name: "Bilal Ergene", initials: "BE", color: "var(--seg-1)" },
  { id: "r2", name: "ErgeneAI Satış", initials: "EA", color: "var(--seg-2)" },
];

export const repById = Object.fromEntries(reps.map((r) => [r.id, r])) as Record<string, Rep>;

export interface Deal {
  id: string;
  title: string;
  company: string;
  value: number;
  stage: StageId;
  ownerId: string;
  daysInStage: number;
  closeDate: string;
  contactId: string;
}

export const deals: Deal[] = [
  // — LEAD aşaması (yeni, henüz nitelikli değil)
  { id: "d1", title: "AI KB Demo", company: "İstanbul Dental Group", value: 15000, stage: "lead", ownerId: "r1", daysInStage: 1, closeDate: "2026-08-15", contactId: "p1" },
  { id: "d2", title: "CRM Kurulumu", company: "Marmara Emlak", value: 12000, stage: "lead", ownerId: "r2", daysInStage: 3, closeDate: "2026-08-20", contactId: "p2" },
  { id: "d3", title: "AI Asistan Paketi", company: "Ankara Hukuk", value: 18000, stage: "lead", ownerId: "r1", daysInStage: 5, closeDate: "2026-08-25", contactId: "p3" },
  { id: "d4", title: "Email Marketing", company: "Ege Tekstil", value: 9000, stage: "lead", ownerId: "r2", daysInStage: 2, closeDate: "2026-09-01", contactId: "p4" },
  { id: "d5", title: "Sosyal Medya Paketi", company: "Moda House", value: 11000, stage: "lead", ownerId: "r1", daysInStage: 4, closeDate: "2026-09-05", contactId: "p5" },
  // — NITELIKLI (görüşme yapıldı, ihtiyaç net)
  { id: "d6", title: "Klinik CRM + Randevu", company: "Bursa Özel Sağlık", value: 24000, stage: "qualified", ownerId: "r1", daysInStage: 6, closeDate: "2026-07-30", contactId: "p6" },
  { id: "d7", title: "AI Telefon Asistanı", company: "Adana Diş Kliniği", value: 15000, stage: "qualified", ownerId: "r2", daysInStage: 8, closeDate: "2026-08-05", contactId: "p7" },
  { id: "d8", title: "Full Paket (Brain+CRM+Mail)", company: "Trabzon Ticaret", value: 32000, stage: "qualified", ownerId: "r1", daysInStage: 4, closeDate: "2026-08-10", contactId: "p8" },
  // — TEKLIF (fiyat teklifi sunuldu)
  { id: "d9", title: "SEO + Web Sitesi", company: "İzmir Avukatlık", value: 21000, stage: "proposal", ownerId: "r1", daysInStage: 7, closeDate: "2026-07-18", contactId: "p9" },
  { id: "d10", title: "Lead Gen Sistemi", company: "Antalya Turizm", value: 16000, stage: "proposal", ownerId: "r2", daysInStage: 10, closeDate: "2026-07-25", contactId: "p10" },
  // — MUZAKERE (fiyat/pazarlık aşamasında)
  { id: "d11", title: "Brain Enterprise", company: "Konya Gıda Sanayi", value: 42000, stage: "negotiation", ownerId: "r1", daysInStage: 5, closeDate: "2026-07-12", contactId: "p11" },
  { id: "d12", title: "Tüm Kitler Paketi", company: "Gaziantep Tekstil", value: 55000, stage: "negotiation", ownerId: "r2", daysInStage: 9, closeDate: "2026-07-15", contactId: "p12" },
  // — KAZANILDI
  { id: "d13", title: "Brain KB Başlangıç", company: "Eskişehir Danışmanlık", value: 6000, stage: "won", ownerId: "r1", daysInStage: 1, closeDate: "2026-06-20", contactId: "p13" },
  { id: "d14", title: "Reachly Email Paketi", company: "Samsun Dijital", value: 7500, stage: "won", ownerId: "r2", daysInStage: 1, closeDate: "2026-06-25", contactId: "p14" },
];

export const dealColumns = [
  { key: "title", label: { tr: "Deal", en: "Deal" } as L },
  { key: "company", label: { tr: "Şirket", en: "Company" } as L },
  { key: "value", label: { tr: "Değer", en: "Value" } as L, align: "right" as const, format: "money" as const },
  { key: "stage", label: { tr: "Aşama", en: "Stage" } as L, format: "stage" as const },
  { key: "owner", label: { tr: "Sahip", en: "Owner" } as L, format: "owner" as const },
  { key: "closeDate", label: { tr: "Kapanış", en: "Close date" } as L, format: "date" as const },
];

export interface Contact {
  id: string;
  name: string;
  title: string;
  company: string;
  email: string;
  phone: string;
  openDeals: number;
  initials: string;
  color: string;
}

export const contacts: Contact[] = [
  // — KLINIK / SAĞLIK
  { id: "p1", name: "Dr. Ahmet Yılmaz", title: "Başhekim", company: "İstanbul Dental Group", email: "ahmet@istanbuldental.com", phone: "0532 111 2233", openDeals: 1, initials: "AY", color: "var(--seg-1)" },
  { id: "p6", name: "Op. Dr. Mehmet Demir", title: "Kurucu", company: "Bursa Özel Sağlık", email: "mehmet@bursaozelsaglik.com", phone: "0533 444 5566", openDeals: 1, initials: "MD", color: "var(--seg-2)" },
  { id: "p7", name: "Dt. Zeynep Kaya", title: "Klinik Sahibi", company: "Adana Diş Kliniği", email: "zeynep@adanadisklinigi.com", phone: "0544 777 8899", openDeals: 1, initials: "ZK", color: "var(--seg-3)" },
  // — EMLAK / GAYRİMENKUL
  { id: "p2", name: "Ali Koçak", title: "Genel Müdür", company: "Marmara Emlak", email: "ali@marmaraemlak.com", phone: "0535 222 3344", openDeals: 1, initials: "AK", color: "var(--seg-4)" },
  // — HUKUK
  { id: "p3", name: "Av. Canan Şahin", title: "Ortak Avukat", company: "Ankara Hukuk", email: "canan@ankarabulvar.com", phone: "0536 555 6677", openDeals: 1, initials: "CŞ", color: "var(--seg-1)" },
  { id: "p9", name: "Av. Serkan Öztürk", title: "Büro Sahibi", company: "İzmir Avukatlık", email: "serkan@izmiravukat.com", phone: "0537 888 9900", openDeals: 1, initials: "SÖ", color: "var(--seg-2)" },
  // — TEKSTİL / MODA
  { id: "p4", name: "Fatma Aksoy", title: "Pazarlama Müdürü", company: "Ege Tekstil", email: "fatma@egetekstil.com", phone: "0538 111 2233", openDeals: 1, initials: "FA", color: "var(--seg-3)" },
  { id: "p12", name: "Mehmet Güneş", title: "CEO", company: "Gaziantep Tekstil", email: "mehmet@gazianteptekstil.com", phone: "0541 555 6677", openDeals: 1, initials: "MG", color: "var(--seg-4)" },
  // — TİCARET / SANAYİ
  { id: "p8", name: "Hasan Çelik", title: "İşletme Sahibi", company: "Trabzon Ticaret", email: "hasan@trabzonticaret.com", phone: "0540 333 4455", openDeals: 1, initials: "HÇ", color: "var(--seg-1)" },
  { id: "p11", name: "İbrahim Yıldız", title: "Yönetim Kurulu Başkanı", company: "Konya Gıda Sanayi", email: "ibrahim@konyagida.com", phone: "0539 222 3344", openDeals: 1, initials: "İY", color: "var(--seg-2)" },
  // — TURİZM
  { id: "p10", name: "Murat Arslan", title: "Dijital Pazarlama Müdürü", company: "Antalya Turizm", email: "murat@antalyaturizm.com", phone: "0542 666 7788", openDeals: 1, initials: "MA", color: "var(--seg-3)" },
  // — MODA
  { id: "p5", name: "Selin Yıldırım", title: "Kurucu", company: "Moda House", email: "selin@modahouse.com", phone: "0534 666 7788", openDeals: 1, initials: "SY", color: "var(--seg-4)" },
  // — KAZANILAN MÜŞTERİLER
  { id: "p13", name: "Mert Aydın", title: "Danışman", company: "Eskişehir Danışmanlık", email: "mert@eskisehirdanismanlik.com", phone: "0555 111 2233", openDeals: 1, initials: "MA", color: "var(--seg-1)" },
  { id: "p14", name: "Burak Şen", title: "Dijital Ajans Sahibi", company: "Samsun Dijital", email: "burak@samsundijital.com", phone: "0555 444 5566", openDeals: 1, initials: "BŞ", color: "var(--seg-2)" },
];

export const contactById = Object.fromEntries(contacts.map((c) => [c.id, c])) as Record<string, Contact>;

export type ActivityKind = "call" | "email" | "meeting" | "task";

export interface Activity {
  id: string;
  kind: ActivityKind;
  title: L;
  who: string;
  company: string;
  due: string;
  done: boolean;
}

export const activities: Activity[] = [
  { id: "ac1", kind: "call", title: { tr: "Keşif görüşmesi", en: "Discovery call" }, who: "Dr. Ahmet Yılmaz", company: "İstanbul Dental Group", due: "2026-07-16T14:00:00Z", done: false },
  { id: "ac2", kind: "email", title: { tr: "Teklifi gönder", en: "Send proposal" }, who: "Av. Canan Şahin", company: "Ankara Hukuk", due: "2026-07-16T16:30:00Z", done: false },
  { id: "ac3", kind: "meeting", title: { tr: "Demo toplantısı", en: "Demo meeting" }, who: "Op. Dr. Mehmet Demir", company: "Bursa Özel Sağlık", due: "2026-07-17T11:00:00Z", done: false },
  { id: "ac4", kind: "call", title: { tr: "Fiyat görüşmesi", en: "Price negotiation" }, who: "İbrahim Yıldız", company: "Konya Gıda Sanayi", due: "2026-07-15T09:00:00Z", done: true },
  { id: "ac5", kind: "email", title: { tr: "Sözleşme taslağı gönder", en: "Send draft contract" }, who: "Mehmet Güneş", company: "Gaziantep Tekstil", due: "2026-07-18T15:00:00Z", done: false },
  { id: "ac6", kind: "meeting", title: { tr: "Klinik CRM tanıtımı", en: "Clinic CRM demo" }, who: "Dt. Zeynep Kaya", company: "Adana Diş Kliniği", due: "2026-07-19T10:00:00Z", done: false },
  { id: "ac7", kind: "task", title: { tr: "Referans müşteri hazırla", en: "Prepare case study" }, who: "Burak Şen", company: "Samsun Dijital", due: "2026-07-20T12:00:00Z", done: false },
];

export interface DKpi {
  label: L;
  value: string;
  delta?: number;
  icon?: string;
  hint?: L;
}

const vsLast: L = { tr: "geçen aya göre", en: "vs last month" };

export const kpis: DKpi[] = [
  { label: { tr: "Pipeline değeri", en: "Pipeline value" }, value: "₺258,500", delta: 22.4, icon: "layers", hint: vsLast },
  { label: { tr: "Açık deal", en: "Open deals" }, value: "14", delta: 16.0, icon: "kanban", hint: vsLast },
  { label: { tr: "Kazanma oranı", en: "Win rate" }, value: "42%", delta: 8.0, icon: "trophy", hint: vsLast },
  { label: { tr: "Ort. deal boyutu", en: "Avg deal size" }, value: "₺18,500", delta: 5.1, icon: "dollar-sign", hint: vsLast },
];

export const summary = {
  pipelineValue: 258500,
  openDeals: 14,
  winRate: 42,
  avgDealSize: 18500,
  wonThisMonth: 13500,
  quota: 80000,
};

export interface ForecastPoint {
  label: string;
  closed: number;
  weighted: number;
}

export const forecast: ForecastPoint[] = [
  { label: "Oca", closed: 0, weighted: 0 },
  { label: "Şub", closed: 0, weighted: 0 },
  { label: "Mar", closed: 0, weighted: 0 },
  { label: "Nis", closed: 0, weighted: 0 },
  { label: "May", closed: 0, weighted: 0 },
  { label: "Haz", closed: 13500, weighted: 74500 },
  { label: "Tem", closed: 0, weighted: 138200 },
  { label: "Ağu", closed: 0, weighted: 96400 },
];

export const forecastMeta = {
  title: { tr: "Gelir tahmini", en: "Revenue forecast" } as L,
  subtitle: { tr: "Kapanan + ağırlıklı pipeline", en: "Closed + weighted pipeline" } as L,
  delta: "+22.4%",
};

export interface LeaderRow {
  repId: string;
  won: number;
  wonValue: number;
  winRate: number;
  quota: number;
}

export const leaderboard: LeaderRow[] = [
  { repId: "r1", won: 8, wonValue: 125000, winRate: 44, quota: 150000 },
  { repId: "r2", won: 6, wonValue: 98500, winRate: 39, quota: 120000 },
];

export interface PipelineDemoCard {
  id: string;
  company: string;
  value: number;
  stage: StageId;
  ownerId: string;
}

export const pipelineDemo: PipelineDemoCard[] = [
  { id: "x1", company: "İstanbul Dental", value: 15000, stage: "lead", ownerId: "r1" },
  { id: "x2", company: "Bursa Özel Sağlık", value: 24000, stage: "qualified", ownerId: "r2" },
  { id: "x3", company: "Konya Gıda", value: 42000, stage: "negotiation", ownerId: "r1" },
  { id: "x4", company: "İzmir Avukatlık", value: 21000, stage: "proposal", ownerId: "r2" },
];
