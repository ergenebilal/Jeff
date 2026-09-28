/**
 * ┌──────────────────────────────────────────────────────────────────────────┐
 * │  app.config.ts — the single source of truth for this starter.            │
 * │                                                                          │
 * │  Every user-facing string is bilingual: { tr: "...", en: "..." }.        │
 * │  The guided setup (run `/setup`, or say "bu projeyi kur") edits this      │
 * │  file plus app/globals.css and .env.local.                               │
 * └──────────────────────────────────────────────────────────────────────────┘
 *
 *  PIPELY — a sales CRM with a visual deal pipeline (contacts, deals,
 *  activities, forecasting). Modeled on real, profitable products (Pipedrive,
 *  HubSpot CRM). English brand; copy toggles TR/EN.
 */
import type { L } from "@/lib/i18n/config";

export type IconName = string;

export interface NavItem {
  label: L;
  href: string;
  icon: IconName;
  /** Optional "Soon" / "Beta" style badge shown muted in the sidebar. */
  badge?: L;
  /** Render as disabled/muted (e.g. a not-yet-shipped section). */
  muted?: boolean;
}

export interface NavGroup {
  label: L;
  items: NavItem[];
}

export interface Feature {
  icon: IconName;
  title: L;
  body: L;
}

export interface Stat {
  value: string;
  label: L;
}

export interface PricingTier {
  name: string;
  price: string;
  period?: L;
  tagline: L;
  features: L[];
  cta: L;
  featured?: boolean;
}

export interface FaqItem {
  q: L;
  a: L;
}

export interface Integration {
  key: string;
  name: string;
  envVars: string[];
  required: boolean;
  docsUrl: string;
  purpose: string;
}

export interface AppConfig {
  name: string;
  tagline: L;
  description: L;
  domain: string;
  logoText: string;
  accentName: string;
  marketing: {
    badge: L;
    heroTitle: L;
    heroAccent: L;
    heroSubtitle: L;
    heroCtaPrimary: L;
    heroCtaSecondary: L;
    features: Feature[];
    stats: Stat[];
    pricing: PricingTier[];
    faq: FaqItem[];
  };
  /** Sidebar navigation, grouped (Sell / Manage). */
  navGroups: NavGroup[];
  /** Flat nav (kept for the topbar title lookup + back-compat). */
  nav: NavItem[];
  integrations: Integration[];
}

export const appConfig: AppConfig = {
  name: "ErgeneAI Pipely",
  tagline: {
    tr: "ErgeneAI satış pipeline'ı.",
    en: "ErgeneAI sales pipeline.",
  },
  description: {
    tr: "Görsel deal pipeline, kişiler, aktiviteler ve tahminleme ile bir satış CRM'i. Anlaşmaları sürükle-bırak ile aşamalar arasında taşı.",
    en: "A sales CRM with a visual deal pipeline, contacts, activities and forecasting. Drag deals across stages, track every touchpoint.",
  },
  domain: "pipely.ergeneai.com",
  logoText: "EP",
  accentName: "sales green",

  marketing: {
    badge: { tr: "Satış CRM & pipeline", en: "Sales CRM & pipeline" },
    heroTitle: {
      tr: "Satış ekibinin gerçekten",
      en: "A pipeline your sales team",
    },
    heroAccent: {
      tr: "güncelleyeceği bir pipeline.",
      en: "will actually update.",
    },
    heroSubtitle: {
      tr: "Pipely deal'lerini görsel bir panoda toplar, her aramayı ve e-postayı kaydeder ve geliri otomatik öngörür. Temsilciler tahtayı günceller çünkü güncellemek kolaydır — sen de tahmini her zaman doğru bulursun.",
      en: "Pipely puts your deals on a visual board, logs every call and email, and forecasts revenue automatically. Reps keep the board current because it's effortless — and you get a forecast you can trust.",
    },
    heroCtaPrimary: { tr: "Ücretsiz başla", en: "Start free" },
    heroCtaSecondary: { tr: "Canlı demoyu gör", en: "See the live demo" },
    features: [
      { icon: "kanban", title: { tr: "Görsel pipeline", en: "Visual pipeline" }, body: { tr: "Deal'leri sürükle-bırak ile aşamalar arasında taşı. Her aşamadaki değeri, gün sayısını ve sahibi tek bakışta gör.", en: "Drag deals across stages on a kanban board. See value, days-in-stage and owner per column at a glance." } },
      { icon: "users", title: { tr: "Kişi yönetimi", en: "Contact management" }, body: { tr: "Kişiler ve şirketler tek yerde. Her deal, her aktivite ve her not ilgili kişiye bağlanır.", en: "People and companies in one place. Every deal, activity and note ties back to the right contact." } },
      { icon: "phone-call", title: { tr: "Aktivite takibi", en: "Activity tracking" }, body: { tr: "Aramalar, e-postalar ve toplantılar otomatik kaydedilir. Vadesi gelen görevler asla kaçmaz.", en: "Calls, emails and meetings are logged automatically. Due tasks never slip through the cracks." } },
      { icon: "mail", title: { tr: "E-posta & takvim senkronu", en: "Email & calendar sync" }, body: { tr: "Gmail veya Outlook'u bağla; gelen kutun ve takvimin deal'lerine otomatik bağlanır.", en: "Connect Gmail or Outlook; your inbox and calendar link to deals automatically." } },
      { icon: "trending-up", title: { tr: "Gelir tahmini", en: "Forecasting" }, body: { tr: "Olasılığa göre ağırlıklandırılmış pipeline ile ay ay geliri öngör. Kotaya ne kadar yakınsın, hep bil.", en: "Forecast revenue month by month with a probability-weighted pipeline. Always know how close you are to quota." } },
      { icon: "workflow", title: { tr: "Otomasyon", en: "Automation" }, body: { tr: "Deal aşama değiştirince görev oluştur, e-posta gönder veya Slack'e bildir — kural sen koyarsın.", en: "When a deal changes stage, create a task, send an email or ping Slack — rules you define." } },
    ],
    stats: [
      { value: "+20%", label: { tr: "kazanma oranı", en: "win rate" } },
      { value: "5", label: { tr: "pipeline aşaması", en: "pipeline stages" } },
      { value: "8h", label: { tr: "haftada kazanılan", en: "saved per rep/wk" } },
      { value: "100%", label: { tr: "güncel tahmin", en: "forecast accuracy" } },
    ],
    pricing: [
      { name: "Starter", price: "$0", period: { tr: "/kullanıcı/ay", en: "/user/mo" }, tagline: { tr: "Tek kişilik satış için.", en: "For solo sellers." }, features: [{ tr: "3 kullanıcıya kadar", en: "Up to 3 users" }, { tr: "Görsel pipeline & kişiler", en: "Visual pipeline & contacts" }, { tr: "Aktivite kaydı", en: "Activity logging" }, { tr: "1 pipeline", en: "1 pipeline" }], cta: { tr: "Başla", en: "Get started" } },
      { name: "Growth", price: "$29", period: { tr: "/kullanıcı/ay", en: "/user/mo" }, tagline: { tr: "Büyüyen ekipler için.", en: "For growing teams." }, features: [{ tr: "Sınırsız kullanıcı", en: "Unlimited users" }, { tr: "E-posta & takvim senkronu", en: "Email & calendar sync" }, { tr: "Gelir tahmini & raporlar", en: "Forecasting & reports" }, { tr: "Otomasyon kuralları", en: "Automation rules" }, { tr: "Öncelikli destek", en: "Priority support" }], cta: { tr: "Ücretsiz dene", en: "Start free trial" }, featured: true },
      { name: "Scale", price: "Custom", tagline: { tr: "Kurumsal satış için.", en: "For enterprise sales." }, features: [{ tr: "Growth'taki her şey", en: "Everything in Growth" }, { tr: "Çoklu pipeline & roller", en: "Multiple pipelines & roles" }, { tr: "Lead zenginleştirme", en: "Lead enrichment" }, { tr: "SSO & denetim kaydı", en: "SSO & audit log" }, { tr: "Özel hesap yöneticisi", en: "Dedicated manager" }], cta: { tr: "Satışa ulaş", en: "Contact sales" } },
    ],
    faq: [
      { q: { tr: "Pipely'yi denemek için kart gerekli mi?", en: "Do I need a card to try Pipely?" }, a: { tr: "Hayır. Gerçekçi örnek deal'ler, kişiler ve aktivitelerle demo modda açılır — hemen tıklayabilirsin.", en: "No. It boots in demo mode with realistic sample deals, contacts and activities — click around immediately." } },
      { q: { tr: "Deal'leri nasıl taşırım?", en: "How do I move deals?" }, a: { tr: "Pipeline'da deal kartını tutup hedef aşamaya sürükle. Pipeline değeri ve kazanma oranı anında güncellenir.", en: "On the pipeline, grab a deal card and drag it to the target stage. Pipeline value and win rate update instantly." } },
      { q: { tr: "E-posta ve takvimimi bağlayabilir miyim?", en: "Can I sync my email and calendar?" }, a: { tr: "Evet. Gmail veya Outlook'u bağla; gelen kutun, gönderdiklerin ve toplantıların ilgili deal'lere otomatik bağlanır.", en: "Yes. Connect Gmail or Outlook; your inbox, sent mail and meetings link to the right deals automatically." } },
      { q: { tr: "Gelir tahmini nasıl çalışıyor?", en: "How does forecasting work?" }, a: { tr: "Her aşamanın bir kazanma olasılığı var. Pipely açık deal'leri bu olasılıkla ağırlıklandırır ve kapanış tarihine göre ay ay toplar.", en: "Each stage has a win probability. Pipely weights open deals by it and rolls them up by close date, month by month." } },
      { q: { tr: "Lead'leri zenginleştirebilir miyim?", en: "Can I enrich leads?" }, a: { tr: "Bir zenginleştirme API'si (Clearbit/Apollo) bağlayınca; yeni kişiler için şirket, unvan ve sosyal veriler otomatik doldurulur.", en: "Wire an enrichment API (Clearbit/Apollo) and new contacts get company, title and social data filled in automatically." } },
      { q: { tr: "Teknoloji nedir?", en: "What's the stack?" }, a: { tr: "Next.js 16, React 19, Tailwind v4. Supabase + e-posta/takvim senkronu + zenginleştirme + Slack ile bağlanır.", en: "Next.js 16, React 19, Tailwind v4. Wires to Supabase + email/calendar sync + enrichment + Slack." } },
      { q: { tr: "Pipedrive'dan veri taşıyabilir miyim?", en: "Can I import from Pipedrive?" }, a: { tr: "Demo şablonu Pipedrive/HubSpot alanlarını taklit eder, böylece CSV içe aktarımı düz eşleşir. İçe aktarma kurulumdan sonra açılır.", en: "The demo schema mirrors Pipedrive/HubSpot fields, so a CSV import maps cleanly. Import unlocks after setup." } },
      { q: { tr: "Yayına alabilir miyim?", en: "Can I deploy it?" }, a: { tr: "Evet — standart bir Next.js uygulaması. Vercel'e veya herhangi bir Node sunucusuna gönder.", en: "Yes — it's a standard Next.js app. Push to Vercel or any Node host." } },
    ],
  },

  navGroups: [
    {
      label: { tr: "Sat", en: "Sell" },
      items: [
        { label: { tr: "Panel", en: "Dashboard" }, href: "/dashboard", icon: "layout-dashboard" },
        { label: { tr: "Pipeline", en: "Pipeline" }, href: "/deals", icon: "kanban" },
        { label: { tr: "Kişiler", en: "Contacts" }, href: "/contacts", icon: "users" },
        { label: { tr: "Aktiviteler", en: "Activities" }, href: "/activities", icon: "phone-call", muted: true },
        { label: { tr: "E-postalar", en: "Inbox" }, href: "/inbox", icon: "mail", badge: { tr: "Yakında", en: "Soon" }, muted: true },
      ],
    },
    {
      label: { tr: "Yönet", en: "Manage" },
      items: [
        { label: { tr: "Tahmin", en: "Forecast" }, href: "/forecast", icon: "trending-up", muted: true },
        { label: { tr: "Raporlar", en: "Reports" }, href: "/reports", icon: "chart-no-axes-column", muted: true },
        { label: { tr: "Ekip", en: "Team" }, href: "/team", icon: "user-round-cog", muted: true },
        { label: { tr: "Entegrasyonlar", en: "Integrations" }, href: "/settings", icon: "plug" },
      ],
    },
  ],

  nav: [
    { label: { tr: "Panel", en: "Dashboard" }, href: "/dashboard", icon: "layout-dashboard" },
    { label: { tr: "Pipeline", en: "Pipeline" }, href: "/deals", icon: "kanban" },
    { label: { tr: "Kişiler", en: "Contacts" }, href: "/contacts", icon: "users" },
    { label: { tr: "Ayarlar", en: "Settings" }, href: "/settings", icon: "settings" },
  ],

  integrations: [
    {
      key: "supabase",
      name: "Supabase",
      envVars: ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"],
      required: false,
      docsUrl: "https://supabase.com/dashboard/project/_/settings/api",
      purpose: "Database & auth. Stores deals, contacts and activities. Without it, the app runs in demo mode.",
    },
    {
      key: "google",
      name: "Google Workspace (Gmail + Calendar)",
      envVars: ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
      required: false,
      docsUrl: "https://console.cloud.google.com/apis/credentials",
      purpose: "Email & calendar sync — link inbox threads and meetings to deals (Outlook works the same way).",
    },
    {
      key: "clearbit",
      name: "Clearbit (enrichment)",
      envVars: ["CLEARBIT_API_KEY"],
      required: false,
      docsUrl: "https://dashboard.clearbit.com/api",
      purpose: "Auto-fill company, title and social data for new contacts from their email domain.",
    },
    {
      key: "slack",
      name: "Slack",
      envVars: ["SLACK_WEBHOOK_URL"],
      required: false,
      docsUrl: "https://api.slack.com/messaging/webhooks",
      purpose: "Notify a channel when a deal is won or moves stage. Without it, automations stay in-app only.",
    },
  ],
};

export default appConfig;
