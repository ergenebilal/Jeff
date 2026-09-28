/**
 * ┌──────────────────────────────────────────────────────────────────────────┐
 * │  app.config.ts — the single source of truth for this starter.            │
 * │                                                                          │
 * │  Every user-facing string is bilingual: { tr: "...", en: "..." }.        │
 * │  The guided setup (run `/setup`, or say "bu projeyi kur") edits this      │
 * │  file plus app/globals.css and .env.local.                               │
 * └──────────────────────────────────────────────────────────────────────────┘
 *
 *  BRAIN — an AI knowledge base / internal answer engine. Connect your docs
 *  (Notion / Google Drive / Slack / Confluence), ask a question, get a cited
 *  answer (RAG). Inspired by getguru.com and glean.com. English brand; copy
 *  toggles TR/EN.
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

export interface Testimonial {
  quote: L;
  name: string;
  role: L;
  metric: L;
}

export interface HowStep {
  icon: IconName;
  title: L;
  body: L;
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
    heroBenefits: L[];
    features: Feature[];
    how: HowStep[];
    stats: Stat[];
    testimonials: Testimonial[];
    pricing: PricingTier[];
    faq: FaqItem[];
  };
  /** Sidebar navigation, grouped (Workspace / Management). */
  navGroups: NavGroup[];
  /** Flat nav (kept for the topbar title lookup + back-compat). */
  nav: NavItem[];
  integrations: Integration[];
}

export const appConfig: AppConfig = {
  name: "ErgeneAI Brain",
  tagline: {
    tr: "ErgeneAI'nin bilgi tabanı, bir soru uzağında.",
    en: "ErgeneAI's knowledge base, one question away.",
  },
  description: {
    tr: "Belgelerini bağla, soru sor, kaynak gösterilmiş yanıt al. Brain ekibinin dağınık bilgisini tek bir cevap motoruna dönüştürür.",
    en: "Connect your docs, ask a question and get a cited answer. Brain turns your team's scattered knowledge into one answer engine.",
  },
  domain: "brain.ergeneai.com",
  logoText: "EB",
  accentName: "indigo-violet",

  marketing: {
    badge: { tr: "Dahili cevap motoru", en: "Internal answer engine" },
    heroTitle: {
      tr: "Şirketinin bilgisi,",
      en: "Your company's knowledge,",
    },
    heroAccent: {
      tr: "bir soru uzağında.",
      en: "one question away.",
    },
    heroSubtitle: {
      tr: "Brain belgelerini Notion, Drive, Slack ve Confluence'tan indeksler. Ekibin düz dille sorar; her yanıt, gerçek kaynaklara bağlanmış alıntılarla gelir — uydurma yok.",
      en: "Brain indexes your docs from Notion, Drive, Slack and Confluence. Your team asks in plain language; every answer comes with citations linked to the real source — no hallucinations.",
    },
    heroCtaPrimary: { tr: "Ücretsiz başla", en: "Start free" },
    heroCtaSecondary: { tr: "Canlı demoyu dene", en: "Try the live demo" },
    heroBenefits: [
      { tr: "Her yanıt kaynak gösterir", en: "Every answer is cited" },
      { tr: "5 dakikada kaynaklarını bağla", en: "Connect sources in 5 minutes" },
      { tr: "Slack & tarayıcı eklentisi", en: "Slack & browser extension" },
    ],
    features: [
      { icon: "plug", title: { tr: "Kaynaklarını bağla", en: "Connect your sources" }, body: { tr: "Notion, Google Drive, Slack ve Confluence'ı tek tıkla bağla. Brain her şeyi indeksler ve güncel tutar.", en: "Wire up Notion, Google Drive, Slack and Confluence in one click. Brain indexes everything and keeps it current." } },
      { icon: "sparkles", title: { tr: "Anında cevaplar", en: "Instant answers" }, body: { tr: "Düz dille sor, saniyeler içinde sentezlenmiş bir yanıt al. Arama sonuçlarını taramak yok.", en: "Ask in plain language and get a synthesized answer in seconds. No more scanning ten search results." } },
      { icon: "quote", title: { tr: "Her yanıtta alıntı", en: "Citations on everything" }, body: { tr: "Her cümle, kaynak belgeye bağlanır. Cevabın nereden geldiğini tek tıkla doğrula.", en: "Every claim links back to the source doc. Verify where an answer came from with one click." } },
      { icon: "shield-check", title: { tr: "Doğrulama & güven", en: "Verification & trust" }, body: { tr: "Uzmanlar kartları doğrular; eskiyen içerik otomatik işaretlenir. Bilgin her zaman taze.", en: "Experts verify cards; stale content gets flagged automatically. Your knowledge stays trustworthy." } },
      { icon: "panels-top-left", title: { tr: "Slack & tarayıcı eklentisi", en: "Slack & browser extension" }, body: { tr: "Brain'e Slack'ten ya da herhangi bir sekmeden sor. Cevaplar bağlamını terk etmeden gelir.", en: "Ask Brain from Slack or any browser tab. Answers come to you without leaving your context." } },
      { icon: "chart-no-axes-column", title: { tr: "Analitik & boşluklar", en: "Analytics & gaps" }, body: { tr: "Neyin sorulduğunu, neyin eksik olduğunu gör. Bilgi boşluklarını fırsata çevir.", en: "See what's asked and what's missing. Turn knowledge gaps into cards before they cost you." } },
    ],
    how: [
      { icon: "plug", title: { tr: "Belgeleri bağla", en: "Connect docs" }, body: { tr: "Kaynaklarını yetkilendir; Brain güvenli şekilde indeksler ve izinlere saygı duyar.", en: "Authorize your sources; Brain indexes securely and respects permissions." } },
      { icon: "search", title: { tr: "Bir soru sor", en: "Ask a question" }, body: { tr: "Web, Slack ya da tarayıcı eklentisinden düz dille sor.", en: "Ask in plain language from the web, Slack, or the browser extension." } },
      { icon: "sparkles", title: { tr: "Kaynaklı cevap al", en: "Get a cited answer" }, body: { tr: "Brain doğru pasajları bulur, sentezler ve kaynak gösterir.", en: "Brain retrieves the right passages, synthesizes, and cites them." } },
      { icon: "refresh-cw", title: { tr: "Taze tut", en: "Keep it fresh" }, body: { tr: "Uzmanlar doğrular, eskiyenler işaretlenir, boşluklar kapatılır.", en: "Experts verify, stale docs get flagged, and gaps get closed." } },
    ],
    stats: [
      { value: "5×", label: { tr: "daha hızlı cevap", en: "faster answers" } },
      { value: "73%", label: { tr: "destek yönlendirme", en: "support deflection" } },
      { value: "6", label: { tr: "kaynak konnektörü", en: "source connectors" } },
      { value: "100%", label: { tr: "kaynaklı yanıt", en: "cited answers" } },
    ],
    testimonials: [
      { quote: { tr: "İlk hafta Slack'teki “bu nerede?” mesajları yarıya düştü.", en: "“Where is this?” messages in Slack halved in the first week." }, name: "Maria Gomez", role: { tr: "Operasyon Lideri, Northwind", en: "Head of Ops, Northwind" }, metric: { tr: "Slack gürültüsü -48%", en: "−48% Slack noise" } },
      { quote: { tr: "Yeni başlayanlar artık bana değil Brain'e soruyor — ve doğru cevabı alıyor.", en: "New hires ask Brain instead of me now — and get the right answer." }, name: "Dana Ortiz", role: { tr: "İK Müdürü, Parable", en: "People Manager, Parable" }, metric: { tr: "Onboarding 2× hızlı", en: "Onboarding 2× faster" } },
      { quote: { tr: "Her cevabın kaynağı olması güven krizini çözdü. Artık bilgiye güveniyoruz.", en: "Citations on every answer ended the trust crisis. We rely on it now." }, name: "Sam Reeves", role: { tr: "Mühendislik Lideri, Formwork", en: "Eng Lead, Formwork" }, metric: { tr: "Cevaplar 5× hızlı", en: "Answers 5× faster" } },
      { quote: { tr: "Bilgi boşlukları paneli sayesinde dokümante etmediğimiz konuları gördük.", en: "The knowledge-gaps panel showed us exactly what we'd never documented." }, name: "Priya Nair", role: { tr: "Gelir Operasyonları, Cedarworks", en: "RevOps, Cedarworks" }, metric: { tr: "31 boşluk kapatıldı", en: "31 gaps closed" } },
      { quote: { tr: "Destek talebi hacmimiz çeyrekte üçte bir azaldı. Çoğu kendi kendine yanıtlanıyor.", en: "Support ticket volume dropped a third this quarter. Most self-resolve." }, name: "Tom Reilly", role: { tr: "Destek Müdürü, Lumen", en: "Support Manager, Lumen" }, metric: { tr: "Talepler -34%", en: "−34% tickets" } },
      { quote: { tr: "Tarayıcı eklentisi her sekmede yanımda. Doküman avına son.", en: "The browser extension is with me on every tab. No more doc hunts." }, name: "Aisha Khan", role: { tr: "Yazılım Mühendisi, Brightline", en: "Software Engineer, Brightline" }, metric: { tr: "Günde 40 dk kazanç", en: "40 min/day saved" } },
    ],
    pricing: [
      { name: "Starter", price: "$0", period: { tr: "/ay", en: "/mo" }, tagline: { tr: "Küçük ekipler için.", en: "For small teams." }, features: [{ tr: "3 koltuğa kadar", en: "Up to 3 seats" }, { tr: "2 kaynak konnektörü", en: "2 source connectors" }, { tr: "Ayda 200 soru", en: "200 questions/mo" }, { tr: "Web cevap motoru", en: "Web answer engine" }], cta: { tr: "Başla", en: "Get started" } },
      { name: "Team", price: "$12", period: { tr: "/koltuk/ay", en: "/seat/mo" }, tagline: { tr: "Büyüyen ekipler için.", en: "For growing teams." }, features: [{ tr: "Sınırsız koltuk", en: "Unlimited seats" }, { tr: "Tüm kaynak konnektörleri", en: "All source connectors" }, { tr: "Slack & tarayıcı eklentisi", en: "Slack & browser extension" }, { tr: "Doğrulama & analitik", en: "Verification & analytics" }, { tr: "Öncelikli destek", en: "Priority support" }], cta: { tr: "Ücretsiz dene", en: "Start free trial" }, featured: true },
      { name: "Enterprise", price: "Custom", tagline: { tr: "Kurumsal için.", en: "For the enterprise." }, features: [{ tr: "Team'deki her şey", en: "Everything in Team" }, { tr: "SSO / SCIM & roller", en: "SSO / SCIM & roles" }, { tr: "Özel veri saklama", en: "Custom data retention" }, { tr: "SLA & denetim kaydı", en: "SLA & audit log" }, { tr: "Özel hesap yöneticisi", en: "Dedicated manager" }], cta: { tr: "Satışa ulaş", en: "Contact sales" } },
    ],
    faq: [
      { q: { tr: "Hangi kaynakları bağlayabilirim?", en: "Which sources can I connect?" }, a: { tr: "Notion, Google Drive, Slack, Confluence, GitHub ve genel web. Yeni konnektörler düzenli ekleniyor.", en: "Notion, Google Drive, Slack, Confluence, GitHub and the public web. New connectors land regularly." } },
      { q: { tr: "Cevaplar uydurma olur mu?", en: "Will answers hallucinate?" }, a: { tr: "Brain yalnızca indekslenmiş belgelerden cevap üretir ve her iddiayı kaynağa bağlar. Kaynak yoksa, “bilmiyorum” der.", en: "Brain only answers from your indexed docs and links every claim to a source. If there's no source, it says it doesn't know." } },
      { q: { tr: "İzinlere saygı duyar mı?", en: "Does it respect permissions?" }, a: { tr: "Evet. Kaynak sistemindeki izinler korunur; kimse erişimi olmayan bir belgeden cevap alamaz.", en: "Yes. Source-system permissions are preserved; nobody gets an answer from a doc they can't access." } },
      { q: { tr: "Bilginin tazeliğini nasıl korur?", en: "How does it keep knowledge fresh?" }, a: { tr: "Kaynaklar sürekli yeniden indekslenir, eskiyen kartlar işaretlenir ve uzmanlar doğrulama kuyruğunda inceler.", en: "Sources re-index continuously, stale cards get flagged, and experts review them in a verification queue." } },
      { q: { tr: "Slack'ten kullanabilir miyim?", en: "Can I use it from Slack?" }, a: { tr: "Evet. Slack uygulaması ve tarayıcı eklentisiyle bağlamını terk etmeden sorabilirsin.", en: "Yes. The Slack app and browser extension let you ask without leaving your context." } },
      { q: { tr: "Denemek için anahtar gerekli mi?", en: "Do I need keys to try it?" }, a: { tr: "Hayır. Gerçekçi örnek belgeler ve sorularla demo modda açılır — hemen tıklayabilirsin.", en: "No. It boots in demo mode with realistic sample docs and questions — click around immediately." } },
      { q: { tr: "Teknoloji nedir?", en: "What's the stack?" }, a: { tr: "Next.js 16, React 19, Tailwind v4. Bir LLM/embeddings sağlayıcısı, pgvector ve kaynak konnektörleriyle bağlanır.", en: "Next.js 16, React 19, Tailwind v4. Wires to an LLM/embeddings provider, pgvector and source connectors." } },
      { q: { tr: "Yayına alabilir miyim?", en: "Can I deploy it?" }, a: { tr: "Evet — standart bir Next.js uygulaması. Vercel'e veya herhangi bir Node sunucusuna gönder.", en: "Yes — it's a standard Next.js app. Push to Vercel or any Node host." } },
    ],
  },

  navGroups: [
    {
      label: { tr: "Çalışma alanı", en: "Workspace" },
      items: [
        { label: { tr: "Panel", en: "Dashboard" }, href: "/dashboard", icon: "layout-dashboard" },
        { label: { tr: "Kaynaklar", en: "Sources" }, href: "/sources", icon: "files" },
        { label: { tr: "Sorular", en: "Questions" }, href: "/questions", icon: "messages-square" },
        { label: { tr: "Boşluklar", en: "Gaps" }, href: "/gaps", icon: "search-x", badge: { tr: "Yakında", en: "Soon" }, muted: true },
      ],
    },
    {
      label: { tr: "Yönetim", en: "Management" },
      items: [
        { label: { tr: "Doğrulama", en: "Verification" }, href: "/verification", icon: "shield-check", muted: true },
        { label: { tr: "Ekip", en: "Team" }, href: "/team", icon: "users", muted: true },
        { label: { tr: "Analitik", en: "Analytics" }, href: "/analytics", icon: "chart-no-axes-column", muted: true },
        { label: { tr: "Entegrasyonlar", en: "Integrations" }, href: "/settings", icon: "plug" },
      ],
    },
  ],

  nav: [
    { label: { tr: "Panel", en: "Dashboard" }, href: "/dashboard", icon: "layout-dashboard" },
    { label: { tr: "Kaynaklar", en: "Sources" }, href: "/sources", icon: "files" },
    { label: { tr: "Sorular", en: "Questions" }, href: "/questions", icon: "messages-square" },
    { label: { tr: "Ayarlar", en: "Settings" }, href: "/settings", icon: "settings" },
  ],

  integrations: [
    {
      key: "openai",
      name: "LLM & Embeddings",
      envVars: ["OPENAI_API_KEY"],
      required: false,
      docsUrl: "https://platform.openai.com/api-keys",
      purpose: "Generates cited answers and embeds documents for retrieval. Swap for Anthropic, Mistral, or any provider. Without it, answers are demo data.",
    },
    {
      key: "supabase",
      name: "Supabase (pgvector)",
      envVars: ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"],
      required: false,
      docsUrl: "https://supabase.com/docs/guides/ai/vector-columns",
      purpose: "Vector store for embeddings + database & auth. Without it, the app runs in demo mode.",
    },
    {
      key: "notion",
      name: "Notion",
      envVars: ["NOTION_API_KEY"],
      required: false,
      docsUrl: "https://developers.notion.com/docs/create-a-notion-integration",
      purpose: "Indexes Notion pages and databases as knowledge cards.",
    },
    {
      key: "google_drive",
      name: "Google Drive",
      envVars: ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
      required: false,
      docsUrl: "https://developers.google.com/drive/api/guides/about-sdk",
      purpose: "Indexes Docs, Sheets and Slides from connected Drive folders.",
    },
    {
      key: "slack",
      name: "Slack",
      envVars: ["SLACK_BOT_TOKEN", "SLACK_SIGNING_SECRET"],
      required: false,
      docsUrl: "https://api.slack.com/apps",
      purpose: "Indexes channel knowledge and answers questions in Slack.",
    },
  ],
};

export default appConfig;
