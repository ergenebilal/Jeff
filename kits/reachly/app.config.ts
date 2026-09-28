/**
 * ┌──────────────────────────────────────────────────────────────────────────┐
 * │  app.config.ts — the single source of truth for this starter.            │
 * │                                                                          │
 * │  Every user-facing string is bilingual: { tr: "...", en: "..." }.        │
 * │  The guided setup (run `/setup`, or say "bu projeyi kur") edits this      │
 * │  file plus app/globals.css and .env.local.                               │
 * └──────────────────────────────────────────────────────────────────────────┘
 */
import type { L } from "@/lib/i18n/config";

export type IconName = string;

export interface NavItem {
  label: L;
  href: string;
  icon: IconName;
  badge?: L;
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
  period?: string;
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
    /** Accent fragment shown emphasized inside the hero title. */
    heroAccent: L;
    heroSubtitle: L;
    heroCtaPrimary: L;
    heroCtaSecondary: L;
    features: Feature[];
    stats: Stat[];
    pricing: PricingTier[];
    faq: FaqItem[];
  };
  /** Flat list — used by the topbar for the current-page title lookup. */
  nav: NavItem[];
  /** Grouped list — drives the sidebar. */
  navGroups: NavGroup[];
  integrations: Integration[];
}

export const appConfig: AppConfig = {
  name: "ErgeneAI Reachly",
  tagline: { tr: "ErgeneAI soğuk e-posta erişim motoru.", en: "ErgeneAI cold email engine." },
  description: {
    tr: "Ölçekte soğuk e-posta erişimi: çok adımlı diziler, birleşik yanıt gelen kutusu ve gelen kutusu ısıtma ile teslimat. Sınırsız posta kutusu bağla, ısıt, dizi gönder ve cevapları tek panelde topla.",
    en: "Cold email outreach at scale: multi-step sequences, a unified reply inbox, and inbox warmup for deliverability. Connect unlimited mailboxes, warm them up, send sequences and catch every reply in one place.",
  },
  domain: "reachly.ergeneai.com",
  logoText: "ER",
  accentName: "sky",

  marketing: {
    badge: { tr: "Soğuk e-posta erişimi", en: "Cold email outreach" },
    heroTitle: {
      tr: "Soğuk e-posta gönder,",
      en: "Send cold email that",
    },
    heroAccent: {
      tr: "cevap al.",
      en: "actually gets replies.",
    },
    heroSubtitle: {
      tr: "Sınırsız posta kutusu bağla, otomatik ısıt, çok adımlı diziler gönder ve her cevabı birleşik bir gelen kutusunda topla — teslimat ilk günden korunur.",
      en: "Connect unlimited mailboxes, warm them up automatically, run multi-step sequences and catch every reply in one unified inbox — with deliverability protected from day one.",
    },
    heroCtaPrimary: { tr: "Ücretsiz başla", en: "Start free" },
    heroCtaSecondary: { tr: "Nasıl çalıştığını gör", en: "See how it works" },
    features: [
      { icon: "mailbox", title: { tr: "Sınırsız posta kutusu", en: "Unlimited mailboxes" }, body: { tr: "İstediğin kadar gönderen hesabı bağla; Reachly hacmi otomatik döndürür ve riski dağıtır.", en: "Connect as many sender accounts as you want; Reachly rotates volume and spreads risk automatically." } },
      { icon: "flame", title: { tr: "Yerleşik ısıtma", en: "Built-in warmup" }, body: { tr: "Her posta kutusu gerçek konuşmalarla ısınır; itibar yükselir, spam'e düşmezsin.", en: "Every mailbox warms with real conversations; reputation climbs and you stay out of spam." } },
      { icon: "list-ordered", title: { tr: "Çok adımlı diziler", en: "Multi-step sequences" }, body: { tr: "E-posta, bekleme, koşul ve dallanma adımlarını sürükle-bırak ile kur. Cevap gelince durur.", en: "Build email, wait, condition and branch steps by drag-and-drop. Stops the moment a reply lands." } },
      { icon: "inbox", title: { tr: "Birleşik gelen kutusu", en: "Unified inbox" }, body: { tr: "Tüm posta kutularından gelen cevaplar tek akışta, duygu etiketleriyle birlikte.", en: "Replies from every mailbox in one stream, auto-tagged by sentiment." } },
      { icon: "flask-conical", title: { tr: "A/Z testi", en: "A/Z testing" }, body: { tr: "Konu satırı ve gövde varyantlarını paralel dene; kazananı kanıtla, tahmin etme.", en: "Test subject and body variants in parallel; prove the winner instead of guessing." } },
      { icon: "shield-check", title: { tr: "Teslimat koruması", en: "Deliverability" }, body: { tr: "SPF/DKIM/DMARC denetimi, spam skoru ve posta kutusu sağlık göstergeleri tek bakışta.", en: "SPF/DKIM/DMARC checks, spam score and mailbox health gauges at a glance." } },
    ],
    stats: [
      { value: "∞", label: { tr: "posta kutusu", en: "mailboxes" } },
      { value: "0", label: { tr: "anahtarla demo", en: "keys to demo" } },
      { value: "1", label: { tr: "birleşik gelen kutusu", en: "unified inbox" } },
      { value: "98%", label: { tr: "teslimat oranı", en: "inbox placement" } },
    ],
    pricing: [
      { name: "Starter", price: "$0", period: "/ay", tagline: { tr: "İlk dizini test et.", en: "Test your first sequence." }, features: [{ tr: "Demo modu", en: "Demo mode" }, { tr: "1 posta kutusu", en: "1 mailbox" }, { tr: "250 lead", en: "250 leads" }, { tr: "Topluluk desteği", en: "Community support" }], cta: { tr: "Başla", en: "Get started" } },
      { name: "Growth", price: "$37", period: "/ay", tagline: { tr: "Erişimi ölçekle.", en: "Scale your outreach." }, features: [{ tr: "Sınırsız posta kutusu", en: "Unlimited mailboxes" }, { tr: "Sınırsız ısıtma", en: "Unlimited warmup" }, { tr: "25.000 aktif lead", en: "25,000 active leads" }, { tr: "Birleşik gelen kutusu + A/Z", en: "Unified inbox + A/Z" }, { tr: "Öncelikli destek", en: "Priority support" }], cta: { tr: "Ücretsiz dene", en: "Start free trial" }, featured: true },
      { name: "Scale", price: "—", tagline: { tr: "Ajanslar ve ekipler için.", en: "For agencies & teams." }, features: [{ tr: "Growth'taki her şey", en: "Everything in Growth" }, { tr: "Sınırsız lead", en: "Unlimited leads" }, { tr: "Çalışma alanları & roller", en: "Workspaces & roles" }, { tr: "Özel IP'ler", en: "Dedicated IPs" }, { tr: "Özel destek", en: "Dedicated support" }], cta: { tr: "Bize ulaş", en: "Contact sales" } },
    ],
    faq: [
      { q: { tr: "Denemek için API anahtarı gerekli mi?", en: "Do I need any API keys to try it?" }, a: { tr: "Hayır. Gerçekçi kampanyalar, cevaplar ve posta kutularıyla demo modda açılır, hemen tıklayabilirsin.", en: "No. It boots in demo mode with realistic campaigns, replies and mailboxes so you can click around immediately." } },
      { q: { tr: "Soğuk e-posta yasal mı?", en: "Is cold email legal?" }, a: { tr: "Doğru yapıldığında evet — Reachly her e-postaya abonelikten çıkma bağlantısı ekler, gönderme sınırlarını uygular ve CAN-SPAM/GDPR uyumlu kalmana yardımcı olur.", en: "Done right, yes — Reachly adds an unsubscribe link to every email, enforces sending limits, and helps you stay CAN-SPAM/GDPR compliant." } },
      { q: { tr: "Posta kutusu ısıtma nasıl çalışır?", en: "How does mailbox warmup work?" }, a: { tr: "Reachly posta kutunu bir ısıtma ağına bağlar; gerçek görünen e-postalar gönderilip cevaplanır, açılır ve spam'den çıkarılır — gönderen itibarın zamanla yükselir.", en: "Reachly enrolls your mailbox in a warmup network; human-looking emails are sent, replied to, opened and rescued from spam — so your sender reputation climbs over time." } },
      { q: { tr: "Mevcut posta kutularımı bağlayabilir miyim?", en: "Can I connect my existing mailboxes?" }, a: { tr: "Evet. Google Workspace, Microsoft 365 ve her SMTP/IMAP sağlayıcısı çalışır. İstediğin kadar bağla, hacim otomatik döner.", en: "Yes. Google Workspace, Microsoft 365 and any SMTP/IMAP provider work. Connect as many as you like; volume rotates automatically." } },
      { q: { tr: "Teknoloji nedir?", en: "What's the stack?" }, a: { tr: "Next.js 16 (App Router), React 19, Tailwind v4. Vendor kilidi yok.", en: "Next.js 16 (App Router), React 19, Tailwind v4. No vendor lock-in." } },
      { q: { tr: "Nasıl kendim yaparım?", en: "How do I make it mine?" }, a: { tr: "Klasörü Claude Code'da aç ve \"bu projeyi kur\" de (veya /setup çalıştır).", en: "Open the folder in Claude Code and say \"set up this project\" (or run /setup)." } },
      { q: { tr: "Yayına alabilir miyim?", en: "Can I deploy it?" }, a: { tr: "Evet — standart bir Next.js uygulaması. Vercel'e veya herhangi bir Node sunucusuna gönder.", en: "Yes — it's a standard Next.js app. Push to Vercel or any Node host." } },
    ],
  },

  nav: [
    { label: { tr: "Panel", en: "Dashboard" }, href: "/dashboard", icon: "layout-dashboard" },
    { label: { tr: "Kampanyalar", en: "Campaigns" }, href: "/campaigns", icon: "send", muted: true },
    { label: { tr: "Gelen kutusu", en: "Inbox" }, href: "/inbox", icon: "inbox", badge: { tr: "7", en: "7" } },
    { label: { tr: "Lead'ler", en: "Leads" }, href: "/leads", icon: "users" },
    { label: { tr: "Posta kutuları", en: "Mailboxes" }, href: "/mailboxes", icon: "mailbox", muted: true },
    { label: { tr: "Ayarlar", en: "Settings" }, href: "/settings", icon: "settings" },
  ],

  navGroups: [
    {
      label: { tr: "Erişim", en: "Outreach" },
      items: [
        { label: { tr: "Panel", en: "Dashboard" }, href: "/dashboard", icon: "layout-dashboard" },
        { label: { tr: "Kampanyalar", en: "Campaigns" }, href: "/campaigns", icon: "send", muted: true },
        { label: { tr: "Diziler", en: "Sequences" }, href: "/sequences", icon: "list-ordered", muted: true },
      ],
    },
    {
      label: { tr: "Gelen", en: "Inbound" },
      items: [
        { label: { tr: "Gelen kutusu", en: "Inbox" }, href: "/inbox", icon: "inbox", badge: { tr: "7", en: "7" } },
        { label: { tr: "Lead'ler", en: "Leads" }, href: "/leads", icon: "users" },
      ],
    },
    {
      label: { tr: "Teslimat", en: "Deliverability" },
      items: [
        { label: { tr: "Posta kutuları", en: "Mailboxes" }, href: "/mailboxes", icon: "mailbox", muted: true },
        { label: { tr: "Isıtma", en: "Warmup" }, href: "/warmup", icon: "flame", muted: true },
      ],
    },
  ],

  integrations: [
    {
      key: "ses",
      name: "Amazon SES",
      envVars: ["AWS_SES_REGION", "AWS_SES_ACCESS_KEY_ID", "AWS_SES_SECRET_ACCESS_KEY"],
      required: false,
      docsUrl: "https://docs.aws.amazon.com/ses/latest/dg/setting-up.html",
      purpose: "Email-sending infrastructure for sequences. Without it, sends are simulated in demo mode.",
    },
    {
      key: "postmark",
      name: "Postmark",
      envVars: ["POSTMARK_SERVER_TOKEN"],
      required: false,
      docsUrl: "https://postmarkapp.com/support/article/1008-what-are-the-account-and-server-api-tokens",
      purpose: "Alternative transactional sender + delivery webhooks. Optional; SES or SMTP can replace it.",
    },
    {
      key: "smtp",
      name: "SMTP / IMAP mailbox",
      envVars: ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD"],
      required: false,
      docsUrl: "https://nodemailer.com/smtp/",
      purpose: "Connect a custom Google Workspace / Microsoft 365 sender mailbox for sending and warmup.",
    },
    {
      key: "verifier",
      name: "ZeroBounce (email verification)",
      envVars: ["ZEROBOUNCE_API_KEY"],
      required: false,
      docsUrl: "https://www.zerobounce.net/docs/email-validation-api-quickstart/",
      purpose: "Verify lead emails before sending to protect deliverability. Optional; leads import without it.",
    },
    {
      key: "supabase",
      name: "Supabase",
      envVars: ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"],
      required: false,
      docsUrl: "https://supabase.com/dashboard/project/_/settings/api",
      purpose: "Database & auth. Without it, the app runs in demo mode.",
    },
  ],
};

export default appConfig;
