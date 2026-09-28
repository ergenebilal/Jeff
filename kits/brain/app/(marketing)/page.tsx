"use client";

import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  Sparkles,
  Quote,
  ShieldCheck,
  Plug,
  Search,
  RefreshCw,
  X,
  Minus,
  Star,
  Zap,
  Lock,
  Layers,
  ScanSearch,
  Headphones,
  Briefcase,
  Code2,
  GraduationCap,
  MessageSquare,
  Puzzle,
} from "lucide-react";
import appConfig from "@/app.config";
import { Icon } from "@/components/ui/icon";
import { AskBar } from "@/components/app/ask-bar";
import { SourceIcon, SOURCE_LABEL, type SourceKey } from "@/components/app/source-icon";
import { HeroPreview } from "@/components/marketing/hero-preview";
import { CompanyMark, InitialAvatar } from "@/components/marketing/marks";
import { useLang } from "@/components/i18n/language-provider";
import { cn } from "@/lib/utils";
import type { L } from "@/lib/i18n/config";

const COMPANIES = ["Northwind", "Parable", "Formwork", "Cedarworks", "Lumen", "Brightline", "Meridian", "Harvest"];
const SOURCES: SourceKey[] = ["notion", "drive", "slack", "confluence", "github", "web"];

/* ── Hero stat band — at-a-glance proof. ─────────────────────────────────────── */
const HERO_STATS: { value: string; label: L }[] = [
  { value: "8,420", label: { tr: "indekslenmiş belge", en: "indexed documents" } },
  { value: "73%", label: { tr: "destek yönlendirme", en: "support deflection" } },
  { value: "~1.4s", label: { tr: "ortalama yanıt", en: "avg answer time" } },
  { value: "100%", label: { tr: "kaynaklı yanıt", en: "cited answers" } },
];

/* ── Connected-sources showcase. ─────────────────────────────────────────────── */
const SOURCE_TILES: { source: SourceKey; blurb: L; docs: string }[] = [
  { source: "notion", blurb: { tr: "Sayfalar, wiki ve veritabanları", en: "Pages, wikis and databases" }, docs: "3,180" },
  { source: "drive", blurb: { tr: "Docs, Sheets ve Slides", en: "Docs, Sheets and Slides" }, docs: "2,240" },
  { source: "slack", blurb: { tr: "Kanal bilgisi ve sabitlenenler", en: "Channel knowledge & pins" }, docs: "1,610" },
  { source: "confluence", blurb: { tr: "Alanlar ve runbook'lar", en: "Spaces and runbooks" }, docs: "980" },
  { source: "github", blurb: { tr: "READMEs, handbook ve PR'lar", en: "READMEs, handbooks and PRs" }, docs: "320" },
  { source: "web", blurb: { tr: "Genel siteler ve yardım merkezleri", en: "Public sites and help centers" }, docs: "90" },
];

/* ── Deep-dive feature blocks (alternating). ─────────────────────────────────── */
const DEEP_DIVE: { eyebrow: L; title: L; body: L; points: L[]; panel: "retrieval" | "verify" | "channels"; reverse?: boolean }[] = [
  {
    eyebrow: { tr: "Erişim", en: "Retrieval" },
    title: { tr: "Doğru pasajı bulur, on sonucu değil", en: "Finds the right passage, not ten results" },
    body: { tr: "Brain her belgeyi anlam vektörlerine böler, soruna en yakın bölümleri çeker ve tek bir net yanıta sentezler. İzinler kaynağından miras alınır — kimse görmemesi gereken bir şeyi göremez.", en: "Brain splits every doc into meaning vectors, pulls the passages closest to your question, and synthesizes them into one clear answer. Permissions are inherited from the source — nobody sees what they shouldn't." },
    points: [
      { tr: "Anlamsal arama + yeniden sıralama", en: "Semantic search with re-ranking" },
      { tr: "Kaynak-düzeyinde izin mirası", en: "Source-level permission inheritance" },
      { tr: "Çok-kaynaklı tek yanıt", en: "One answer across many sources" },
    ],
    panel: "retrieval",
  },
  {
    eyebrow: { tr: "Güven", en: "Trust" },
    title: { tr: "Eskiyen bilgiyi yüzeye çıkarır", en: "Surfaces knowledge before it goes stale" },
    body: { tr: "Her kart bir tazelik puanı taşır. Kaynak değiştiğinde ya da kart düşük oy aldığında doğrulama kuyruğuna düşer ve doğru uzmana yönlendirilir. Bilgin asla sessizce eskimez.", en: "Every card carries a freshness score. When a source changes or a card gets downvoted, it drops into a verification queue and routes to the right expert. Your knowledge never silently rots." },
    points: [
      { tr: "Otomatik tazelik puanlaması", en: "Automatic freshness scoring" },
      { tr: "Uzmana yönlendirilen doğrulama kuyruğu", en: "Expert-routed verification queue" },
      { tr: "Düşük oy → yeniden inceleme", en: "Downvote → re-review loop" },
    ],
    panel: "verify",
    reverse: true,
  },
  {
    eyebrow: { tr: "Erişilebilirlik", en: "Everywhere" },
    title: { tr: "Bağlamını terk etmeden sor", en: "Ask without leaving your context" },
    body: { tr: "Brain'e web panelinden, Slack'ten /brain komutuyla ya da herhangi bir sekmede tarayıcı eklentisinden sor. Cevap, kaynaklarıyla birlikte sana gelir — sen onu aramaya gitmezsin.", en: "Ask Brain from the web panel, from Slack with /brain, or from any tab via the browser extension. The answer comes to you with its sources — you don't go hunting for it." },
    points: [
      { tr: "Slack uygulaması & /brain komutu", en: "Slack app & /brain command" },
      { tr: "Tarayıcı eklentisi (her sekme)", en: "Browser extension (any tab)" },
      { tr: "REST API & webhook'lar", en: "REST API & webhooks" },
    ],
    panel: "channels",
  },
];

/* ── Use-case / persona strip. ───────────────────────────────────────────────── */
const PERSONAS: { icon: typeof Headphones; title: L; body: L; metric: L }[] = [
  { icon: Headphones, title: { tr: "Destek", en: "Support" }, body: { tr: "Tekrarlı soruları kendi kendine yanıtla, talep hacmini düşür.", en: "Self-resolve repeat questions and cut ticket volume." }, metric: { tr: "Talepler -34%", en: "−34% tickets" } },
  { icon: Briefcase, title: { tr: "Satış", en: "Sales" }, body: { tr: "Fiyat, güvenlik ve rakip sorularına anında doğru yanıt.", en: "Instant, accurate answers on pricing, security and competitors." }, metric: { tr: "2× daha hızlı yanıt", en: "2× faster replies" } },
  { icon: Code2, title: { tr: "Mühendislik", en: "Engineering" }, body: { tr: "Runbook'lar, mimari kararlar ve on-call bilgisi tek soruda.", en: "Runbooks, architecture decisions and on-call know-how in one ask." }, metric: { tr: "Günde 40 dk kazanç", en: "40 min/day saved" } },
  { icon: GraduationCap, title: { tr: "Onboarding", en: "Onboarding" }, body: { tr: "Yeni başlayanlar sana değil Brain'e sorar — doğru cevapla.", en: "New hires ask Brain instead of you — with the right answer." }, metric: { tr: "Onboarding 2× hızlı", en: "Onboarding 2× faster" } },
];

/* ── Where you can ask Brain (channels strip). ───────────────────────────────── */
const CHANNELS: { icon: typeof MessageSquare; name: L; body: L }[] = [
  { icon: Search, name: { tr: "Web paneli", en: "Web panel" }, body: { tr: "Tam cevap motoru, geçmiş ve filtreler.", en: "The full answer engine, history and filters." } },
  { icon: MessageSquare, name: { tr: "Slack uygulaması", en: "Slack app" }, body: { tr: "/brain ile sor; yanıt kanalda kaynaklarıyla gelir.", en: "Ask with /brain; the answer lands in-channel with sources." } },
  { icon: Puzzle, name: { tr: "Tarayıcı eklentisi", en: "Browser extension" }, body: { tr: "Her sekmede yanında; metni seç, sor.", en: "With you on every tab; select text and ask." } },
];

export default function LandingPage() {
  const { t, lang } = useLang();
  const m = appConfig.marketing;
  const tt = (v: { tr: string; en: string }) => v[lang];

  const copy = {
    featuresTitle: { tr: "Bir cevap motoru için gereken her şey", en: "Everything an answer engine needs" },
    featuresSub: { tr: "Bağla, sor, doğrula. Brain dağınık bilgini çalışır hâle getirir.", en: "Connect, ask, verify. Brain turns scattered knowledge into something that works." },
    howTitle: { tr: "Nasıl çalışır", en: "How it works" },
    howSub: { tr: "Kaynakları bağla, sor, kaynaklı cevap al ve taze tut.", en: "Connect docs, ask, get a cited answer, keep it fresh." },
    demoTitle: { tr: "Kendin dene", en: "Try it yourself" },
    demoSub: { tr: "Bir soru seç ya da yaz — yanıt kaynaklarıyla birlikte akar.", en: "Pick a question or type one — the answer streams in with its sources." },
    sourcesTitle: { tr: "Bilginin yaşadığı her yere bağlan", en: "Connect everywhere knowledge lives" },
    sourcesSub: { tr: "Brain altı konnektörden indeksler ve hepsini güncel tutar. Yeni konnektörler düzenli ekleniyor.", en: "Brain indexes from six connectors and keeps them all current. New connectors land regularly." },
    deepTitle: { tr: "Yüzeyin altında ne var", en: "What's under the surface" },
    deepSub: { tr: "Erişim, güven ve erişilebilirlik — bir cevap motorunu güvenilir kılan üç katman.", en: "Retrieval, trust and reach — the three layers that make an answer engine reliable." },
    personasTitle: { tr: "Her ekip için bir cevap", en: "An answer for every team" },
    personasSub: { tr: "Destekten mühendisliğe, Brain günlük işin bir parçası olur.", en: "From support to engineering, Brain becomes part of the daily flow." },
    channelsTitle: { tr: "Brain'e nereden sorarsın", en: "Where you ask Brain" },
    channelsSub: { tr: "Bağlamını terk etme — cevap sana gelir.", en: "Never leave your context — the answer comes to you." },
    trustTitle: { tr: "Her cevap, kaynağına kadar izlenebilir", en: "Every answer traces back to its source" },
    trustSub: { tr: "Genel bir sohbet botu değil. Brain yalnızca senin belgelerinden konuşur ve her iddiayı kanıta bağlar.", en: "Not a generic chatbot. Brain only speaks from your docs and ties every claim to evidence." },
    compTitle: { tr: "Brain'i bir karşılaştır", en: "See the difference" },
    compSub: { tr: "Her yere bakmak, genel bir bot ve Brain.", en: "Searching everywhere, a generic chatbot, and Brain." },
    testimonialsTitle: { tr: "Ekipler Brain'le neyi kazanıyor", en: "What teams get back with Brain" },
    testimonialsSub: { tr: "Bilgi-yoğun ekiplerden gerçek sonuçlar.", en: "Real outcomes from knowledge-heavy teams." },
    pricingTitle: { tr: "Koltuk başına basit fiyatlandırma", en: "Simple pricing by seat" },
    pricingSub: { tr: "Ücretsiz başla. Ekibin büyüdükçe ölçekle.", en: "Start free. Scale as your team grows." },
    popular: { tr: "En popüler", en: "Most popular" },
    faqTitle: { tr: "Sık sorulanlar", en: "Frequently asked" },
    faqSub: { tr: "Cevabını bulamadın mı? Ekibimize yaz.", en: "Can't find it? Reach our team." },
    ctaTitle: { tr: "Şirketinin bilgisini bir soruya indir", en: "Make your company's knowledge one question away" },
    ctaSub: { tr: "Demo modda anında çalışır. Kaynaklarını bağlamak için Claude Code'da \"bu projeyi kur\" de.", en: "Runs instantly in demo mode. To connect your sources, open Claude Code and say \"set up this project.\"" },
  };

  /* citation/trust deep-dive bullets */
  const trustPoints = [
    { icon: ShieldCheck, title: { tr: "Sıfır uydurma", en: "Zero hallucination" }, body: { tr: "Kaynak yoksa Brain “bilmiyorum” der — uydurmaz.", en: "If there's no source, Brain says it doesn't know — it won't invent." } },
    { icon: Quote, title: { tr: "Satır içi alıntılar", en: "Inline citations" }, body: { tr: "Her cümle, doğrudan kaynak belgeye numaralı bir bağlantı taşır.", en: "Every sentence carries a numbered link straight to the source doc." } },
    { icon: RefreshCw, title: { tr: "Tazelik puanı", en: "Freshness scoring" }, body: { tr: "Eskiyen içerik işaretlenir, doğrulama kuyruğuna düşer.", en: "Stale content gets flagged and routed to a verification queue." } },
  ];

  /* comparison rows */
  const compRows = [
    { label: { tr: "Tek bir cevap, on sonuç değil", en: "One answer, not ten results" }, a: false, b: "~", c: true },
    { label: { tr: "Kaynak gösterir", en: "Cites its sources" }, a: false, b: false, c: true },
    { label: { tr: "İzinlere saygı duyar", en: "Respects permissions" }, a: true, b: false, c: true },
    { label: { tr: "Bilgiyi güncel tutar", en: "Keeps knowledge fresh" }, a: false, b: false, c: true },
    { label: { tr: "Slack & tarayıcıda çalışır", en: "Works in Slack & browser" }, a: "~", b: "~", c: true },
    { label: { tr: "Boşlukları yüzeye çıkarır", en: "Surfaces knowledge gaps" }, a: false, b: false, c: true },
  ];

  function CompCell({ v }: { v: boolean | string }) {
    if (v === true) return <Check className="mx-auto h-4 w-4 text-success" />;
    if (v === false) return <X className="mx-auto h-4 w-4 text-muted-foreground/50" />;
    return <Minus className="mx-auto h-4 w-4 text-warning-foreground" />;
  }

  return (
    <>
      {/* ── Hero ─────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10" style={{ background: "var(--grad-hero)" }} />
        <span className="blob -left-10 top-10 -z-10 h-72 w-72 bg-primary/25 drift" aria-hidden />
        <span className="blob -right-10 top-32 -z-10 h-64 w-64 drift" aria-hidden style={{ background: "color-mix(in oklch, var(--seg-2) 30%, transparent)", animationDelay: "2s" }} />

        <div className="mx-auto grid max-w-6xl items-center gap-12 px-5 py-16 sm:py-20 lg:grid-cols-[1.05fr_0.95fr] lg:py-24">
          <div className="stagger">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground shadow-soft">
              <span className="h-1.5 w-1.5 rounded-full bg-primary pulse-dot" />
              {t(m.badge)}
            </span>
            <h1 className="mt-5 max-w-xl font-display text-[40px] font-extrabold leading-[1.04] tracking-tight sm:text-[54px]">
              {t(m.heroTitle)}{" "}
              <span className="bg-gradient-to-br from-primary to-[oklch(48%_0.2_302)] bg-clip-text text-transparent">{t(m.heroAccent)}</span>
            </h1>
            <p className="mt-5 max-w-lg text-[17px] leading-relaxed text-muted-foreground">{t(m.heroSubtitle)}</p>

            <ul className="mt-6 space-y-2.5">
              {m.heroBenefits.map((b) => (
                <li key={t(b)} className="flex items-center gap-2.5 text-[15px] font-medium">
                  <span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-success/15 text-success">
                    <Check className="h-3 w-3" strokeWidth={3} />
                  </span>
                  {t(b)}
                </li>
              ))}
            </ul>

            <div className="mt-8 flex flex-col items-start gap-3 sm:flex-row sm:items-center">
              <Link
                href="/signup"
                className="inline-flex h-12 items-center gap-2 rounded-lg bg-primary px-6 text-[15px] font-semibold text-primary-foreground shadow-sm shadow-primary/20 transition-opacity hover:opacity-90"
              >
                {t(m.heroCtaPrimary)} <ArrowRight className="h-4 w-4" />
              </Link>
              <a
                href="#demo"
                className="inline-flex h-12 items-center gap-2 rounded-lg border border-border bg-card px-6 text-[15px] font-semibold text-foreground transition-colors hover:bg-muted"
              >
                <Sparkles className="h-4 w-4 text-primary" /> {t(m.heroCtaSecondary)}
              </a>
            </div>

            <p className="mt-5 text-[13px] text-muted-foreground">
              {lang === "tr" ? "Kredi kartı yok · Demo modda anında çalışır" : "No credit card · Runs instantly in demo mode"}
            </p>
          </div>

          {/* floating product preview */}
          <div className="relative animate-float-up">
            <span className="absolute -right-6 -top-6 -z-10 h-40 w-40 rounded-full bg-primary/10 blur-2xl" aria-hidden />
            <HeroPreview />
            {/* small floating source chips */}
            <div className="mt-3 flex flex-wrap justify-center gap-2">
              {SOURCES.slice(0, 5).map((s) => (
                <span key={s} className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1 text-[11.5px] font-medium text-muted-foreground shadow-pill">
                  <SourceIcon source={s} size={14} className="rounded-[4px]" />
                  {SOURCE_LABEL[s]}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Stat band ────────────────────────────────────────────────── */}
      <section className="mx-auto -mt-2 max-w-6xl px-5">
        <div className="grid grid-cols-2 gap-px overflow-hidden rounded-2xl border border-border bg-border shadow-soft sm:grid-cols-4">
          {HERO_STATS.map((s) => (
            <div key={s.value} className="bg-card px-5 py-7 text-center">
              <p className="font-display text-3xl font-extrabold tracking-tight">{s.value}</p>
              <p className="mt-1.5 text-xs text-muted-foreground">{tt(s.label)}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Trusted by ───────────────────────────────────────────────── */}
      <section className="mt-12 border-y border-border bg-card/60">
        <div className="mx-auto max-w-6xl px-5 py-8">
          <p className="text-center label-mono text-muted-foreground">
            {lang === "tr" ? "Bilgi-yoğun ekipler tarafından kullanılıyor" : "Trusted by knowledge-heavy teams"}
          </p>
          <div className="mt-5 flex flex-wrap items-center justify-center gap-x-10 gap-y-5">
            {COMPANIES.map((c) => (
              <CompanyMark key={c} name={c} />
            ))}
          </div>
        </div>
      </section>

      {/* ── Interactive demo ─────────────────────────────────────────── */}
      <section id="demo" className="mx-auto max-w-3xl px-5 py-20">
        <div className="text-center">
          <span className="label-mono text-primary">{lang === "tr" ? "Canlı demo" : "Live demo"}</span>
          <h2 className="mt-2 font-display text-3xl font-bold tracking-tight">{tt(copy.demoTitle)}</h2>
          <p className="mx-auto mt-3 max-w-xl text-muted-foreground">{tt(copy.demoSub)}</p>
        </div>
        <div className="mt-8">
          <AskBar />
        </div>
        <p className="mt-3 text-center text-xs text-muted-foreground">
          {lang === "tr"
            ? "Bu demo, örnek bir bilgi tabanına karşı çalışır — gerçek anahtar gerekmez."
            : "This demo runs against a sample knowledge base — no real keys required."}
        </p>
      </section>

      {/* ── Features grid ────────────────────────────────────────────── */}
      <section id="features" className="border-t border-border bg-muted/30">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <div className="max-w-2xl">
            <h2 className="font-display text-3xl font-bold tracking-tight">{tt(copy.featuresTitle)}</h2>
            <p className="mt-3 text-muted-foreground">{tt(copy.featuresSub)}</p>
          </div>
          <div className="mt-10 grid gap-5 stagger sm:grid-cols-2 lg:grid-cols-3">
            {m.features.map((f) => (
              <div key={tt(f.title)} className="rounded-2xl border border-border bg-card p-6 shadow-soft transition-shadow hover:shadow-pop">
                <span className="grid h-11 w-11 place-items-center rounded-xl bg-primary/10 text-primary">
                  <Icon name={f.icon} className="h-5 w-5" />
                </span>
                <h3 className="mt-4 font-semibold">{t(f.title)}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{t(f.body)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Connected sources showcase ───────────────────────────────── */}
      <section id="sources" className="mx-auto max-w-6xl px-5 py-20">
        <div className="grid items-start gap-12 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <span className="label-mono text-primary">{lang === "tr" ? "Konnektörler" : "Connectors"}</span>
            <h2 className="mt-2 font-display text-3xl font-bold tracking-tight">{tt(copy.sourcesTitle)}</h2>
            <p className="mt-3 max-w-md text-muted-foreground">{tt(copy.sourcesSub)}</p>
            <div className="mt-7 space-y-3">
              <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-3.5 shadow-soft">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
                  <Plug className="h-[18px] w-[18px]" />
                </span>
                <p className="text-sm">
                  <span className="font-semibold">{lang === "tr" ? "Tek tıkla yetkilendir." : "Authorize in one click."}</span>{" "}
                  <span className="text-muted-foreground">{lang === "tr" ? "Brain güvenli indeksler, izinlere saygı duyar." : "Brain indexes securely and respects permissions."}</span>
                </p>
              </div>
              <div className="flex items-center gap-3 rounded-xl border border-border bg-card p-3.5 shadow-soft">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-success/10 text-success">
                  <RefreshCw className="h-[18px] w-[18px]" />
                </span>
                <p className="text-sm">
                  <span className="font-semibold">{lang === "tr" ? "Sürekli senkron." : "Always in sync."}</span>{" "}
                  <span className="text-muted-foreground">{lang === "tr" ? "Kaynak değişince yeniden indekslenir." : "Re-indexes whenever a source changes."}</span>
                </p>
              </div>
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            {SOURCE_TILES.map((tile) => (
              <div key={tile.source} className="group flex items-start gap-3.5 rounded-2xl border border-border bg-card p-5 shadow-soft transition-shadow hover:shadow-pop">
                <SourceIcon source={tile.source} size={40} className="rounded-xl" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-semibold tracking-tight">{SOURCE_LABEL[tile.source]}</p>
                    <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-1.5 py-0.5 text-[10px] font-semibold text-success">
                      <span className="h-1.5 w-1.5 rounded-full bg-success" /> {lang === "tr" ? "Bağlı" : "Connected"}
                    </span>
                  </div>
                  <p className="mt-0.5 text-[13px] leading-snug text-muted-foreground">{tt(tile.blurb)}</p>
                  <p className="mt-2 tnum text-[11px] text-muted-foreground">
                    {tile.docs} {lang === "tr" ? "belge indekslendi" : "docs indexed"}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ─────────────────────────────────────────────── */}
      <section id="how" className="border-y border-border bg-muted/30">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <div className="max-w-2xl">
            <h2 className="font-display text-3xl font-bold tracking-tight">{tt(copy.howTitle)}</h2>
            <p className="mt-3 text-muted-foreground">{tt(copy.howSub)}</p>
          </div>
          <div className="relative mt-10 grid gap-5 md:grid-cols-4">
            {/* connecting line */}
            <div className="pointer-events-none absolute left-0 right-0 top-[34px] hidden h-px bg-border md:block" aria-hidden />
            {m.how.map((s, i) => (
              <div key={tt(s.title)} className="relative rounded-2xl border border-border bg-card p-6 shadow-soft">
                <div className="flex items-center gap-3">
                  <span className="relative z-10 grid h-9 w-9 place-items-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
                    {i + 1}
                  </span>
                  <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary/10 text-primary">
                    <Icon name={s.icon} className="h-[18px] w-[18px]" />
                  </span>
                </div>
                <h3 className="mt-4 font-semibold">{t(s.title)}</h3>
                <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{t(s.body)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Deep-dive feature blocks ─────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="max-w-2xl">
          <h2 className="font-display text-3xl font-bold tracking-tight">{tt(copy.deepTitle)}</h2>
          <p className="mt-3 text-muted-foreground">{tt(copy.deepSub)}</p>
        </div>
        <div className="mt-14 space-y-16">
          {DEEP_DIVE.map((d) => (
            <div
              key={tt(d.title)}
              className={cn("grid items-center gap-10 lg:grid-cols-2", d.reverse && "lg:[&>*:first-child]:order-2")}
            >
              <div>
                <span className="label-mono text-primary">{tt(d.eyebrow)}</span>
                <h3 className="mt-2 max-w-md font-display text-2xl font-bold tracking-tight sm:text-[28px]">{tt(d.title)}</h3>
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

              {/* illustrative panel */}
              <div className="rounded-2xl border border-border bg-card p-5 shadow-pop">
                <DeepPanel panel={d.panel} lang={lang} />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Personas / use-cases strip ───────────────────────────────── */}
      <section className="border-y border-border bg-muted/30">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <div className="max-w-2xl">
            <h2 className="font-display text-3xl font-bold tracking-tight">{tt(copy.personasTitle)}</h2>
            <p className="mt-3 text-muted-foreground">{tt(copy.personasSub)}</p>
          </div>
          <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {PERSONAS.map((p) => {
              const I = p.icon;
              return (
                <div key={tt(p.title)} className="flex flex-col rounded-2xl border border-border bg-card p-6 shadow-soft">
                  <span className="grid h-11 w-11 place-items-center rounded-xl bg-primary/10 text-primary">
                    <I className="h-5 w-5" />
                  </span>
                  <h3 className="mt-4 font-semibold tracking-tight">{tt(p.title)}</h3>
                  <p className="mt-1.5 flex-1 text-sm leading-relaxed text-muted-foreground">{tt(p.body)}</p>
                  <span className="mt-4 inline-flex w-fit items-center gap-1 rounded-full bg-success/10 px-2.5 py-0.5 text-[12px] font-semibold text-success">
                    {tt(p.metric)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Channels strip ───────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="grid items-center gap-12 lg:grid-cols-[1fr_1.1fr]">
          <div>
            <span className="label-mono text-primary">{lang === "tr" ? "Her yerde" : "Everywhere"}</span>
            <h2 className="mt-2 font-display text-3xl font-bold tracking-tight">{tt(copy.channelsTitle)}</h2>
            <p className="mt-3 max-w-md text-muted-foreground">{tt(copy.channelsSub)}</p>
            <div className="mt-7 space-y-4">
              {CHANNELS.map((c) => {
                const I = c.icon;
                return (
                  <div key={tt(c.name)} className="flex items-start gap-3.5">
                    <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
                      <I className="h-5 w-5" />
                    </span>
                    <div>
                      <h3 className="font-semibold">{tt(c.name)}</h3>
                      <p className="mt-0.5 text-sm leading-relaxed text-muted-foreground">{tt(c.body)}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* a mock Slack thread answer */}
          <div className="rounded-2xl border border-border bg-card p-5 shadow-pop">
            <div className="flex items-center gap-2 border-b border-border pb-3">
              <span className="grid h-7 w-7 place-items-center rounded-md" style={{ background: "var(--color-src-slack)" }}>
                <SourceIcon source="slack" size={20} className="rounded-md" />
              </span>
              <span className="text-[13px] font-semibold">#ask-anything</span>
              <span className="ml-auto label-mono text-muted-foreground">{lang === "tr" ? "canlı" : "live"}</span>
            </div>
            <div className="mt-3.5 space-y-3.5">
              <div className="flex items-start gap-2.5">
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-muted text-[11px] font-bold text-muted-foreground">MG</span>
                <div className="min-w-0">
                  <p className="text-[12px] font-semibold">Maria Gomez <span className="font-mono text-[10px] font-normal text-muted-foreground">9:41</span></p>
                  <p className="text-[13px]">/brain {lang === "tr" ? "PTO politikamız nedir?" : "what's our PTO policy?"}</p>
                </div>
              </div>
              <div className="flex items-start gap-2.5">
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-md bg-primary/10 text-primary">
                  <Sparkles className="h-3.5 w-3.5" />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-[12px] font-semibold text-primary">Brain <span className="font-mono text-[10px] font-normal text-muted-foreground">9:41</span></p>
                  <p className="mt-0.5 text-[13px] leading-relaxed text-foreground">
                    {lang === "tr"
                      ? "Tam zamanlı çalışanlar yılda 25 gün PTO + 10 resmi tatil alır; en fazla 5 gün devreder."
                      : "Full-time staff get 25 days PTO + 10 public holidays a year; up to 5 days roll over."}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {[{ s: "notion" as SourceKey, t: "People Handbook" }, { s: "drive" as SourceKey, t: "Holiday Calendar" }].map((c, i) => (
                      <span key={c.t} className="inline-flex items-center gap-1.5 rounded-md border border-border bg-muted/40 py-0.5 pl-1 pr-2 text-[11px]">
                        <span className="grid h-4 w-4 place-items-center rounded bg-card text-[9px] font-bold text-muted-foreground ring-1 ring-border">{i + 1}</span>
                        <SourceIcon source={c.s} size={13} className="rounded-[3px]" />
                        {c.t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Citations / trust deep-dive ──────────────────────────────── */}
      <section className="border-y border-border bg-card/60">
        <div className="mx-auto grid max-w-6xl items-center gap-12 px-5 py-20 lg:grid-cols-2">
          <div>
            <span className="label-mono text-primary">{lang === "tr" ? "Güven katmanı" : "The trust layer"}</span>
            <h2 className="mt-2 font-display text-3xl font-bold tracking-tight">{tt(copy.trustTitle)}</h2>
            <p className="mt-3 text-muted-foreground">{tt(copy.trustSub)}</p>
            <div className="mt-7 space-y-5">
              {trustPoints.map((p) => (
                <div key={tt(p.title)} className="flex items-start gap-3.5">
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
                    <p.icon className="h-5 w-5" />
                  </span>
                  <div>
                    <h3 className="font-semibold">{tt(p.title)}</h3>
                    <p className="mt-0.5 text-sm leading-relaxed text-muted-foreground">{tt(p.body)}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* annotated cited-answer card */}
          <div className="rounded-2xl border border-border bg-card p-5 shadow-pop">
            <p className="label-mono mb-2 text-muted-foreground">{lang === "tr" ? "Kaynaklı yanıt" : "Cited answer"}</p>
            <p className="text-[14.5px] leading-relaxed text-foreground">
              {lang === "tr" ? "Tam zamanlı çalışanlar yılda " : "Full-time employees get "}
              <Cite n={1}>{lang === "tr" ? "25 gün ücretli izin" : "25 days of PTO"}</Cite>
              {lang === "tr" ? " ve 10 resmi tatil alır. Kullanılmayan en fazla " : " plus 10 public holidays. Up to "}
              <Cite n={1}>{lang === "tr" ? "5 gün devreder" : "5 unused days roll over"}</Cite>
              {lang === "tr" ? ". Talepler en az 2 hafta önceden " : ". File requests at least 2 weeks ahead via "}
              <Cite n={2}>{lang === "tr" ? "İK takvimi" : "the HR calendar"}</Cite>.
            </p>
            <div className="mt-4 space-y-2 border-t border-border pt-4">
              {[
                { n: 1, title: "People Handbook — Time Off", source: "notion" as SourceKey },
                { n: 2, title: "2026 Holiday Calendar", source: "drive" as SourceKey },
              ].map((c) => (
                <div key={c.n} className="flex items-center gap-2.5 rounded-lg border border-border bg-muted/40 p-2">
                  <span className="grid h-6 w-6 shrink-0 place-items-center rounded-md bg-card text-[11px] font-bold text-primary ring-1 ring-border">{c.n}</span>
                  <SourceIcon source={c.source} size={20} className="rounded-md" />
                  <span className="truncate text-[13px] font-medium">{c.title}</span>
                  <span className="ml-auto inline-flex items-center gap-1 rounded-full bg-success/10 px-1.5 py-0.5 text-[10px] font-semibold text-success">
                    <Check className="h-2.5 w-2.5" /> {lang === "tr" ? "doğrulandı" : "verified"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Comparison table ─────────────────────────────────────────── */}
      <section className="mx-auto max-w-4xl px-5 py-20">
        <div className="text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight">{tt(copy.compTitle)}</h2>
          <p className="mx-auto mt-3 max-w-xl text-muted-foreground">{tt(copy.compSub)}</p>
        </div>
        <div className="mt-10 overflow-hidden rounded-2xl border border-border bg-card shadow-soft">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="py-4 pl-5 text-left text-[13px] font-medium text-muted-foreground">{lang === "tr" ? "Yetenek" : "Capability"}</th>
                <th className="px-3 py-4 text-center text-[13px] font-medium text-muted-foreground">{lang === "tr" ? "Her yere bakmak" : "Search everywhere"}</th>
                <th className="px-3 py-4 text-center text-[13px] font-medium text-muted-foreground">{lang === "tr" ? "Genel bot" : "Generic chatbot"}</th>
                <th className="px-3 py-4 text-center">
                  <span className="inline-flex items-center gap-1.5 font-semibold text-primary">
                    <Sparkles className="h-3.5 w-3.5" /> {appConfig.name}
                  </span>
                </th>
              </tr>
            </thead>
            <tbody>
              {compRows.map((r) => (
                <tr key={tt(r.label)} className="border-b border-border/60 last:border-0">
                  <td className="py-3.5 pl-5 text-left font-medium">{tt(r.label)}</td>
                  <td className="px-3 py-3.5"><CompCell v={r.a} /></td>
                  <td className="px-3 py-3.5"><CompCell v={r.b} /></td>
                  <td className="bg-primary/[0.03] px-3 py-3.5"><CompCell v={r.c} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-4 flex items-center justify-center gap-2 text-center text-xs text-muted-foreground">
          <Check className="h-3.5 w-3.5 text-success" /> {lang === "tr" ? "tam" : "full"}
          <Minus className="ml-3 h-3.5 w-3.5 text-warning-foreground" /> {lang === "tr" ? "kısmi" : "partial"}
          <X className="ml-3 h-3.5 w-3.5 text-muted-foreground/50" /> {lang === "tr" ? "yok" : "none"}
        </p>
      </section>

      {/* ── Testimonials ─────────────────────────────────────────────── */}
      <section className="border-y border-border bg-muted/30">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <div className="max-w-2xl">
            <h2 className="font-display text-3xl font-bold tracking-tight">{tt(copy.testimonialsTitle)}</h2>
            <p className="mt-3 text-muted-foreground">{tt(copy.testimonialsSub)}</p>
          </div>
          <div className="mt-10 grid gap-5 stagger sm:grid-cols-2 lg:grid-cols-3">
            {m.testimonials.map((tm, i) => (
              <figure key={tm.name} className="flex flex-col rounded-2xl border border-border bg-card p-6 shadow-soft">
                <div className="flex items-center gap-1 text-warning">
                  {Array.from({ length: 5 }).map((_, s) => (
                    <Star key={s} className="h-3.5 w-3.5 fill-current" />
                  ))}
                </div>
                <blockquote className="mt-3 flex-1 text-[15px] leading-relaxed text-foreground">{t(tm.quote)}</blockquote>
                <span className="mt-4 inline-flex w-fit items-center gap-1 rounded-full bg-primary/10 px-2.5 py-0.5 text-[12px] font-semibold text-primary">
                  {t(tm.metric)}
                </span>
                <figcaption className="mt-4 flex items-center gap-3 border-t border-border pt-4">
                  <InitialAvatar name={tm.name} i={i} />
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold">{tm.name}</p>
                    <p className="truncate text-xs text-muted-foreground">{t(tm.role)}</p>
                  </div>
                </figcaption>
              </figure>
            ))}
          </div>
          <div className="mt-8 flex items-center justify-center gap-1.5 text-sm text-muted-foreground">
            {Array.from({ length: 5 }).map((_, i) => (
              <Star key={i} className="h-4 w-4 fill-warning text-warning" />
            ))}
            <span className="ml-2">{lang === "tr" ? "4.9/5 · 200+ ekip" : "4.9/5 · 200+ teams"}</span>
          </div>
        </div>
      </section>

      {/* ── Pricing ──────────────────────────────────────────────────── */}
      <section id="pricing" className="mx-auto max-w-6xl px-5 py-20">
        <div className="text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight">{tt(copy.pricingTitle)}</h2>
          <p className="mt-3 text-muted-foreground">{tt(copy.pricingSub)}</p>
        </div>
        <div className="mt-10 grid gap-5 lg:grid-cols-3">
          {m.pricing.map((tier) => (
            <div
              key={tier.name}
              className={cn(
                "flex flex-col rounded-2xl border border-border bg-card p-7 shadow-soft",
                tier.featured && "ring-2 ring-primary shadow-pop",
              )}
            >
              {tier.featured && (
                <span className="mb-3 inline-flex w-fit items-center gap-1 rounded-full bg-primary px-2.5 py-0.5 text-xs font-semibold text-primary-foreground">
                  <Sparkles className="h-3 w-3" /> {tt(copy.popular)}
                </span>
              )}
              <h3 className="font-semibold">{tier.name}</h3>
              <div className="mt-2 flex items-baseline gap-1">
                <span className="font-display text-4xl font-extrabold tracking-tight">{tier.price}</span>
                {tier.period && <span className="text-sm text-muted-foreground">{t(tier.period)}</span>}
              </div>
              <p className="mt-1.5 text-sm text-muted-foreground">{t(tier.tagline)}</p>
              <ul className="mt-5 flex-1 space-y-2.5 text-sm">
                {tier.features.map((f) => (
                  <li key={t(f)} className="flex items-start gap-2.5">
                    <Check className="mt-0.5 h-4 w-4 shrink-0 text-success" />
                    {t(f)}
                  </li>
                ))}
              </ul>
              <Link
                href="/signup"
                className={cn(
                  "mt-7 inline-flex h-11 w-full items-center justify-center rounded-lg text-sm font-semibold transition-all",
                  tier.featured
                    ? "bg-primary text-primary-foreground shadow-sm shadow-primary/20 hover:opacity-90"
                    : "border border-border bg-card text-foreground hover:bg-muted",
                )}
              >
                {t(tier.cta)}
              </Link>
            </div>
          ))}
        </div>
        <p className="mt-6 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-center text-[13px] text-muted-foreground">
          <span className="inline-flex items-center gap-1.5"><Lock className="h-3.5 w-3.5 text-primary" /> {lang === "tr" ? "SOC 2 & izin-farkında" : "SOC 2 & permission-aware"}</span>
          <span className="inline-flex items-center gap-1.5"><Zap className="h-3.5 w-3.5 text-primary" /> {lang === "tr" ? "5 dakikada kurulum" : "5-minute setup"}</span>
          <span className="inline-flex items-center gap-1.5"><Layers className="h-3.5 w-3.5 text-primary" /> {lang === "tr" ? "6 kaynak konnektörü" : "6 source connectors"}</span>
        </p>
      </section>

      {/* ── FAQ ──────────────────────────────────────────────────────── */}
      <section id="faq" className="border-t border-border bg-muted/30">
        <div className="mx-auto max-w-3xl px-5 py-20">
          <div className="text-center">
            <h2 className="font-display text-3xl font-bold tracking-tight">{tt(copy.faqTitle)}</h2>
            <p className="mt-3 text-muted-foreground">{tt(copy.faqSub)}</p>
          </div>
          <div className="mt-10 space-y-3">
            {m.faq.map((f) => (
              <details key={t(f.q)} className="group rounded-xl border border-border bg-card px-5 py-4 shadow-soft">
                <summary className="flex cursor-pointer list-none items-center justify-between gap-4 font-medium">
                  {t(f.q)}
                  <span className="grid h-6 w-6 shrink-0 place-items-center rounded-full border border-border text-muted-foreground transition-transform group-open:rotate-45 group-open:border-primary group-open:text-primary">+</span>
                </summary>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{t(f.a)}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-5 py-24">
        <div className="relative overflow-hidden rounded-3xl px-8 py-16 text-center text-white shadow-pop" style={{ backgroundImage: "var(--grad-brand)" }}>
          <span className="pointer-events-none absolute -right-10 -top-10 h-48 w-48 rounded-full bg-white/15 blur-2xl" aria-hidden />
          <span className="pointer-events-none absolute -bottom-12 -left-8 h-48 w-48 rounded-full bg-black/10 blur-2xl" aria-hidden />
          <div className="relative">
            <div className="mx-auto mb-5 flex w-fit items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-xs font-medium text-white/90 ring-1 ring-white/20">
              {SOURCES.slice(0, 4).map((s) => (
                <SourceIcon key={s} source={s} size={16} className="rounded-[4px]" />
              ))}
              <span>{lang === "tr" ? "6 konnektör · canlı" : "6 connectors · live"}</span>
            </div>
            <h2 className="mx-auto max-w-2xl font-display text-3xl font-bold tracking-tight sm:text-4xl">{tt(copy.ctaTitle)}</h2>
            <p className="mx-auto mt-3 max-w-xl text-white/85">{tt(copy.ctaSub)}</p>
            <div className="mt-7 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link href="/signup" className="inline-flex h-12 items-center gap-2 rounded-lg bg-white px-6 text-[15px] font-semibold text-foreground transition-colors hover:bg-white/90">
                {t(m.heroCtaPrimary)} <ArrowRight className="h-4 w-4" />
              </Link>
              <Link href="/dashboard" className="inline-flex h-12 items-center gap-2 rounded-lg border border-white/30 px-6 text-[15px] font-semibold text-white transition-colors hover:bg-white/10">
                {lang === "tr" ? "Paneli gör" : "See the dashboard"}
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────── */}
      <LandingFooter lang={lang} />
    </>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   Inline citation pill used inside the trust deep-dive sentence.
   ───────────────────────────────────────────────────────────────────────────── */
function Cite({ n, children }: { n: number; children: React.ReactNode }) {
  return (
    <span className="rounded bg-primary/10 px-1 py-0.5 font-medium text-primary">
      {children}
      <sup className="ml-0.5 text-[10px] font-bold">{n}</sup>
    </span>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   Illustrative panels for the deep-dive blocks — pure inline SVG / markup.
   ───────────────────────────────────────────────────────────────────────────── */
function DeepPanel({ panel, lang }: { panel: "retrieval" | "verify" | "channels"; lang: "tr" | "en" }) {
  if (panel === "retrieval") {
    const passages: { source: SourceKey; title: string; score: number }[] = [
      { source: "notion", title: "People Handbook — Time Off", score: 0.94 },
      { source: "drive", title: "2026 Holiday Calendar", score: 0.81 },
      { source: "confluence", title: "Onboarding Checklist", score: 0.42 },
    ];
    return (
      <div>
        <div className="flex items-center gap-2 rounded-xl border border-border bg-muted/40 p-2.5">
          <ScanSearch className="h-4 w-4 text-primary" />
          <span className="flex-1 text-[13px] text-foreground">{lang === "tr" ? "PTO politikamız nedir?" : "What's our PTO policy?"}</span>
        </div>
        <p className="label-mono mt-3 mb-2 text-muted-foreground">{lang === "tr" ? "Eşleşen pasajlar" : "Matched passages"}</p>
        <div className="space-y-2">
          {passages.map((p) => (
            <div key={p.title} className="flex items-center gap-2.5 rounded-lg border border-border bg-card p-2">
              <SourceIcon source={p.source} size={18} className="rounded-md" />
              <span className="min-w-0 flex-1 truncate text-[12.5px] font-medium">{p.title}</span>
              <span className="h-1.5 w-16 overflow-hidden rounded-full bg-muted">
                <span className="block h-full rounded-full bg-primary" style={{ width: `${p.score * 100}%` }} />
              </span>
              <span className="tnum w-9 text-right text-[11px] font-semibold text-muted-foreground">{p.score.toFixed(2)}</span>
            </div>
          ))}
        </div>
        <p className="mt-3 flex items-center gap-1.5 text-[12px] text-muted-foreground">
          <Check className="h-3.5 w-3.5 text-success" /> {lang === "tr" ? "Top 2 pasaj tek yanıta sentezlendi" : "Top 2 passages synthesized into one answer"}
        </p>
      </div>
    );
  }

  if (panel === "verify") {
    const rows: { title: string; source: SourceKey; status: "fresh" | "stale" | "review"; days: number }[] = [
      { title: "People Handbook", source: "notion", status: "fresh", days: 2 },
      { title: "Pricing & Plans", source: "notion", status: "stale", days: 91 },
      { title: "Refund FAQ", source: "confluence", status: "review", days: 6 },
    ];
    const TONE = {
      fresh: { tr: "taze", en: "fresh", cls: "bg-success/10 text-success" },
      stale: { tr: "eskimiş", en: "stale", cls: "bg-warning/15 text-warning-foreground" },
      review: { tr: "incelemede", en: "in review", cls: "bg-info/10 text-info" },
    };
    return (
      <div>
        <div className="flex items-center justify-between">
          <p className="label-mono text-muted-foreground">{lang === "tr" ? "Doğrulama kuyruğu" : "Verification queue"}</p>
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary">
            <RefreshCw className="h-3 w-3" /> {lang === "tr" ? "otomatik tarama" : "auto-scan"}
          </span>
        </div>
        <div className="mt-3 space-y-2">
          {rows.map((r) => {
            const tone = TONE[r.status];
            return (
              <div key={r.title} className="flex items-center gap-2.5 rounded-lg border border-border bg-card p-2.5">
                <SourceIcon source={r.source} size={20} className="rounded-md" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[12.5px] font-medium">{r.title}</p>
                  <p className="tnum text-[10.5px] text-muted-foreground">
                    {lang === "tr" ? `${r.days} gün önce doğrulandı` : `verified ${r.days}d ago`}
                  </p>
                </div>
                <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", tone.cls)}>
                  {lang === "tr" ? tone.tr : tone.en}
                </span>
              </div>
            );
          })}
        </div>
        <div className="mt-3 flex items-center gap-2 rounded-lg border border-border bg-muted/40 p-2.5">
          <ShieldCheck className="h-4 w-4 text-success" />
          <span className="text-[12px] text-muted-foreground">{lang === "tr" ? "Eskiyen kart Priya'ya yönlendirildi" : "Stale card routed to Priya for review"}</span>
        </div>
      </div>
    );
  }

  // channels
  const items: { icon: typeof Search; label: L; sub: L }[] = [
    { icon: Search, label: { tr: "Web paneli", en: "Web panel" }, sub: { tr: "tam cevap motoru", en: "full answer engine" } },
    { icon: MessageSquare, label: { tr: "Slack /brain", en: "Slack /brain" }, sub: { tr: "kanal içi yanıt", en: "in-channel answer" } },
    { icon: Puzzle, label: { tr: "Tarayıcı eklentisi", en: "Browser extension" }, sub: { tr: "her sekmede", en: "on any tab" } },
    { icon: Code2, label: { tr: "REST API", en: "REST API" }, sub: { tr: "webhook'lar", en: "with webhooks" } },
  ];
  return (
    <div className="grid grid-cols-2 gap-3">
      {items.map((it) => {
        const I = it.icon;
        return (
          <div key={it.label.en} className="rounded-xl border border-border bg-card p-3.5 shadow-soft">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary/10 text-primary">
              <I className="h-[18px] w-[18px]" />
            </span>
            <p className="mt-3 text-[13px] font-semibold">{it.label[lang]}</p>
            <p className="text-[11px] text-muted-foreground">{it.sub[lang]}</p>
          </div>
        );
      })}
    </div>
  );
}

/* ─────────────────────────────────────────────────────────────────────────────
   Richer multi-column footer.
   ───────────────────────────────────────────────────────────────────────────── */
function LandingFooter({ lang }: { lang: "tr" | "en" }) {
  const cols: { title: L; links: { label: L; href: string }[] }[] = [
    {
      title: { tr: "Ürün", en: "Product" },
      links: [
        { label: { tr: "Özellikler", en: "Features" }, href: "#features" },
        { label: { tr: "Kaynaklar", en: "Sources" }, href: "#sources" },
        { label: { tr: "Nasıl çalışır", en: "How it works" }, href: "#how" },
        { label: { tr: "Fiyatlandırma", en: "Pricing" }, href: "#pricing" },
        { label: { tr: "Canlı demo", en: "Live demo" }, href: "#demo" },
      ],
    },
    {
      title: { tr: "Konnektörler", en: "Connectors" },
      links: [
        { label: { tr: "Notion", en: "Notion" }, href: "#sources" },
        { label: { tr: "Google Drive", en: "Google Drive" }, href: "#sources" },
        { label: { tr: "Slack", en: "Slack" }, href: "#sources" },
        { label: { tr: "Confluence", en: "Confluence" }, href: "#sources" },
        { label: { tr: "GitHub & Web", en: "GitHub & Web" }, href: "#sources" },
      ],
    },
    {
      title: { tr: "Şirket", en: "Company" },
      links: [
        { label: { tr: "Hakkımızda", en: "About" }, href: "#" },
        { label: { tr: "Müşteriler", en: "Customers" }, href: "#" },
        { label: { tr: "Güvenlik", en: "Security" }, href: "#" },
        { label: { tr: "Blog", en: "Blog" }, href: "#" },
        { label: { tr: "Kariyer", en: "Careers" }, href: "#" },
      ],
    },
    {
      title: { tr: "Kaynaklar", en: "Resources" },
      links: [
        { label: { tr: "Dokümanlar", en: "Docs" }, href: "#" },
        { label: { tr: "API referansı", en: "API reference" }, href: "#" },
        { label: { tr: "SSS", en: "FAQ" }, href: "#faq" },
        { label: { tr: "Durum", en: "Status" }, href: "#" },
        { label: { tr: "Değişim günlüğü", en: "Changelog" }, href: "#" },
      ],
    },
  ];

  return (
    <footer className="border-t border-border bg-card/60">
      <div className="mx-auto max-w-6xl px-5 py-16">
        <div className="grid gap-10 lg:grid-cols-[1.3fr_repeat(4,1fr)]">
          {/* brand column */}
          <div className="max-w-xs">
            <span className="inline-flex items-center gap-2.5">
              <span className="grid h-9 w-9 place-items-center rounded-xl text-white shadow-pill" style={{ backgroundImage: "var(--grad-brand)" }}>
                <Sparkles className="h-[18px] w-[18px]" />
              </span>
              <span className="font-display text-[17px] font-bold tracking-tight">{appConfig.name}</span>
            </span>
            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">
              {lang === "tr"
                ? "Şirketinin dağınık bilgisini, kaynak gösteren tek bir cevap motoruna dönüştürür."
                : "Turns your company's scattered knowledge into one cited answer engine."}
            </p>
            <Link
              href="/signup"
              className="mt-5 inline-flex h-10 items-center gap-2 rounded-lg bg-primary px-4 text-[13.5px] font-semibold text-primary-foreground transition-opacity hover:opacity-90"
            >
              {lang === "tr" ? "Ücretsiz başla" : "Start free"} <ArrowUpRight className="h-4 w-4" />
            </Link>
          </div>

          {/* link columns */}
          {cols.map((col) => (
            <div key={col.title.en}>
              <p className="label-mono text-foreground/80">{col.title[lang]}</p>
              <ul className="mt-4 space-y-2.5">
                {col.links.map((lnk) => (
                  <li key={lnk.label.en}>
                    <a href={lnk.href} className="text-sm text-muted-foreground transition-colors hover:text-foreground">
                      {lnk.label[lang]}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="mt-12 flex flex-col items-center justify-between gap-4 border-t border-border pt-6 sm:flex-row">
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} {appConfig.name}. {lang === "tr" ? "Tüm hakları saklıdır." : "All rights reserved."}
          </p>
          <div className="flex items-center gap-5 text-xs text-muted-foreground">
            <a href="#" className="transition-colors hover:text-foreground">{lang === "tr" ? "Gizlilik" : "Privacy"}</a>
            <a href="#" className="transition-colors hover:text-foreground">{lang === "tr" ? "Şartlar" : "Terms"}</a>
            <span className="inline-flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-success pulse-dot" />
              {lang === "tr" ? "Tüm sistemler çalışıyor" : "All systems operational"}
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
