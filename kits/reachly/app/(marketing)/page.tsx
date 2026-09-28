"use client";

import Link from "next/link";
import {
  ArrowRight,
  Check,
  Minus,
  Plus,
  Quote,
  Star,
  ShieldCheck,
  Zap,
  Mail,
  Reply as ReplyIcon,
  Flame,
  Inbox,
  Send,
  Clock,
  GitBranch,
  Upload,
} from "lucide-react";
import appConfig from "@/app.config";
import { Icon } from "@/components/ui/icon";
import { FlowDemo } from "@/components/marketing/flow-demo";
import { ProductPreview, CompanyMark, IntegrationGlyph } from "@/components/marketing/marks";
import { useLang } from "@/components/i18n/language-provider";
import { cn } from "@/lib/utils";
import type { L } from "@/lib/i18n/config";

/* ─────────────────────────────────────────────────────────────────────────────
   Reachly landing page — a clean, light SaaS marketing surface that MATCHES the
   dashboard's sky/cyan identity (Onest + JetBrains Mono, hairline borders, soft
   shadows, --grad-hero wash). Every visible string is bilingual { tr, en } and
   resolved through the active language via tt(). No photos — inline SVG/CSS only.

   Acts, in order:
     nav (in layout.tsx) · hero · trusted-by · interactive flow demo · features
     grid · how-it-works · deliverability deep-dive · comparison table ·
     testimonials · pricing · FAQ · final CTA · footer (in layout.tsx)
   ───────────────────────────────────────────────────────────────────────────── */

/* Hero — three green-check benefits. */
const HERO_BENEFITS: L[] = [
  { tr: "Sınırsız posta kutusu bağla — hacim otomatik döner", en: "Connect unlimited mailboxes — volume rotates automatically" },
  { tr: "Her posta kutusu yerleşik ısıtmayla spam'den uzak durur", en: "Every mailbox stays out of spam with built-in warmup" },
  { tr: "Tüm cevaplar tek birleşik gelen kutusunda, etiketli", en: "Every reply in one unified inbox, auto-tagged" },
];

/* Trusted-by — the same fake companies the demo data uses. */
const TRUSTED = ["Northwind", "Parable", "Formwork", "Cedarworks", "Lumen", "Harvest", "Brightline", "Meridian"];

/* Four headline stats reused from app.config marketing.stats, but with landing tone. */
const BIG_STATS: { value: string; label: L }[] = [
  { value: "48.2k", label: { tr: "haftalık gönderim", en: "weekly sends" } },
  { value: "61.8%", label: { tr: "ortalama açılma", en: "avg open rate" } },
  { value: "8.4%", label: { tr: "ortalama cevap", en: "avg reply rate" } },
  { value: "98%", label: { tr: "gelen kutusu oranı", en: "inbox placement" } },
];

/* How-it-works — four steps from import → warmup → sequence → reply. */
const HOW_STEPS: { n: string; icon: string; title: L; body: L }[] = [
  {
    n: "01",
    icon: "upload",
    title: { tr: "Lead'leri içe aktar", en: "Import your leads" },
    body: { tr: "CSV yükle ya da CRM'ini bağla. Reachly e-postaları doğrular, kopyaları temizler ve riskli adresleri ayıklar.", en: "Upload a CSV or connect your CRM. Reachly verifies emails, dedupes and filters risky addresses." },
  },
  {
    n: "02",
    icon: "flame",
    title: { tr: "Posta kutularını ısıt", en: "Warm up mailboxes" },
    body: { tr: "Gönderen hesaplarını ısıtma ağına ekle. İtibar günler içinde yükselir, gönderim sınırın güvenle artar.", en: "Enroll sender accounts in the warmup network. Reputation climbs in days and your sending limit grows safely." },
  },
  {
    n: "03",
    icon: "list-ordered",
    title: { tr: "Diziyi gönder", en: "Send the sequence" },
    body: { tr: "E-posta, bekleme ve koşul adımlarını kur. Reachly hacmi posta kutuların arasında döndürür, cevap gelince durur.", en: "Build email, wait and condition steps. Reachly rotates volume across mailboxes and stops the moment a reply lands." },
  },
  {
    n: "04",
    icon: "inbox",
    title: { tr: "Cevapları yakala", en: "Catch every reply" },
    body: { tr: "Tüm posta kutularından gelen yanıtlar tek akışta birleşir, duyguya göre etiketlenir — hiçbiri kaçmaz.", en: "Replies from every mailbox merge into one stream, tagged by sentiment — nothing slips through." },
  },
];

/* Deliverability deep-dive — alternating blocks, each with a small inline panel. */
const DEEP_DIVE: { eyebrow: L; title: L; body: L; points: L[]; reverse?: boolean }[] = [
  {
    eyebrow: { tr: "Isıtma", en: "Warmup" },
    title: { tr: "İtibarın otomatik yükselsin", en: "Reputation that climbs on autopilot" },
    body: { tr: "Her posta kutusu gerçek görünen konuşmalara katılır: e-postalar gönderilir, açılır, cevaplanır ve spam'den kurtarılır. Sen gönderirken Reachly itibarını korur.", en: "Each mailbox joins human-looking conversations: emails are sent, opened, replied to and rescued from spam. Reachly protects reputation while you send." },
    points: [
      { tr: "Günlük ısıtma hacmi otomatik artar", en: "Daily warmup volume ramps automatically" },
      { tr: "Spam'e düşenler kurtarılıp işaretlenir", en: "Spam-trapped emails are rescued and flagged" },
      { tr: "Posta kutusu sağlık göstergesi (0–100)", en: "Mailbox health gauge (0–100)" },
    ],
  },
  {
    eyebrow: { tr: "Kimlik doğrulama", en: "Authentication" },
    title: { tr: "SPF, DKIM ve DMARC tek bakışta", en: "SPF, DKIM and DMARC at a glance" },
    body: { tr: "Reachly her gönderen alan adını tarar ve kurulum eksiklerini gösterir. Yeşil onaylar gelen kutusuna düşmenin temelini kurar.", en: "Reachly scans every sender domain and surfaces setup gaps. Green checks build the foundation for landing in the inbox." },
    points: [
      { tr: "SPF / DKIM / DMARC denetimi", en: "SPF / DKIM / DMARC checks" },
      { tr: "Kara liste taraması ve uyarılar", en: "Blacklist scan and alerts" },
      { tr: "Özel takip alanı önerisi", en: "Custom tracking domain guidance" },
    ],
    reverse: true,
  },
  {
    eyebrow: { tr: "Hacim kontrolü", en: "Volume control" },
    title: { tr: "Sınırları aşmadan ölçekle", en: "Scale without tripping limits" },
    body: { tr: "Reachly günlük gönderim sınırlarını uygular, hacmi posta kutuların arasında döndürür ve spam skorunu izler — büyürken bile teslimat korunur.", en: "Reachly enforces daily sending caps, rotates volume across mailboxes and watches your spam score — deliverability holds even as you scale." },
    points: [
      { tr: "Posta kutusu başına günlük sınır", en: "Per-mailbox daily caps" },
      { tr: "Akıllı hacim dağıtımı", en: "Smart volume distribution" },
      { tr: "Gerçek-zamanlı spam skoru", en: "Real-time spam score" },
    ],
  },
];

/* Comparison table — Mailchimp/manual vs generic vs Reachly. */
type CompareValue = boolean | L | string;
const COMPARE: { feature: L; manual: CompareValue; generic: CompareValue; reachly: CompareValue }[] = [
  { feature: { tr: "Sınırsız posta kutusu", en: "Unlimited mailboxes" }, manual: false, generic: { tr: "Ek ücretli", en: "Paid add-on" }, reachly: true },
  { feature: { tr: "Yerleşik ısıtma", en: "Built-in warmup" }, manual: false, generic: false, reachly: true },
  { feature: { tr: "Çok adımlı diziler", en: "Multi-step sequences" }, manual: { tr: "Manuel", en: "Manual" }, generic: true, reachly: true },
  { feature: { tr: "Birleşik cevap kutusu", en: "Unified reply inbox" }, manual: false, generic: { tr: "Kısmi", en: "Partial" }, reachly: true },
  { feature: { tr: "Teslimat denetimi", en: "Deliverability checks" }, manual: false, generic: { tr: "Sınırlı", en: "Limited" }, reachly: true },
  { feature: { tr: "A/Z testi", en: "A/Z testing" }, manual: false, generic: true, reachly: true },
  { feature: { tr: "Anahtarsız demo", en: "Keyless demo" }, manual: { tr: "—", en: "—" }, generic: false, reachly: true },
  { feature: { tr: "Kişi başı fiyat", en: "Per-contact pricing" }, manual: { tr: "—", en: "—" }, generic: { tr: "Var", en: "Yes" }, reachly: { tr: "Yok", en: "None" } },
];

/* Testimonials — avatars are SVG initials (rendered with grad-brand), each with a metric. */
const TESTIMONIALS: { quote: L; name: string; role: L; initials: string; metric: L }[] = [
  { quote: { tr: "İlk haftada cevap oranımız %3'ten %9'a çıktı. Isıtma gerçekten işe yarıyor.", en: "Our reply rate went from 3% to 9% in the first week. The warmup actually works." }, name: "Maria Gomez", role: { tr: "Kurucu · Northwind", en: "Founder · Northwind" }, initials: "MG", metric: { tr: "%3 → %9 cevap", en: "3% → 9% reply" } },
  { quote: { tr: "Sekiz posta kutusunu bir öğleden sonrada bağladık. Tüm cevaplar artık tek gelen kutusunda.", en: "Wired up eight mailboxes in an afternoon. Every reply now lands in one inbox." }, name: "Liam Chen", role: { tr: "CEO · Parable", en: "CEO · Parable" }, initials: "LC", metric: { tr: "8 posta kutusu", en: "8 mailboxes" } },
  { quote: { tr: "Spam klasörüne düşmeyi tamamen bıraktık. Teslimat paneli her sabah ilk baktığım yer.", en: "We stopped hitting spam entirely. The deliverability panel is the first thing I check each morning." }, name: "Nadia Park", role: { tr: "Büyüme · Formwork", en: "Growth · Formwork" }, initials: "NP", metric: { tr: "%98 gelen kutusu", en: "98% inbox" } },
  { quote: { tr: "A/Z testi tahmin etmeyi bıraktırdı. Kazanan konu satırını veriyle kanıtladık.", en: "A/Z testing ended the guesswork. We proved the winning subject line with data." }, name: "Aisha Khan", role: { tr: "Pazarlama · Lumen", en: "Marketing · Lumen" }, initials: "AK", metric: { tr: "+%41 açılma", en: "+41% opens" } },
  { quote: { tr: "Ajans olarak her müşteriye ayrı çalışma alanı açıyoruz. Ölçeklenmesi çok rahat.", en: "As an agency we spin up a workspace per client. It scales effortlessly." }, name: "Diego Santos", role: { tr: "Operasyon · Harvest", en: "Ops · Harvest" }, initials: "DS", metric: { tr: "12 çalışma alanı", en: "12 workspaces" } },
  { quote: { tr: "Anahtarsız demo modu satışı kapattı. Ekibe gösterip aynı gün geçtik.", en: "The keyless demo mode closed the deal. Showed the team and we switched same day." }, name: "Owen Mills", role: { tr: "Kurucu · Meridian", en: "Founder · Meridian" }, initials: "OM", metric: { tr: "Aynı gün kurulum", en: "Same-day setup" } },
];

/* Three small trust cards under the testimonials band. */
const TRUST_POINTS: { icon: typeof ShieldCheck; title: L; body: L }[] = [
  { icon: ShieldCheck, title: { tr: "Uyumlu gönderim", en: "Compliant sending" }, body: { tr: "Her e-postaya abonelikten çıkma bağlantısı; CAN-SPAM ve GDPR dostu.", en: "Unsubscribe link on every email; CAN-SPAM and GDPR-friendly." } },
  { icon: Flame, title: { tr: "Sürekli ısıtma", en: "Always-on warmup" }, body: { tr: "Kampanya gönderirken bile itibarın arka planda korunur.", en: "Reputation is protected in the background even while you send." } },
  { icon: Zap, title: { tr: "Gerçek-zamanlı", en: "Real-time" }, body: { tr: "Açılmalar, cevaplar ve toplantılar geldikçe panele düşer.", en: "Opens, replies and meetings hit the panel the moment they happen." } },
];

/* Who Reachly is for — use-case cards. */
const USE_CASES: { icon: string; title: L; body: L }[] = [
  { icon: "rocket", title: { tr: "Kurucular & ilk satışlar", en: "Founders & first sales" }, body: { tr: "Henüz satış ekibin yokken ilk müşterilerine ulaş. Diziyi kur, ısıt, cevapları topla.", en: "Reach your first customers before you have a sales team. Build the sequence, warm up, gather replies." } },
  { icon: "briefcase", title: { tr: "Ajanslar", en: "Agencies" }, body: { tr: "Her müşteriye ayrı çalışma alanı, posta kutusu ve raporlama. Sınırsız müşteri ölçekle.", en: "A separate workspace, mailbox set and reporting per client. Scale across unlimited clients." } },
  { icon: "users", title: { tr: "Satış ekipleri", en: "Sales teams" }, body: { tr: "Outbound'u sistematikleştir: A/Z testi, koşullu dallar ve birleşik gelen kutusu.", en: "Systematize outbound: A/Z testing, conditional branches and a unified inbox." } },
  { icon: "store", title: { tr: "Yerel & DTC", en: "Local & DTC" }, body: { tr: "Demo, indirim ya da iş birliği için işletmelere kişiselleştirilmiş soğuk e-posta gönder.", en: "Send personalized cold email to businesses for demos, offers or partnerships." } },
];

/* Integration logos for the strip (the kit's expected integrations). */
const INTEGRATIONS: { name: string; glyph: "ses" | "smtp" | "verify" | "db"; sub: L }[] = [
  { name: "Amazon SES", glyph: "ses", sub: { tr: "Gönderim altyapısı", en: "Sending infrastructure" } },
  { name: "SMTP / IMAP", glyph: "smtp", sub: { tr: "Google & Microsoft", en: "Google & Microsoft" } },
  { name: "ZeroBounce", glyph: "verify", sub: { tr: "E-posta doğrulama", en: "Email verification" } },
  { name: "Supabase", glyph: "db", sub: { tr: "Veritabanı & auth", en: "Database & auth" } },
];

export default function LandingPage() {
  const { t, lang } = useLang();
  const m = appConfig.marketing;
  const tt = (v: L) => v[lang];

  /* Local section copy that doesn't live in app.config.ts. */
  const sectionCopy = {
    demoTitle: { tr: "Bir kampanyayı kendin başlat", en: "Launch a campaign yourself" } as L,
    demoSub: { tr: "Adımları aç/kapat, başlat'a bas ve gönderim, açılma, cevap sayaçlarının yükselişini izle — hepsi tarayıcında.", en: "Toggle the steps, hit launch, and watch the sent, open and reply counters climb — all in your browser." } as L,
    featuresTitle: { tr: "Soğuk e-posta için ihtiyacın olan her şey", en: "Everything you need for cold email" } as L,
    featuresSub: { tr: "Posta kutularından dizilere, ısıtmadan birleşik gelen kutusuna — tek panel.", en: "From mailboxes to sequences to warmup to a unified inbox — in one panel." } as L,
    howTitle: { tr: "Dört adımda erişim", en: "Outreach in four steps" } as L,
    howSub: { tr: "İçe aktar, ısıt, gönder, cevapla. Reachly aradaki her şeyi halleder.", en: "Import, warm up, send, reply. Reachly handles everything in between." } as L,
    deepTitle: { tr: "Teslimat, sonradan değil baştan", en: "Deliverability, by design" } as L,
    deepSub: { tr: "Üç katman, tek panel: ısıt, doğrula, hacmi kontrol et.", en: "Three layers, one panel: warm up, authenticate, control volume." } as L,
    useCasesTitle: { tr: "Reachly kimler için?", en: "Who Reachly is for" } as L,
    useCasesSub: { tr: "Soğuk e-postayla büyüyen her ekip için bir akış.", en: "A flow for every team growing with cold email." } as L,
    apiTitle: { tr: "Geliştiriciler için kuruldu", en: "Built for developers" } as L,
    apiSub: { tr: "Temiz bir REST API, imzalı webhook'lar ve örnek-temelli dokümanlar — kendi akışına göm.", en: "A clean REST API, signed webhooks and example-first docs — embed it in your own flow." } as L,
    integrationsTitle: { tr: "Sevdiğin araçlarla çalışır", en: "Works with the tools you love" } as L,
    integrationsSub: { tr: "SES, SMTP, ZeroBounce ve Supabase'i dakikalar içinde bağla — ya da anahtarsız demo modda kal.", en: "Wire SES, SMTP, ZeroBounce and Supabase in minutes — or stay in keyless demo mode." } as L,
    compareTitle: { tr: "Neden Reachly?", en: "Why Reachly?" } as L,
    compareSub: { tr: "Manuel takip ve genel e-posta araçlarıyla karşılaştır.", en: "Compared to manual tracking and generic email tools." } as L,
    testimonialsTitle: { tr: "Ekipler Reachly ile cevap alıyor", en: "Teams get replies with Reachly" } as L,
    testimonialsSub: { tr: "Soğuk e-postayla büyüyen kurucu ve ajanslardan.", en: "From founders and agencies growing with cold email." } as L,
    pricingTitle: { tr: "Basit, dürüst fiyatlandırma", en: "Simple, honest pricing" } as L,
    pricingSub: { tr: "Ücretsiz başla. Kişi başı ücret yok — posta kutusu başına değil.", en: "Start free. No per-contact fees — and no charge per mailbox." } as L,
    popular: { tr: "En popüler", en: "Most popular" } as L,
    faqTitle: { tr: "Sıkça sorulanlar", en: "Frequently asked" } as L,
    faqSub: { tr: "Cevabını bulamadın mı? Ekibimize yaz.", en: "Can't find an answer? Reach our team." } as L,
    ctaTitle: { tr: "Bugün cevap almaya başla", en: "Start getting replies today" } as L,
    ctaSub: { tr: "Anahtarsız demo modda aç, hazır olunca SES ve SMTP posta kutularını bağla.", en: "Open the keyless demo, then wire SES and SMTP mailboxes when you're ready." } as L,
  };

  return (
    <>
      {/* ── HERO ──────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10" style={{ background: "var(--grad-hero)" }} aria-hidden />
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-5 py-16 sm:py-24 lg:grid-cols-[1.05fr_0.95fr]">
          {/* Left copy */}
          <div className="stagger">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground shadow-pill">
              <span className="h-1.5 w-1.5 rounded-full bg-primary pulse-dot" />
              {t(m.badge)}
            </span>
            <h1 className="mt-5 max-w-xl font-display text-[40px] font-extrabold leading-[1.03] tracking-[-0.03em] sm:text-[56px]">
              {t(m.heroTitle)}{" "}
              <span className="bg-gradient-to-br from-[oklch(66%_0.15_214)] to-[oklch(55%_0.16_234)] bg-clip-text text-transparent">
                {t(m.heroAccent)}
              </span>
            </h1>
            <p className="mt-5 max-w-lg text-[17px] leading-relaxed text-muted-foreground">{t(m.heroSubtitle)}</p>

            <ul className="mt-6 space-y-2.5">
              {HERO_BENEFITS.map((b) => (
                <li key={tt(b)} className="flex items-start gap-2.5 text-[15px]">
                  <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-success/12 text-success">
                    <Check className="h-3 w-3" strokeWidth={3} />
                  </span>
                  {tt(b)}
                </li>
              ))}
            </ul>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/signup"
                className="inline-flex h-12 items-center justify-center gap-2 rounded-xl bg-primary px-6 text-[15px] font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90"
              >
                {t(m.heroCtaPrimary)} <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="#demo"
                className="inline-flex h-12 items-center justify-center gap-2 rounded-xl border border-border bg-card px-6 text-[15px] font-semibold text-foreground shadow-pill transition-colors hover:bg-muted"
              >
                {t(m.heroCtaSecondary)}
              </a>
            </div>

            <p className="mt-4 text-xs text-muted-foreground">
              {lang === "tr" ? "Kredi kartı gerekmez · Anahtarsız demo · 5 dakikada kurulum" : "No credit card · Keyless demo · 5-minute setup"}
            </p>
          </div>

          {/* Right floating product preview */}
          <div className="relative animate-float-up lg:pl-4">
            <div className="absolute -left-6 -top-6 -z-10 h-40 w-40 rounded-full bg-primary/10 blur-3xl drift" aria-hidden />
            <div className="absolute -bottom-8 -right-4 -z-10 h-44 w-44 rounded-full bg-[oklch(60%_0.16_200)]/10 blur-3xl" aria-hidden />
            <ProductPreview />
          </div>
        </div>

        {/* Trusted-by row */}
        <div className="border-y border-border bg-card/50">
          <div className="mx-auto max-w-6xl px-5 py-6">
            <p className="text-center text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
              {lang === "tr" ? "Büyüyen ekipler tarafından kullanılıyor" : "Used by growing teams"}
            </p>
            <div className="mt-5 flex flex-wrap items-center justify-center gap-x-8 gap-y-4 sm:gap-x-12">
              {TRUSTED.map((c) => (
                <CompanyMark key={c} name={c} />
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── STATS BAND ────────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-5 py-16">
        <div className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-border bg-border shadow-soft sm:grid-cols-4">
          {BIG_STATS.map((s) => (
            <div key={s.value} className="bg-card px-5 py-8 text-center">
              <p className="tnum font-display text-3xl font-extrabold tracking-tight">{s.value}</p>
              <p className="mt-1.5 text-xs text-muted-foreground">{tt(s.label)}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── INTERACTIVE DEMO ──────────────────────────────────────── */}
      <section id="demo" className="mx-auto max-w-6xl px-5 py-20">
        <div className="grid items-center gap-12 lg:grid-cols-[1fr_1fr]">
          <div>
            <p className="label-mono text-primary">{lang === "tr" ? "Canlı demo" : "Live demo"}</p>
            <h2 className="mt-2 max-w-md font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(sectionCopy.demoTitle)}</h2>
            <p className="mt-3 max-w-md text-muted-foreground">{tt(sectionCopy.demoSub)}</p>
            <div className="mt-6 grid grid-cols-2 gap-3 sm:grid-cols-2">
              {[
                { icon: Send, label: { tr: "Dizi adımları", en: "Sequence steps" } as L, sub: { tr: "e-posta · bekle · koşul", en: "email · wait · condition" } as L },
                { icon: Flame, label: { tr: "Otomatik ısıtma", en: "Auto warmup" } as L, sub: { tr: "arka planda çalışır", en: "runs in the background" } as L },
                { icon: Inbox, label: { tr: "Birleşik kutusu", en: "Unified inbox" } as L, sub: { tr: "tüm cevaplar tek yerde", en: "all replies in one place" } as L },
                { icon: ShieldCheck, label: { tr: "Teslimat koruması", en: "Deliverability" } as L, sub: { tr: "SPF · DKIM · DMARC", en: "SPF · DKIM · DMARC" } as L },
              ].map((f) => {
                const I = f.icon;
                return (
                  <div key={tt(f.label)} className="rounded-xl border border-border bg-card p-3 shadow-soft">
                    <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary/10 text-primary">
                      <I className="h-4 w-4" />
                    </span>
                    <p className="mt-2 text-[13px] font-semibold leading-tight">{tt(f.label)}</p>
                    <p className="mt-0.5 text-[11px] text-muted-foreground">{tt(f.sub)}</p>
                  </div>
                );
              })}
            </div>
          </div>
          <FlowDemo />
        </div>
      </section>

      {/* ── FEATURES ──────────────────────────────────────────────── */}
      <section id="features" className="border-t border-border bg-muted/30">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(sectionCopy.featuresTitle)}</h2>
            <p className="mt-3 text-muted-foreground">{tt(sectionCopy.featuresSub)}</p>
          </div>
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {m.features.map((f) => (
              <div key={tt(f.title)} className="group rounded-2xl border border-border bg-card p-6 shadow-soft transition-shadow hover:shadow-pop">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                  <Icon name={f.icon} className="h-5 w-5" />
                </span>
                <h3 className="mt-4 font-semibold tracking-tight">{t(f.title)}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{t(f.body)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── USE CASES ─────────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(sectionCopy.useCasesTitle)}</h2>
          <p className="mt-3 text-muted-foreground">{tt(sectionCopy.useCasesSub)}</p>
        </div>
        <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {USE_CASES.map((u) => (
            <div key={tt(u.title)} className="rounded-2xl border border-border bg-card p-6 shadow-soft transition-shadow hover:shadow-pop">
              <span className="grid h-11 w-11 place-items-center rounded-xl bg-primary/10 text-primary">
                <Icon name={u.icon} className="h-5 w-5" />
              </span>
              <h3 className="mt-4 font-semibold tracking-tight">{tt(u.title)}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{tt(u.body)}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── HOW IT WORKS ──────────────────────────────────────────── */}
      <section id="how" className="mx-auto max-w-6xl px-5 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(sectionCopy.howTitle)}</h2>
          <p className="mt-3 text-muted-foreground">{tt(sectionCopy.howSub)}</p>
        </div>
        <div className="relative mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
          {HOW_STEPS.map((s, i) => (
            <div key={s.n} className="relative rounded-2xl border border-border bg-card p-6 shadow-soft">
              <div className="flex items-center justify-between">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-primary/10 text-primary">
                  <Icon name={s.icon} className="h-5 w-5" />
                </span>
                <span className="font-display text-3xl font-extrabold text-primary/15">{s.n}</span>
              </div>
              <h3 className="mt-4 font-semibold tracking-tight">{tt(s.title)}</h3>
              <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{tt(s.body)}</p>
              {i < HOW_STEPS.length - 1 && (
                <span className="absolute -right-3 top-1/2 z-10 hidden h-6 w-6 -translate-y-1/2 place-items-center rounded-full border border-border bg-card text-muted-foreground lg:grid">
                  <ArrowRight className="h-3 w-3" />
                </span>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* ── DELIVERABILITY DEEP-DIVE ──────────────────────────────── */}
      <section className="border-y border-border bg-muted/30">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(sectionCopy.deepTitle)}</h2>
            <p className="mt-3 text-muted-foreground">{tt(sectionCopy.deepSub)}</p>
          </div>
          <div className="mt-14 space-y-16">
            {DEEP_DIVE.map((d, idx) => (
              <div
                key={tt(d.title)}
                className={cn("grid items-center gap-10 lg:grid-cols-2", d.reverse && "lg:[&>*:first-child]:order-2")}
              >
                <div>
                  <p className="label-mono text-primary">{tt(d.eyebrow)}</p>
                  <h3 className="mt-2 max-w-md font-display text-2xl font-bold tracking-tight sm:text-3xl">{tt(d.title)}</h3>
                  <p className="mt-3 max-w-md text-muted-foreground">{tt(d.body)}</p>
                  <ul className="mt-5 space-y-2.5">
                    {d.points.map((p) => (
                      <li key={tt(p)} className="flex items-start gap-2.5 text-[15px]">
                        <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-primary/10 text-primary">
                          <Check className="h-3 w-3" strokeWidth={3} />
                        </span>
                        {tt(p)}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* small illustrative panel */}
                <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
                  {idx === 0 && <WarmupPanel lang={lang} />}
                  {idx === 1 && <AuthPanel lang={lang} />}
                  {idx === 2 && <VolumePanel lang={lang} />}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── DEVELOPER / API ───────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="grid items-center gap-10 lg:grid-cols-2">
          <div>
            <p className="label-mono text-primary">API</p>
            <h2 className="mt-2 max-w-md font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(sectionCopy.apiTitle)}</h2>
            <p className="mt-3 max-w-md text-muted-foreground">{tt(sectionCopy.apiSub)}</p>
            <ul className="mt-6 space-y-2.5">
              {[
                { tr: "REST + imzalı webhook'lar", en: "REST + signed webhooks" },
                { tr: "Cevap ve açılma olayları anında", en: "Reply and open events in real time" },
                { tr: "TypeScript & Python SDK'ları", en: "TypeScript & Python SDKs" },
              ].map((p) => (
                <li key={p.en} className="flex items-start gap-2.5 text-[15px]">
                  <span className="mt-0.5 grid h-5 w-5 shrink-0 place-items-center rounded-full bg-primary/10 text-primary">
                    <Check className="h-3 w-3" strokeWidth={3} />
                  </span>
                  {lang === "tr" ? p.tr : p.en}
                </li>
              ))}
            </ul>
          </div>
          {/* code preview card */}
          <div className="overflow-hidden rounded-2xl border border-border bg-[oklch(22%_0.02_240)] shadow-pop">
            <div className="flex items-center gap-1.5 border-b border-white/10 px-4 py-3">
              <span className="h-2.5 w-2.5 rounded-full bg-destructive/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-warning/70" />
              <span className="h-2.5 w-2.5 rounded-full bg-success/70" />
              <span className="ml-2 font-mono text-[11px] text-white/40">launch-sequence.ts</span>
            </div>
            <pre className="overflow-x-auto p-4 font-mono text-[12.5px] leading-relaxed text-white/80">
{`const campaign = await reachly.campaigns.create({
  name: "Q3 SaaS Founders — US",
  mailboxes: ["alex@reachly.io", "ops@reachly.io"],
  steps: [
    { type: "email", template: "first-touch" },
    { type: "wait", days: 2 },
    { type: "email", template: "follow-up" },
  ],
  stopOnReply: true,
});

// → reachly rotates volume, warms mailboxes,
//   and streams every reply to your inbox.
reachly.on("reply.received", (e) => {
  route(e.leadId, e.sentiment);
});`}
            </pre>
          </div>
        </div>
      </section>

      {/* ── COMPARISON TABLE ──────────────────────────────────────── */}
      <section className="mx-auto max-w-5xl px-5 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(sectionCopy.compareTitle)}</h2>
          <p className="mt-3 text-muted-foreground">{tt(sectionCopy.compareSub)}</p>
        </div>
        <div className="mt-12 overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="px-5 py-4 text-left font-medium text-muted-foreground"></th>
                  <th className="px-5 py-4 text-center font-medium text-muted-foreground">{lang === "tr" ? "Manuel / Mailchimp" : "Manual / Mailchimp"}</th>
                  <th className="px-5 py-4 text-center font-medium text-muted-foreground">{lang === "tr" ? "Genel araç" : "Generic tool"}</th>
                  <th className="bg-primary/[0.04] px-5 py-4 text-center">
                    <span className="inline-flex items-center gap-1.5 font-semibold text-primary">
                      <Send className="h-4 w-4" />
                      {appConfig.name}
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {COMPARE.map((row, i) => (
                  <tr key={tt(row.feature)} className={cn("border-b border-border/60 last:border-0", i % 2 === 1 && "bg-muted/20")}>
                    <td className="px-5 py-3.5 font-medium">{tt(row.feature)}</td>
                    <CompareCell value={row.manual} lang={lang} />
                    <CompareCell value={row.generic} lang={lang} />
                    <CompareCell value={row.reachly} lang={lang} highlight />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ──────────────────────────────────────────── */}
      <section className="border-t border-border bg-muted/30">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(sectionCopy.testimonialsTitle)}</h2>
            <p className="mt-3 text-muted-foreground">{tt(sectionCopy.testimonialsSub)}</p>
          </div>
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {TESTIMONIALS.map((tm) => (
              <figure key={tm.name} className="flex flex-col rounded-2xl border border-border bg-card p-6 shadow-soft">
                <Quote className="h-5 w-5 text-primary/30" />
                <blockquote className="mt-3 flex-1 text-[14.5px] leading-relaxed text-foreground/90">
                  {tt(tm.quote)}
                </blockquote>
                <div className="mt-5 flex items-center gap-3 border-t border-border pt-4">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full text-xs font-bold text-white" style={{ backgroundImage: "var(--grad-brand)" }}>
                    {tm.initials}
                  </span>
                  <div className="min-w-0 flex-1">
                    <figcaption className="text-sm font-semibold leading-tight">{tm.name}</figcaption>
                    <p className="truncate text-xs text-muted-foreground">{tt(tm.role)}</p>
                  </div>
                  <span className="shrink-0 rounded-full bg-success/10 px-2 py-1 text-[11px] font-semibold text-success">{tt(tm.metric)}</span>
                </div>
              </figure>
            ))}
          </div>
          <div className="mt-8 flex items-center justify-center gap-1.5 text-sm text-muted-foreground">
            {Array.from({ length: 5 }).map((_, i) => (
              <Star key={i} className="h-4 w-4 fill-warning text-warning" />
            ))}
            <span className="ml-2">{lang === "tr" ? "4.9/5 · 600+ kurucu" : "4.9/5 · 600+ founders"}</span>
          </div>

          {/* three small trust cards */}
          <div className="mt-12 grid gap-5 sm:grid-cols-3">
            {TRUST_POINTS.map((s) => {
              const I = s.icon;
              return (
                <div key={tt(s.title)} className="rounded-2xl border border-border bg-card p-6 text-center shadow-soft">
                  <span className="mx-auto grid h-12 w-12 place-items-center rounded-xl bg-primary/10 text-primary">
                    <I className="h-5 w-5" />
                  </span>
                  <h3 className="mt-4 font-semibold tracking-tight">{tt(s.title)}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{tt(s.body)}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── INTEGRATIONS STRIP ────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="mx-auto max-w-2xl text-center">
          <h2 className="font-display text-2xl font-bold tracking-tight sm:text-3xl">{tt(sectionCopy.integrationsTitle)}</h2>
          <p className="mt-3 text-muted-foreground">{tt(sectionCopy.integrationsSub)}</p>
        </div>
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {INTEGRATIONS.map((it) => (
            <div key={it.name} className="flex items-center gap-3 rounded-2xl border border-border bg-card p-5 shadow-soft">
              <IntegrationGlyph glyph={it.glyph} />
              <div className="min-w-0">
                <p className="truncate font-semibold tracking-tight">{it.name}</p>
                <p className="truncate text-xs text-muted-foreground">{tt(it.sub)}</p>
              </div>
              <span className="ml-auto inline-flex shrink-0 items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success">
                <span className="h-1.5 w-1.5 rounded-full bg-success" />
                {lang === "tr" ? "Hazır" : "Ready"}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* ── PRICING ───────────────────────────────────────────────── */}
      <section id="pricing" className="border-t border-border bg-muted/30">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(sectionCopy.pricingTitle)}</h2>
            <p className="mt-3 text-muted-foreground">{tt(sectionCopy.pricingSub)}</p>
          </div>
          <div className="mt-12 grid gap-5 lg:grid-cols-3">
            {m.pricing.map((tier) => (
              <div
                key={tier.name}
                className={cn(
                  "flex flex-col rounded-2xl border bg-card p-7 shadow-soft",
                  tier.featured ? "border-primary/40 shadow-pop ring-1 ring-primary/20" : "border-border",
                )}
              >
                {tier.featured && (
                  <span className="mb-3 inline-flex w-fit items-center gap-1 rounded-full bg-primary px-2.5 py-0.5 text-[11px] font-semibold text-primary-foreground">
                    <Star className="h-3 w-3 fill-current" />
                    {tt(sectionCopy.popular)}
                  </span>
                )}
                <h3 className="font-semibold tracking-tight">{tier.name}</h3>
                <div className="mt-2 flex items-baseline gap-1">
                  <span className="tnum font-display text-4xl font-extrabold tracking-tight">{tier.price}</span>
                  {tier.period && <span className="text-sm text-muted-foreground">{lang === "tr" ? tier.period : "/mo"}</span>}
                </div>
                <p className="mt-1.5 text-sm text-muted-foreground">{t(tier.tagline)}</p>
                <ul className="mt-6 flex-1 space-y-3 text-sm">
                  {tier.features.map((f) => (
                    <li key={t(f)} className="flex items-start gap-2.5">
                      <span className="mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded-full bg-success/12 text-success">
                        <Check className="h-2.5 w-2.5" strokeWidth={3} />
                      </span>
                      {t(f)}
                    </li>
                  ))}
                </ul>
                <Link
                  href="/signup"
                  className={cn(
                    "mt-7 inline-flex h-11 items-center justify-center rounded-xl text-sm font-semibold transition-all",
                    tier.featured
                      ? "bg-primary text-primary-foreground shadow-sm hover:opacity-90"
                      : "border border-border bg-card text-foreground hover:bg-muted",
                  )}
                >
                  {t(tier.cta)}
                </Link>
              </div>
            ))}
          </div>
          <p className="mt-6 text-center text-xs text-muted-foreground">
            {lang === "tr"
              ? "Tüm planlar abonelikten çıkma yönetimi ve teslimat denetimleriyle gelir."
              : "Every plan includes unsubscribe management and deliverability checks."}
          </p>
        </div>
      </section>

      {/* ── FAQ ───────────────────────────────────────────────────── */}
      <section id="faq" className="mx-auto max-w-3xl px-5 py-20">
        <div className="text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(sectionCopy.faqTitle)}</h2>
          <p className="mt-3 text-muted-foreground">{tt(sectionCopy.faqSub)}</p>
        </div>
        <div className="mt-10 space-y-3">
          {m.faq.map((f) => (
            <details key={t(f.q)} className="group rounded-xl border border-border bg-card px-5 py-4 shadow-soft">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-medium">
                {t(f.q)}
                <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full border border-border text-muted-foreground transition-colors group-open:border-primary group-open:bg-primary group-open:text-primary-foreground">
                  <Plus className="h-3.5 w-3.5 group-open:hidden" />
                  <Minus className="hidden h-3.5 w-3.5 group-open:block" />
                </span>
              </summary>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{t(f.a)}</p>
            </details>
          ))}
        </div>
      </section>

      {/* ── FINAL CTA ─────────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-5 pb-24">
        <div className="relative overflow-hidden rounded-3xl border border-border bg-card px-8 py-16 text-center shadow-pop">
          <div className="pointer-events-none absolute inset-0 -z-10" style={{ background: "var(--grad-hero)" }} aria-hidden />
          <span className="pointer-events-none absolute -left-10 top-0 -z-10 h-48 w-48 rounded-full bg-primary/10 blur-3xl drift" aria-hidden />
          <div className="mx-auto mb-5 flex w-fit items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground shadow-pill">
            <span className="grid h-5 w-5 place-items-center rounded-md bg-primary/10 text-primary"><Mail className="h-3 w-3" /></span>
            <span className="grid h-5 w-5 place-items-center rounded-md bg-primary/10 text-primary"><Flame className="h-3 w-3" /></span>
            <span className="grid h-5 w-5 place-items-center rounded-md bg-primary/10 text-primary"><ReplyIcon className="h-3 w-3" /></span>
            <span>{lang === "tr" ? "gönder · ısıt · cevapla" : "send · warm · reply"}</span>
          </div>
          <h2 className="mx-auto max-w-2xl font-display text-3xl font-extrabold tracking-tight sm:text-4xl">{tt(sectionCopy.ctaTitle)}</h2>
          <p className="mx-auto mt-3 max-w-xl text-muted-foreground">{tt(sectionCopy.ctaSub)}</p>
          <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Link
              href="/signup"
              className="inline-flex h-12 items-center justify-center gap-2 rounded-xl bg-primary px-7 text-[15px] font-semibold text-primary-foreground shadow-sm transition-opacity hover:opacity-90"
            >
              {t(m.heroCtaPrimary)} <ArrowRight className="h-4 w-4" />
            </Link>
            <a
              href="#demo"
              className="inline-flex h-12 items-center justify-center rounded-xl border border-border bg-card px-7 text-[15px] font-semibold text-foreground shadow-pill transition-colors hover:bg-muted"
            >
              {t(m.heroCtaSecondary)}
            </a>
          </div>
        </div>
      </section>
    </>
  );
}

/* ── Deep-dive inline panels (all inline SVG / CSS, no photos) ──────────────── */

function WarmupPanel({ lang }: { lang: "tr" | "en" }) {
  // 14-day warmup ramp bars
  const ramp = [12, 16, 20, 22, 28, 30, 34, 36, 40, 38, 42, 44, 46, 48];
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-[13px] font-semibold">{lang === "tr" ? "Isıtma rampası" : "Warmup ramp"}</p>
        <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success">
          <Flame className="h-3 w-3" /> {lang === "tr" ? "Sağlık 92" : "Health 92"}
        </span>
      </div>
      <div className="flex h-24 items-end gap-1">
        {ramp.map((v, i) => (
          <div key={i} className="flex-1 rounded-t-sm" style={{ height: `${(v / 48) * 100}%`, background: "var(--grad-brand)", opacity: 0.55 + (i / ramp.length) * 0.45 }} />
        ))}
      </div>
      <div className="flex items-center justify-between text-[11px] text-muted-foreground">
        <span>{lang === "tr" ? "Gün 1 · 12/gün" : "Day 1 · 12/day"}</span>
        <span>{lang === "tr" ? "Gün 14 · 48/gün" : "Day 14 · 48/day"}</span>
      </div>
    </div>
  );
}

function AuthPanel({ lang }: { lang: "tr" | "en" }) {
  const checks: { label: L; ok: boolean }[] = [
    { label: { tr: "SPF kaydı", en: "SPF record" }, ok: true },
    { label: { tr: "DKIM imzası", en: "DKIM signature" }, ok: true },
    { label: { tr: "DMARC politikası", en: "DMARC policy" }, ok: true },
    { label: { tr: "Kara liste taraması", en: "Blacklist scan" }, ok: true },
    { label: { tr: "Özel takip alanı", en: "Custom tracking domain" }, ok: false },
  ];
  return (
    <div className="space-y-2.5">
      <p className="text-[13px] font-semibold">{lang === "tr" ? "Alan adı sağlığı" : "Domain health"}</p>
      {checks.map((c) => (
        <div key={c.label.en} className="flex items-center justify-between rounded-xl border border-border bg-muted/30 px-3 py-2.5 text-[13px]">
          <span className="text-foreground/80">{lang === "tr" ? c.label.tr : c.label.en}</span>
          {c.ok ? (
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-success">
              <Check className="h-3.5 w-3.5" strokeWidth={3} /> {lang === "tr" ? "Geçti" : "Pass"}
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-warning-foreground">
              <Minus className="h-3.5 w-3.5" /> {lang === "tr" ? "Eksik" : "Set up"}
            </span>
          )}
        </div>
      ))}
    </div>
  );
}

function VolumePanel({ lang }: { lang: "tr" | "en" }) {
  const boxes = [
    { email: "alex@reachly.io", pct: 74, label: "184/250" },
    { email: "ops@reachly.io", pct: 28, label: "22/80" },
    { email: "team@reachly.io", pct: 80, label: "96/120" },
  ];
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-[13px] font-semibold">{lang === "tr" ? "Günlük gönderim sınırı" : "Daily sending caps"}</p>
        <span className="tnum text-[11px] text-muted-foreground">{lang === "tr" ? "spam 0.6/10" : "spam 0.6/10"}</span>
      </div>
      {boxes.map((b) => (
        <div key={b.email} className="rounded-xl border border-border bg-muted/30 p-3">
          <div className="flex items-center justify-between">
            <span className="truncate text-[12.5px] font-semibold">{b.email}</span>
            <span className="tnum shrink-0 text-[11px] text-muted-foreground">{b.label}</span>
          </div>
          <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div className="h-full rounded-full" style={{ width: `${b.pct}%`, background: "var(--grad-brand)" }} />
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── Comparison cell — boolean → check/minus, string/L → label ──────────────── */
function CompareCell({
  value,
  lang,
  highlight = false,
}: {
  value: boolean | L | string;
  lang: "tr" | "en";
  highlight?: boolean;
}) {
  const text = typeof value === "string" ? value : typeof value === "object" ? value[lang] : null;
  return (
    <td className={cn("px-5 py-3.5 text-center", highlight && "bg-primary/[0.04]")}>
      {typeof value === "boolean" ? (
        value ? (
          <span className={cn("mx-auto grid h-5 w-5 place-items-center rounded-full", highlight ? "bg-primary text-primary-foreground" : "bg-success/12 text-success")}>
            <Check className="h-3 w-3" strokeWidth={3} />
          </span>
        ) : (
          <span className="mx-auto grid h-5 w-5 place-items-center rounded-full bg-muted text-muted-foreground">
            <Minus className="h-3 w-3" />
          </span>
        )
      ) : (
        <span className={cn("text-[13px] font-medium", highlight ? "text-primary" : "text-muted-foreground")}>{text}</span>
      )}
    </td>
  );
}
