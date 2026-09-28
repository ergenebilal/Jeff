"use client";

import Link from "next/link";
import {
  ArrowRight,
  Check,
  Minus,
  Plus,
  Quote,
  Star,
  Kanban,
  PhoneCall,
  Mail,
  TrendingUp,
  Workflow,
  GripVertical,
} from "lucide-react";
import appConfig from "@/app.config";
import { Icon } from "@/components/ui/icon";
import { Avatar } from "@/components/app/avatar";
import { PipelineDemo } from "@/components/marketing/pipeline-demo";
import { ProductPreview, CompanyMark } from "@/components/marketing/marks";
import { useLang } from "@/components/i18n/language-provider";
import { cn, formatMoney } from "@/lib/utils";
import { stages, repById } from "@/lib/demo/data";
import type { L } from "@/lib/i18n/config";

/* ─────────────────────────────────────────────────────────────────────────────
   Local bilingual copy that doesn't belong in app.config.ts. Everything here is
   { tr, en } and resolved through the active language via tt().
   ───────────────────────────────────────────────────────────────────────────── */

const HERO_BENEFITS: L[] = [
  { tr: "Görsel pipeline — deal'leri sürükle-bırak ile taşı", en: "A visual pipeline — drag deals across stages" },
  { tr: "Her arama, e-posta ve toplantı otomatik kaydedilir", en: "Every call, email and meeting logged automatically" },
  { tr: "Olasılığa göre ağırlıklı, güvenebileceğin bir tahmin", en: "A probability-weighted forecast you can trust" },
];

const TRUSTED = ["Northwind", "Parable", "Formwork", "Cedarworks", "Lumen", "Harvest", "Brightline", "Meridian"];

const HOW_STEPS: { n: string; icon: string; title: L; body: L }[] = [
  {
    n: "01",
    icon: "user-plus",
    title: { tr: "Deal ekle", en: "Add deals" },
    body: { tr: "Kişiyi, şirketi ve değeri gir — ya da CSV / e-postadan içe aktar. Lead zenginleştirme gerisini doldurur.", en: "Drop in the contact, company and value — or import from CSV / email. Enrichment fills in the rest." },
  },
  {
    n: "02",
    icon: "kanban",
    title: { tr: "Aşamaları taşı", en: "Move stages" },
    body: { tr: "Deal kartını tutup hedef sütuna sürükle. Pipeline değeri ve kazanma oranı anında güncellenir.", en: "Grab a deal card and drag it to the next column. Pipeline value and win rate update instantly." },
  },
  {
    n: "03",
    icon: "phone-call",
    title: { tr: "Aktiviteleri takip et", en: "Track activities" },
    body: { tr: "Aramalar, e-postalar ve toplantılar deal'e bağlanır. Vadesi gelen görev hiç kaçmaz.", en: "Calls, emails and meetings attach to the deal. Due tasks never slip." },
  },
  {
    n: "04",
    icon: "trophy",
    title: { tr: "Kapat", en: "Close" },
    body: { tr: "Deal'i Kazanıldı'ya taşı; Slack'e bildirim gider, tahmin güncellenir, ekip kutlar.", en: "Move the deal to Won; Slack pings, the forecast updates, the team celebrates." },
  },
];

type CompareValue = boolean | L | string;
const COMPARE: { feature: L; sheets: CompareValue; bloated: CompareValue; pipely: CompareValue }[] = [
  { feature: { tr: "Görsel sürükle-bırak pipeline", en: "Visual drag-drop pipeline" }, sheets: false, bloated: true, pipely: true },
  { feature: { tr: "Otomatik aktivite kaydı", en: "Auto activity logging" }, sheets: false, bloated: { tr: "Kısmi", en: "Partial" }, pipely: true },
  { feature: { tr: "Ağırlıklı tahmin", en: "Weighted forecasting" }, sheets: { tr: "Manuel", en: "Manual" }, bloated: true, pipely: true },
  { feature: { tr: "E-posta & takvim senkronu", en: "Email & calendar sync" }, sheets: false, bloated: true, pipely: true },
  { feature: { tr: "Temsilciler gerçekten günceller", en: "Reps actually keep it current" }, sheets: { tr: "Asla", en: "Never" }, bloated: false, pipely: true },
  { feature: { tr: "5 dakikada kurulum", en: "5-minute setup" }, sheets: true, bloated: false, pipely: true },
  { feature: { tr: "Kullanıcı başına ücret", en: "Per-user price" }, sheets: { tr: "Ücretsiz", en: "Free" }, bloated: "$65+", pipely: "$29" },
];

const TESTIMONIALS: { quote: L; name: string; role: L; initials: string; color: string; metric: L }[] = [
  { quote: { tr: "Ekibim ilk kez CRM'i gerçekten güncelliyor. Sürükle-bırak o kadar kolay ki bahane kalmadı.", en: "My team actually updates the CRM now. Drag-and-drop is so easy there's no excuse." }, name: "Maria Gomez", role: { tr: "VP Sales · Northwind", en: "VP Sales · Northwind" }, initials: "MG", color: "var(--seg-1)", metric: { tr: "kazanma +%20", en: "win rate +20%" } },
  { quote: { tr: "Tahmin nihayet doğru. Pipeline ağırlıklandırması yönetimle yaptığım toplantıları yarıya indirdi.", en: "The forecast is finally accurate. Weighted pipeline cut my exec meetings in half." }, name: "Liam Chen", role: { tr: "Kurucu · Parable", en: "Founder · Parable" }, initials: "LC", color: "var(--seg-2)", metric: { tr: "tahmin %98 isabet", en: "98% forecast" } },
  { quote: { tr: "Gmail'i bağladık; her e-posta doğru deal'e düştü. Veri girişi pratikte sıfıra indi.", en: "We connected Gmail and every email landed on the right deal. Data entry dropped to near zero." }, name: "Nadia Park", role: { tr: "Operasyon · Formwork", en: "Head of Ops · Formwork" }, initials: "NP", color: "var(--seg-3)", metric: { tr: "haftada 8s kazanç", en: "8h/wk saved" } },
  { quote: { tr: "Bloated bir CRM'den geçtik. Pipely temiz, hızlı ve temsilcilerimiz onu seviyor.", en: "We switched off a bloated CRM. Pipely is clean, fast, and our reps love it." }, name: "Tom Reilly", role: { tr: "CTO · Cedarworks", en: "CTO · Cedarworks" }, initials: "TR", color: "var(--seg-4)", metric: { tr: "%100 benimsendi", en: "100% adoption" } },
  { quote: { tr: "Aktivite hatırlatıcıları sayesinde hiçbir takip kaçmıyor. Cevap süremiz çok düştü.", en: "Activity reminders mean no follow-up slips. Our response time fell off a cliff." }, name: "Aisha Khan", role: { tr: "CEO · Lumen", en: "CEO · Lumen" }, initials: "AK", color: "var(--seg-1)", metric: { tr: "yanıt 4s → 40dk", en: "4h → 40m reply" } },
  { quote: { tr: "Deal kapanınca Slack'e otomatik bildirim gidiyor. Ekip enerjisi tavan yaptı.", en: "Every won deal auto-pings Slack. Team morale went through the roof." }, name: "Diego Santos", role: { tr: "Satış · Harvest", en: "Sales · Harvest" }, initials: "DS", color: "var(--seg-2)", metric: { tr: "döngü %30 kısaldı", en: "30% shorter cycle" } },
];

/* Who Pipely is for — use-case cards. */
const USE_CASES: { icon: string; title: L; body: L }[] = [
  { icon: "rocket", title: { tr: "Startup satış ekipleri", en: "Startup sales teams" }, body: { tr: "İlk satış sürecini kur, deal'leri tek tahtada takip et, kurucu olarak pipeline'ı net gör.", en: "Stand up your first sales process, track deals on one board, see the pipeline as a founder." } },
  { icon: "building-2", title: { tr: "Ajanslar & danışmanlık", en: "Agencies & consultancies" }, body: { tr: "Teklifleri, retainer'ları ve yenilemeleri aşamalarla yönet; her müşteri teması kayıt altında.", en: "Manage proposals, retainers and renewals by stage; every client touch on record." } },
  { icon: "store", title: { tr: "B2B SaaS", en: "B2B SaaS" }, body: { tr: "Demo'dan kapanışa kadar fırsatları izle, kotayı takip et, geliri ay ay öngör.", en: "Track opportunities from demo to close, follow quota, forecast revenue by month." } },
  { icon: "handshake", title: { tr: "Emlak & hizmet", en: "Real estate & services" }, body: { tr: "Lead'leri nitele, görüşmeleri planla, sıcak fırsatları asla soğumaya bırakma.", en: "Qualify leads, schedule viewings, and never let a hot opportunity go cold." } },
];

/* Deep-dive feature blocks (alternating). */
const DEEP_DIVE: { eyebrow: L; title: L; body: L; points: L[]; reverse?: boolean }[] = [
  {
    eyebrow: { tr: "Pipeline", en: "Pipeline" },
    title: { tr: "Tek bakışta tüm satışın", en: "Your whole sale at a glance" },
    body: { tr: "Her aşama bir sütun, her deal bir kart. Değeri, sahibini ve aşamada geçen günü gör; sürükle-bırak ile ilerlet.", en: "Each stage a column, each deal a card. See value, owner and days-in-stage; advance with a drag." },
    points: [
      { tr: "Sürükle-bırak aşama geçişi", en: "Drag-and-drop stage changes" },
      { tr: "Aşamada bekleyen deal uyarısı", en: "Stalled-deal warnings" },
      { tr: "Sahip ve değere göre filtre", en: "Filter by owner and value" },
    ],
  },
  {
    eyebrow: { tr: "Aktiviteler", en: "Activities" },
    title: { tr: "Her temas, otomatik kayıtlı", en: "Every touch, logged for you" },
    body: { tr: "Gmail veya Outlook'u bağla; e-postalar, toplantılar ve aramalar doğru deal'e bağlanır. Vadesi gelen görevler panelin başında durur.", en: "Connect Gmail or Outlook; emails, meetings and calls attach to the right deal. Due tasks sit at the top of your day." },
    points: [
      { tr: "E-posta & takvim iki yönlü senkron", en: "Two-way email & calendar sync" },
      { tr: "Arama / toplantı / görev türleri", en: "Call / meeting / task types" },
      { tr: "Akıllı takip hatırlatıcıları", en: "Smart follow-up reminders" },
    ],
    reverse: true,
  },
  {
    eyebrow: { tr: "Otomasyon", en: "Automation" },
    title: { tr: "Sıkıcı işi pipeline yapsın", en: "Let the pipeline do the busywork" },
    body: { tr: "Deal aşama değiştirince görev oluştur, e-posta gönder ya da Slack'e bildir. Kuralları sen koyarsın, Pipely uygular.", en: "When a deal changes stage, create a task, send an email or ping Slack. You set the rules, Pipely runs them." },
    points: [
      { tr: "Aşama-tetikli iş akışları", en: "Stage-triggered workflows" },
      { tr: "Kazanılan deal → Slack bildirimi", en: "Won deal → Slack notification" },
      { tr: "Otomatik görev ataması", en: "Automatic task assignment" },
    ],
  },
];

/* Integration logos for the strip. */
const INTEGRATIONS: { name: string; glyph: "db" | "mail" | "enrich" | "slack"; sub: L }[] = [
  { name: "Supabase", glyph: "db", sub: { tr: "Veritabanı & auth", en: "Database & auth" } },
  { name: "Gmail / Outlook", glyph: "mail", sub: { tr: "E-posta & takvim", en: "Email & calendar" } },
  { name: "Clearbit", glyph: "enrich", sub: { tr: "Lead zenginleştirme", en: "Lead enrichment" } },
  { name: "Slack", glyph: "slack", sub: { tr: "Deal bildirimleri", en: "Deal notifications" } },
];

export default function LandingPage() {
  const { t, lang } = useLang();
  const m = appConfig.marketing;
  const tt = (v: L) => v[lang];

  const sectionCopy = {
    demoTitle: { tr: "Bir deal'i Kazanıldı'ya sürükle", en: "Drag a deal into Won" } as L,
    demoSub: { tr: "Bu canlı pipeline'da bir kartı taşı — açık pipeline değeri ve kazanma oranı anında güncellenir. Pipely'nin günlük hissi tam olarak bu.", en: "Move a card in this live pipeline — open pipeline value and win rate update instantly. This is exactly how Pipely feels every day." } as L,
    featuresTitle: { tr: "Satışı kapatmak için ihtiyacın olan her şey", en: "Everything you need to close" } as L,
    featuresSub: { tr: "Pipeline'dan tahmine, aktivitelerden otomasyona kadar tek panel.", en: "From pipeline to forecast to activities to automation, in one panel." } as L,
    howTitle: { tr: "Dört adımda kapanış", en: "Close in four steps" } as L,
    howSub: { tr: "Ekle, taşı, takip et, kapat. Pipely aradaki her şeyi halleder.", en: "Add, move, track, close. Pipely handles everything in between." } as L,
    forecastTitle: { tr: "Güvenebileceğin bir tahmin", en: "A forecast you can trust" } as L,
    forecastSub: { tr: "Her aşamanın bir kazanma olasılığı var. Pipely açık deal'leri bununla ağırlıklandırır ve kapanış tarihine göre ay ay toplar.", en: "Each stage carries a win probability. Pipely weights open deals by it and rolls them up by close date, month by month." } as L,
    useCasesTitle: { tr: "Pipely kimler için?", en: "Who Pipely is for" } as L,
    useCasesSub: { tr: "Pipeline'ı olan her satış ekibi için bir akış.", en: "A flow for every team with a pipeline." } as L,
    deepTitle: { tr: "Lead'den deftere kadar", en: "From lead to ledger" } as L,
    deepSub: { tr: "Üç katman, tek panel: pipeline, aktiviteler, otomasyon.", en: "Three layers, one panel: pipeline, activities, automation." } as L,
    integrationsTitle: { tr: "Sevdiğin araçlarla çalışır", en: "Works with the tools you love" } as L,
    integrationsSub: { tr: "Supabase, Gmail/Outlook, Clearbit ve Slack'i dakikalar içinde bağla.", en: "Wire Supabase, Gmail/Outlook, Clearbit and Slack in minutes." } as L,
    compareTitle: { tr: "Neden Pipely?", en: "Why Pipely?" } as L,
    compareSub: { tr: "Tablolar ve şişkin CRM'lerle karşılaştır.", en: "Compared to spreadsheets and bloated CRMs." } as L,
    testimonialsTitle: { tr: "Satış liderleri Pipely'yi seviyor", en: "Sales leaders love Pipely" } as L,
    testimonialsSub: { tr: "Pipeline'ını gerçekten güncelleyen ekiplerden.", en: "From teams that actually keep their pipeline current." } as L,
    pricingTitle: { tr: "Basit, kullanıcı-başına fiyatlandırma", en: "Simple, per-user pricing" } as L,
    pricingSub: { tr: "Ücretsiz başla. Ekibin büyüdükçe yükselt.", en: "Start free. Upgrade as your team grows." } as L,
    popular: { tr: "En popüler", en: "Most popular" } as L,
    faqTitle: { tr: "Sıkça sorulanlar", en: "Frequently asked" } as L,
    faqSub: { tr: "Cevabını bulamadın mı? Ekibimize yaz.", en: "Can't find an answer? Reach our team." } as L,
    ctaTitle: { tr: "Ekibinin gerçekten güncelleyeceği pipeline'ı kur", en: "Build a pipeline your team will actually update" } as L,
    ctaSub: { tr: "Anahtarsız demo modda aç, hazır olunca Supabase ve e-posta senkronunu bağla.", en: "Open the keyless demo, then wire Supabase and email sync when you're ready." } as L,
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
              <span className="bg-gradient-to-br from-[oklch(62%_0.15_152)] to-[oklch(52%_0.13_168)] bg-clip-text text-transparent">
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
            <div className="absolute -bottom-8 -right-4 -z-10 h-44 w-44 rounded-full bg-[oklch(62%_0.13_232)]/10 blur-3xl" aria-hidden />
            <ProductPreview />
          </div>
        </div>

        {/* Trusted-by row */}
        <div className="border-y border-border bg-card/50">
          <div className="mx-auto max-w-6xl px-5 py-6">
            <p className="text-center text-[11px] font-medium uppercase tracking-[0.18em] text-muted-foreground">
              {lang === "tr" ? "Modern satış ekipleri tarafından kullanılıyor" : "Used by modern sales teams"}
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
          {[
            { value: "$2.4B+", label: { tr: "yönetilen pipeline", en: "pipeline managed" } as L },
            { value: "3,200+", label: { tr: "satış ekibi", en: "sales teams" } as L },
            { value: "+20%", label: { tr: "ortalama kazanma artışı", en: "avg win-rate lift" } as L },
            { value: "8h", label: { tr: "haftada/temsilci kazanç", en: "saved per rep/wk" } as L },
          ].map((s) => (
            <div key={s.value} className="bg-card px-5 py-8 text-center">
              <p className="font-display text-3xl font-extrabold tracking-tight">{s.value}</p>
              <p className="mt-1.5 text-xs text-muted-foreground">{tt(s.label)}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── INTERACTIVE DEMO ──────────────────────────────────────── */}
      <section id="demo" className="mx-auto max-w-6xl px-5 py-20">
        <div className="grid items-center gap-12 lg:grid-cols-[1fr_1.15fr]">
          <div>
            <p className="label-mono text-primary">{lang === "tr" ? "Canlı pipeline" : "Live pipeline"}</p>
            <h2 className="mt-2 max-w-md font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(sectionCopy.demoTitle)}</h2>
            <p className="mt-3 max-w-md text-muted-foreground">{tt(sectionCopy.demoSub)}</p>
            <div className="mt-6 grid grid-cols-3 gap-3">
              {m.stats.slice(0, 3).map((s) => (
                <div key={s.value} className="rounded-xl border border-border bg-card p-3 shadow-soft">
                  <p className="tnum text-xl font-bold leading-none">{s.value}</p>
                  <p className="mt-1 text-[11px] text-muted-foreground">{t(s.label)}</p>
                </div>
              ))}
            </div>
          </div>
          <PipelineDemo />
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

      {/* ── DEEP-DIVE FEATURE BLOCKS ──────────────────────────────── */}
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
                {/* a small illustrative panel */}
                <div className="rounded-2xl border border-border bg-card p-5 shadow-soft">
                  {idx === 0 && <DeepPipeline />}
                  {idx === 1 && <DeepActivities />}
                  {idx === 2 && <DeepAutomation lang={lang} />}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FORECASTING DEEP-DIVE ─────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="grid items-center gap-12 lg:grid-cols-[1fr_1.1fr]">
          <div>
            <p className="label-mono text-primary">{lang === "tr" ? "Tahmin" : "Forecast"}</p>
            <h2 className="mt-2 max-w-md font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(sectionCopy.forecastTitle)}</h2>
            <p className="mt-3 max-w-md text-muted-foreground">{tt(sectionCopy.forecastSub)}</p>
            <div className="mt-6 space-y-3">
              {stages.map((s) => (
                <div key={s.id} className="flex items-center gap-3">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
                  <span className="w-28 text-sm font-medium">{t(s.label)}</span>
                  <div className="h-2 flex-1 overflow-hidden rounded-full bg-muted">
                    <div className="h-full rounded-full" style={{ width: `${s.prob * 100}%`, background: s.color }} />
                  </div>
                  <span className="tnum w-12 text-right text-[13px] font-semibold text-muted-foreground">{Math.round(s.prob * 100)}%</span>
                </div>
              ))}
            </div>
          </div>
          {/* weighted math card */}
          <div className="rounded-2xl border border-border bg-card p-6 shadow-pop">
            <p className="text-sm font-medium text-muted-foreground">{lang === "tr" ? "Ağırlıklı tahmin nasıl hesaplanır" : "How the weighted forecast adds up"}</p>
            <div className="mt-4 space-y-2.5">
              {[
                { c: "Lumen", stage: { tr: "Teklif", en: "Proposal" } as L, value: 64000, prob: 0.55 },
                { c: "Northwind", stage: { tr: "Müzakere", en: "Negotiation" } as L, value: 41000, prob: 0.8 },
                { c: "Parable", stage: { tr: "Nitelikli", en: "Qualified" } as L, value: 22500, prob: 0.3 },
              ].map((r) => (
                <div key={r.c} className="flex items-center gap-3 rounded-xl border border-border bg-muted/40 p-3 text-[13px]">
                  <span className="w-20 font-semibold">{r.c}</span>
                  <span className="text-muted-foreground">{tt(r.stage)}</span>
                  <span className="tnum ml-auto text-muted-foreground">{formatMoney(r.value)}</span>
                  <span className="tnum text-muted-foreground">× {Math.round(r.prob * 100)}%</span>
                  <span className="tnum w-16 text-right font-bold text-primary">{formatMoney(Math.round(r.value * r.prob))}</span>
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center justify-between rounded-xl bg-primary/[0.06] px-4 py-3">
              <span className="text-sm font-semibold">{lang === "tr" ? "Ağırlıklı tahmin" : "Weighted forecast"}</span>
              <span className="tnum text-lg font-bold text-primary">{formatMoney(64000 * 0.55 + 41000 * 0.8 + 22500 * 0.3)}</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── USE CASES ─────────────────────────────────────────────── */}
      <section className="border-y border-border bg-muted/30">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <div className="mx-auto max-w-2xl text-center">
            <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(sectionCopy.useCasesTitle)}</h2>
            <p className="mt-3 text-muted-foreground">{tt(sectionCopy.useCasesSub)}</p>
          </div>
          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {USE_CASES.map((u) => (
              <div key={tt(u.title)} className="rounded-2xl border border-border bg-card p-6 shadow-soft">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-primary/10 text-primary">
                  <Icon name={u.icon} className="h-5 w-5" />
                </span>
                <h3 className="mt-4 font-semibold tracking-tight">{tt(u.title)}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{tt(u.body)}</p>
              </div>
            ))}
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
                  <th className="px-5 py-4 text-center font-medium text-muted-foreground">{lang === "tr" ? "Tablolar" : "Spreadsheets"}</th>
                  <th className="px-5 py-4 text-center font-medium text-muted-foreground">{lang === "tr" ? "Şişkin CRM" : "Bloated CRM"}</th>
                  <th className="bg-primary/[0.04] px-5 py-4 text-center">
                    <span className="inline-flex items-center gap-1.5 font-semibold text-primary">
                      <Kanban className="h-4 w-4" />
                      {appConfig.name}
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {COMPARE.map((row, i) => (
                  <tr key={tt(row.feature)} className={cn("border-b border-border/60 last:border-0", i % 2 === 1 && "bg-muted/20")}>
                    <td className="px-5 py-3.5 font-medium">{tt(row.feature)}</td>
                    <CompareCell value={row.sheets} lang={lang} />
                    <CompareCell value={row.bloated} lang={lang} />
                    <CompareCell value={row.pipely} lang={lang} highlight />
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ──────────────────────────────────────────── */}
      <section className="border-y border-border bg-muted/30">
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
                  <Avatar initials={tm.initials} color={tm.color} size={40} />
                  <div className="min-w-0 flex-1">
                    <figcaption className="text-sm font-semibold leading-tight">{tm.name}</figcaption>
                    <p className="truncate text-xs text-muted-foreground">{tt(tm.role)}</p>
                  </div>
                  <span className="rounded-full bg-success/10 px-2 py-1 text-[11px] font-semibold text-success">{tt(tm.metric)}</span>
                </div>
              </figure>
            ))}
          </div>
          <div className="mt-8 flex items-center justify-center gap-1.5 text-sm text-muted-foreground">
            {Array.from({ length: 5 }).map((_, i) => (
              <Star key={i} className="h-4 w-4 fill-warning text-warning" />
            ))}
            <span className="ml-2">{lang === "tr" ? "4.9/5 · 3,200+ ekip" : "4.9/5 · 3,200+ teams"}</span>
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
              <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-[11px] font-semibold text-success">
                <span className="h-1.5 w-1.5 rounded-full bg-success" />
                {lang === "tr" ? "Hazır" : "Ready"}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* ── DEVELOPER / API ───────────────────────────────────────── */}
      <section className="border-t border-border">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <div className="grid items-center gap-10 lg:grid-cols-2">
            <div>
              <p className="label-mono text-primary">{lang === "tr" ? "API" : "API"}</p>
              <h2 className="mt-2 max-w-md font-display text-3xl font-bold tracking-tight sm:text-4xl">
                {lang === "tr" ? "Geliştiriciler için kuruldu" : "Built for developers"}
              </h2>
              <p className="mt-3 max-w-md text-muted-foreground">
                {lang === "tr"
                  ? "Temiz bir REST API, imzalı webhook'lar ve örnek-temelli dokümanlar. Deal'leri programatik oluştur, aşama değişimlerini dinle."
                  : "A clean REST API, signed webhooks, and example-first docs. Create deals programmatically and listen for stage changes."}
              </p>
              <ul className="mt-6 space-y-2.5">
                {[
                  { tr: "REST + imzalı webhook'lar", en: "REST + signed webhooks" },
                  { tr: "TypeScript & Python SDK'ları", en: "TypeScript & Python SDKs" },
                  { tr: "Zapier & Make bağlayıcıları", en: "Zapier & Make connectors" },
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
            <div className="overflow-hidden rounded-2xl border border-border bg-[oklch(22%_0.02_160)] shadow-pop">
              <div className="flex items-center gap-1.5 border-b border-white/10 px-4 py-3">
                <span className="h-2.5 w-2.5 rounded-full bg-destructive/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-warning/70" />
                <span className="h-2.5 w-2.5 rounded-full bg-success/70" />
                <span className="ml-2 font-mono text-[11px] text-white/40">create-deal.ts</span>
              </div>
              <pre className="overflow-x-auto p-4 font-mono text-[12.5px] leading-relaxed text-white/80">
{`const deal = await pipely.deals.create({
  title: "Platform license",
  company: "Northwind Co",
  value: 48000,
  stage: "qualified",
  owner: "alex@pipely.app",
});

// react to a deal reaching "Won"
pipely.on("deal.won", (e) => {
  slack.notify("#wins", e.deal.title);
});`}
              </pre>
            </div>
          </div>
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
                  <span className="font-display text-4xl font-extrabold tracking-tight">{tier.price}</span>
                  {tier.period && <span className="text-sm text-muted-foreground">{t(tier.period)}</span>}
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
            <Kanban className="h-3.5 w-3.5 text-primary" />
            <span>{lang === "tr" ? "5 aşama · canlı pipeline" : "5 stages · live pipeline"}</span>
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
            <Link
              href="/login"
              className="inline-flex h-12 items-center justify-center rounded-xl border border-border bg-card px-7 text-[15px] font-semibold text-foreground shadow-pill transition-colors hover:bg-muted"
            >
              {lang === "tr" ? "Canlı demoyu gör" : "See the live demo"}
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}

/* ── Deep-dive illustrative panels (inline SVG / CSS only) ─────────────────── */
function DeepPipeline() {
  const { t } = useLang();
  const cols = stages.slice(1, 4); // qualified, proposal, negotiation
  const sample: Record<string, { c: string; v: number; o: string }[]> = {
    qualified: [{ c: "Parable", v: 22500, o: "r2" }, { c: "Meridian", v: 52000, o: "r2" }],
    proposal: [{ c: "Lumen", v: 64000, o: "r3" }],
    negotiation: [{ c: "Northwind", v: 41000, o: "r1" }],
  };
  return (
    <div className="grid grid-cols-3 gap-2.5">
      {cols.map((st) => (
        <div key={st.id} className="rounded-xl border border-border bg-muted/40 p-2">
          <div className="mb-2 flex items-center gap-1.5 px-0.5">
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: st.color }} />
            <span className="truncate text-[10px] font-semibold text-muted-foreground">{t(st.label)}</span>
          </div>
          <div className="space-y-1.5">
            {sample[st.id].map((d, i) => {
              const rep = repById[d.o];
              return (
                <div key={i} className="rounded-lg border border-border bg-card p-2 shadow-pill">
                  <div className="flex items-center gap-1">
                    <GripVertical className="h-2.5 w-2.5 text-muted-foreground/40" />
                    <p className="truncate text-[10.5px] font-semibold">{d.c}</p>
                  </div>
                  <div className="mt-1.5 flex items-center justify-between">
                    <span className="tnum text-[10px] font-semibold">{formatMoney(d.v)}</span>
                    <Avatar initials={rep.initials} color={rep.color} size={15} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}

function DeepActivities() {
  const { t, lang } = useLang();
  const items: { I: typeof PhoneCall; title: L; sub: string }[] = [
    { I: PhoneCall, title: { tr: "Keşif görüşmesi", en: "Discovery call" }, sub: "Northwind · 14:00" },
    { I: Mail, title: { tr: "Teklif gönderildi", en: "Proposal sent" }, sub: "Lumen · " + (lang === "tr" ? "az önce" : "just now") },
    { I: TrendingUp, title: { tr: "Demo planlandı", en: "Demo scheduled" }, sub: "Formwork · " + (lang === "tr" ? "yarın" : "tomorrow") },
  ];
  return (
    <div className="space-y-2.5">
      {items.map((it, i) => (
        <div key={i} className="flex items-center gap-3 rounded-xl border border-border bg-muted/40 p-3">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary/10 text-primary">
            <it.I className="h-4 w-4" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="truncate text-[13px] font-semibold leading-tight">{t(it.title)}</p>
            <p className="tnum truncate text-[11px] text-muted-foreground">{it.sub}</p>
          </div>
          <span className="grid h-5 w-5 place-items-center rounded-full bg-success/12 text-success">
            <Check className="h-3 w-3" strokeWidth={3} />
          </span>
        </div>
      ))}
    </div>
  );
}

function DeepAutomation({ lang }: { lang: "tr" | "en" }) {
  const rules: { c: string; l: string; v: string }[] = [
    { c: "var(--stage-won)", l: lang === "tr" ? "Deal kazanıldı → Slack'e bildir" : "Deal won → notify Slack", v: "ON" },
    { c: "var(--stage-proposal)", l: lang === "tr" ? "Teklif aşaması → takip görevi" : "Proposal stage → follow-up task", v: "ON" },
    { c: "var(--stage-lead)", l: lang === "tr" ? "Yeni lead → zenginleştir" : "New lead → enrich contact", v: "ON" },
  ];
  return (
    <div className="space-y-3">
      {rules.map((r) => (
        <div key={r.l} className="flex items-center gap-3 rounded-xl border border-border bg-muted/40 p-3">
          <Workflow className="h-4 w-4 shrink-0" style={{ color: r.c }} />
          <span className="flex-1 text-[12.5px]">{r.l}</span>
          <span className="rounded-full bg-success/10 px-2 py-0.5 text-[10px] font-semibold text-success">{r.v}</span>
        </div>
      ))}
    </div>
  );
}

function IntegrationGlyph({ glyph }: { glyph: "db" | "mail" | "enrich" | "slack" }) {
  const color =
    glyph === "db" ? "var(--color-success)" :
    glyph === "mail" ? "var(--seg-2)" :
    glyph === "enrich" ? "var(--seg-3)" : "var(--seg-4)";
  return (
    <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl" style={{ background: color }}>
      <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="#fff" strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round">
        {glyph === "db" && <path d="M4 6 c0 -1.7 3.6 -3 8 -3 s8 1.3 8 3 v12 c0 1.7 -3.6 3 -8 3 s-8 -1.3 -8 -3 z M4 6 c0 1.7 3.6 3 8 3 s8 -1.3 8 -3 M4 12 c0 1.7 3.6 3 8 3 s8 -1.3 8 -3" />}
        {glyph === "mail" && <path d="M3 6 h18 v12 H3 Z M3 7 l9 7 9 -7" />}
        {glyph === "enrich" && <path d="M11 4 a7 7 0 1 0 0 14 a7 7 0 0 0 0 -14 M21 21 l-5 -5" />}
        {glyph === "slack" && <path d="M9 4 v8 M5 8 h8 M15 20 v-8 M11 16 h8 M4 15 h8 v-2 M20 9 h-8 v2" />}
      </svg>
    </span>
  );
}

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
