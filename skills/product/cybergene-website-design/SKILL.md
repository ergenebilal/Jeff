---
name: cybergene-website-design
version: 1.0.0
author: Jeff + Bilal
description: Use when designing the CyberGene website.
category: product
---

# CyberGene Web Sitesi Tasarım Kilavuzu

## Ne Zaman Kullanılır
- cybergene.co websitesinin yeni tasarımı, güncellemesi veya A/B testi yapılacaksa
- Marka kimliği (CyberGene) ve görsel dili ile uyumlu bir deneyim sunulacaksa
- İşletme odaklı, teknoloji ikincil bir yaklaşımlı benimsenecekse
- Güven, semplicite, insan‑makine dengesi ve gerçek iş değeri önceliklendirilecekse

## 🎨 Marka Kimliği & Logo Kullanımı
- **Ana Slogan:** "İnsan karar verir. Teknoloji yükü taşır."
- **Resmi Logo (`LOGO.SVG`):** `C:\Users\lenovo\cybergene-web\LOGO.SVG` resmi logosu zorunludur. Logo asla yeniden tasarlanamaz, değiştirilemez veya jenerik bir ikonla değiştirilemez. Header, Hero rozetinde ve Footer alanında belirgin ve gururla kullanılmalıdır.
- **Görsel Kimlik & Renk Dünyası:** Koyu antrasit / near-black (`#07090E`), sıcak kırık beyaz metin (`#F4F4F6`), Mor → Mavi → Yeşil gradient imzası SADECE vurgu alanlarında (gradient metin, buton parlaklığı, odak noktası).
- **Yüzey & Minimalizm Disiplini:** Ziyaretçiyi metin, kart, ikon veya teknik bilgi kalabalığıyla boğmak KESİNLİKLE YASAK. Sayfanın ana etkisini: **3D Görseller + Güçlü Tipografi + Geniş Boşluk + Kontrollü Motion + Resmi Logo** oluşturur.
- **3D Görsel Disiplini:** 3D grafikler rastgele dekorasyon değildir. Her ana bölüm için mesajı destekleyen tek, güçlü ve sade 3D görsel kullanılır (1 per section max). Grafik mesajı anlatmıyorsa kullanılmaz.

## 📐 Frontend Master Tasarım Spesifikasyonları (Kilitli Yapı)

### 🎨 Görsel Tasarım & İlham Referansları Framework'ü
- **Cohere:** Tutarlı şekil dili ve arka planda süzülen yumuşak motion background yaklaşımı.
- **Baseten:** Kart bazlı mikro/subtle animasyonlar ve pürüzsüz hover efektleri (kart kalabalığı oluşturmadan, maksimum 4 net hizmet kartı).
- **Arthur:** İnsan + teknoloji birleşimi ve uyumunu yansıtan editoryal görsel dil ("Human × Machine" ifadesi metin olarak YAZILMAZ).
- **XTRACT / Percepta AI Estetiği:** Koyu uzay/antrasit temalı zemin + neon mor/cyan glow ortam ışığı (CyberGene mor-cyan-yeşil paletiyle).
- **Hero 3D Avatar & R3F Mimarisi:** Cohere/Percepta tarzı CSS/SVG motion backdrop arka planda süzülürken, ön planda React Three Fiber ile yarı-insan-yarı-robot 3D avatar/model (`@three-ws/avatar` veya R3F+Drei entegrasyonu). Canvas `client:only="react"` ile lazy-load edilir, `dpr={1.5}` üst sınırı uygulanır, `prefers-reduced-motion` durumunda otomatik animasyon durdurulur.
- **Performans & Görsel Yaklaşım İlkesi:** OpenAI veya Scale AI gibi büyük kurumsal AI sitelerinin yüksek bütçeli ağır görsel üretimini taklit etme. Bunun yerine CSS/SVG/Canvas tabanlı, hafif, 60fps performanslı ama görsel olarak zengin ve keskin bir yaklaşım kullan.
- **Sıfırdan Derleme Stratejisi:** Mevcut `src/components/` dosyalarını parça parça yamalamak yerine, spesifikasyona göre modüler olarak sıfırdan üret.

### 1. Header & Navigasyon
- Sol: Resmi `LOGO.SVG` + `CYBERGENE` markalama metni.
- Orta: Minimal menü (`Hakkımızda`, `Hizmetler`, `Süreç`).
- Sağ: `İşletmenizi Konuşalım` kapsül butonu.

### 2. Bölüm 1 — Hero Section
- **Resmi Logo Etiketi:** `CYBERGENE AI AGENCY` + `LOGO.SVG` rozeti.
- **Hook (Başlık):** "Yapay zekânın gücünü işinize taşıyın." (gradient vurgulu).
- **Alt Metin:** "İşletmeniz için daha akıllı, daha verimli ve çalışma biçiminize uyum sağlayan AI sistemleri kuruyoruz."
- **CTA:** `İşletmenizi Konuşalım` | İkincil CTA: `Nasıl Çalışıyoruz?`
- **Görsel:** Sade, güçlü 3D kuantum cam çekirdek sahnesi.

### 3. Bölüm 2 — Otonom İşletim
- **Hook:** "İşletmeniz için çalışan AI."
- **Alt Metin:** "Tekrarlayan işleri azaltan, operasyonu kolaylaştıran ve ekibinizin kapasitesini artıran sistemler."
- **Görsel:** Tek bir güçlü 3D dikey döner halka/torus görseli.

### 4. Bölüm 3 — Marka Felsefesi (KATI KURAL)
- **Ana Mesaj:** "İnsan karar verir." / "Teknoloji yükü taşır."
- **KATI KURAL:** Ekranda "Human × Machine" yazılması KESİNLİKLE YASAK. "Human × Machine" sadece görsel tasarımın altında yatan fikirdir, metin olarak gösterilmez.
- **3D Görsel:** İnsan ve teknolojinin birbirini tamamlayan iki yapı gibi hissettirdiği 3D çift halka uyum sahnesi.

### 5. Bölüm 4 — Hizmetler (SADECE 4 HİZMET)
Kart kalabalığı oluşturmadan sadece 4 net hizmet gösterilir:
1. **AI Agents:** İşletmeniz adına çalışan dijital çalışma arkadaşları.
2. **AI Automation:** Tekrar eden süreçleri daha akıllı sistemlere dönüştürürüz.
3. **AI Integration:** Yapay zekâyı mevcut araçlarınıza ve iş akışlarınıza bağlarız.
4. **Custom AI Systems:** İşletmenizin ihtiyacına göre özel sistemler tasarlarız.

### 6. Bölüm 5 — Nasıl Çalışıyoruz?
- **Hook:** "Önce anlarız. Sonra kurarız."
- **4 Aşama (Minimal):** `Dinleriz → Analiz Ederiz → Tasarlarız → Geliştiririz`
- Uzun açıklama metinleri ve kart kalabalığı YASAK. Süreç dalgasını temsil eden sade 3D görsel.

### 7. Final CTA, İletişim & Footer
- **Hook:** "İşletmeniz için AI nerede gerçekten işe yarar?"
- **Alt Metin:** "Önce probleminizi anlayalım. Sonra gerçekten fayda sağlayacak çözümü birlikte tasarlayalım."
- **CTA:** `İşletmenizi Konuşalım`
- **WhatsApp Yönlendirmesi:** `https://wa.me/905520947032` (İkincil CTA butonu)
- **Kurucu & İletişim Bilgileri (Kilitli Format):** `Bilal Ergene / Founder & Principal Architect` | `+90 552 094 70 32` | `info@cybergene.co`
- **Sosyal Medya:** Instagram (`https://www.instagram.com/cybergene.ai/`) ve WhatsApp ikonları.
- **Header Navigasyonu:** `TR | EN` dil değiştirici (Pill/Switch, Astro i18n `src/i18n/tr.json` ve `src/i18n/en.json` ile `/en/` rotası).
- **Jeff Canlı Destek Chat Widget'ı (Sağ Alt - v3.0 Mimari):** Floating mor/cyan glow buton, `POST /api/chat/session` (oturum başlatma, UUID `session_id`, `HttpOnly; Secure; SameSite=Strict` `cg_chat_token` çerezi, SHA-256 hash saklama), `POST /api/chat/message` (şablonlu karşılama & açık rıza ile handoff talebi), `GET /api/chat/status/{session_id}` (delta polling, yetkisiz istekte 404 sıfır bilgi sızıntısı), `/api/internal/reply` HMAC-SHA256 + nonce replay korumalı Telegram köprüsü (`telegram_claude_bot.py` `/reply` ve `/close` erken dönüşü), fallback olarak WhatsApp ve e-posta yönlendirmesi. Support API `:8770` portu yalnızca `127.0.0.1` ve `10.0.1.1` private IP'lerine bind edilir (`0.0.0.0` kapalıdır).
- **Footer:** Resmi CyberGene logosu zeminle (#07090E) dikişsiz şeffaf/antrasit uyumuyla tekrar kullanılır.

## 📐 Web Sitesi Tasarım Kilavuzu

### 1. İlk İnsanlık (First 5 Seconds)
Ziyaretçi siteye geldiğinde **5 saniye içinde** şunları anlamalıdır:
- Bu bir AI ajansı / işletme çözüm ortağıdır.
- Gerçek işletmelerle çalışır.
- Teknolojiyi kullanarak işini kolaylaştırır.
- Karmaşık teknoloji jargonuyla etkilemez, iş problemi önce gelir.

### 2. Ana Mesaj (Hero Bölümü — 2026-2027 Master Düzen)
- **Görsel Hiyerarşi:** Merkezde veya asimetrik temiz yerleşimde okunaklı editoryal tipografi. Ziyaretçinin ilk 3 saniyede anlamayacağı karmaşık 3D kokpitler, anlaşılmaz teknik loglar veya kalabalık diyagramlar KESİNLİKLE YASAK.
- **İki satırlık başlık:** "İnsan karar verir." (alt satır) "Teknoloji yükü taşır."
  - Font: Archivo Black / Cabinet Grotesk / Inter Black / Space Grotesk.
  - Vurgulanacak kelimeler: "yükü" ve "taşır." – Mor→Mavi→Yeşil gradient ile.
- **Destek Metni:** "Şablonlar geride kaldı. İşletmenizin süreçlerini 12ms gecikmeyle devralan otonom yapay zekâ ajansı altyapılarını kuruyoruz."
- **3D WebGL Tuvali (ThreeUI Estetiği):** Sayfanın arkasında ziyaretçinin imlecine tepki veren, kırılan ve süzülen prosedürel 3D WebGL / Shader tuvali (ThreeUI `AtTheHorizon` / Kuantum Parçacık Ağı).
- **100vh / Above-the-Fold Uyum Sınırı:** Hero dikey padding ve gap değerleri compact tutulmalı (`pt-20 pb-8`); tüm görsel ve telemetri çubuğu ekranı kaydırmadan (0-scroll) tek bakışta %100 görünmelidir.

### 3. Renk Sistemi
- **Zemin:** Koyu antrasit / near‑black (#0B0F0D)
- **Metin:** Kırık beyaz / soft white (#FFFFFF, #F2F7F3)
- **Gradient İmza (Enerji Rengi):** Mor → Mavi → Yeşil (linear‑gradient(135deg, #A855F7 0%, #3B82F6 50%, #10B981 100%))
  - Sadece vurgularda, başlık kelimeleri, ikonlar, ince çubuklar, hassas ayrıntılar için kullanılır.
  - Büyük bloklar, sayfa arkaplanı, geniş bölümlerde **KULLANILMAZ**.

### 4. Tipografi
- **Başlıklar:** Archivo Black (bold, expressive) veya benzeri (Helvetica Now Bold, Inter Black).
- **Gövde:** Manrope (regular, okunabilir, modern) veya benzeri (Inter, SF Pro Text).
- **Türkçe Karakter:** Büyük harfleri elle yazın (DİŞ KLİNİKLERİ), `text‑transform:uppercase` veya `.upper()` kullanmayın (i → I hatası).
- **OKUNUMLUĞU:** Metin ≥ 35px, yeterli kontrast (WCAG AA/AAA).

### 5. Düzen ve Bileşenler
- **Navigasyon:** Üstte tek CTA butonu "İşletmeni Konuşalım". Altımsı menü (gizli veya görünür) içerir: Çözümler, Nasıl Çalışıyoruz?, Hakkımızda.
- **Kartlar:** Geniş kartlar yerine öznitelikli, anlamlı kartlar kullanın. Her kartın bir amaçlı başlığı, kısa açıklaması ve gerekirse görselleştirmesi olmalıdır. Geniş "iki kart ile ikon" örneklerinden kaçının.
- **Butonlar:** Yuvarlatılmış köşe, premium hissi, gradient dolgu (birincil) veya outline (ikincil). Hover da hafif gradyan değişimi veya gölge.
- **Form Alanları:** Basit, açıklayıcı etiketler, hata mesajları işlevsel.

### 6. İçerik Bölümleri ve Hikâye Akışı
- **Problem Bölümü:** Başlık: "İşletmenizin yükü neden hâlâ insanın omzunda?"
  - Gerçek, sobre iş problemlerini listeleyin: tekrarlayan görevler, manuel veri girişi, kaçan müşteri mesajları, takip yükü, dağınık bilgi, tek kişiye bağımlı süreçler.
  - Korku patlaması, over‑claim (% kurarı) veya finansal kayıp tahmini **YASAK**.
  - Ton: "Bu durumda olmayan bir şey var mı? birlikte bulalım."
- **Çözüm Bölümü:** İş‑odaklı ifadelerle başlayın:
    "Tekrarlayan işleri azaltın."
    "Her müşteri mesajını zamanında karşılayın."
    "Bilgiye daha hızlı ulaşın."
    "Takip edilmesi gereken işleri sistemlere bırakın."
  - Teknoloji ayrıntıları (AI, otomasyon vb.) **ikinci sırada**, sadece nasıl sağlandığını gösterin.
- **İnsan × Makine Bölümü:** Başlık: "İnsan karar verir. Teknoloji yükü taşır."
  - Görsel: organik (insan silüeti, yumuşak çizgi) ile geometrik (kutu, çizgi, ağ) birleştirilir, hiçbir taraf baskın olmaz.
  - Metin: İnsan karar verir, yaratıcılık gösterir, ilişki kurar; makine yükü taşır, hız verir, sürekliliği sağlar.
- **Süreç Bölümü:** Net, numaralı adımlar (ikonlu değil):
    01 – DİNLERİZ
    02 – ANALİZ EDERİZ
    03 – KARAR VERİRİZ
    04 – KURARIZ
    05 – DEVREYE ALIRIZ
    06 – GELİŞTİRİRİZ
  - Her adım kısa bir cümle, fazladan grafik ya da ikon gerektirmez.
- **AI Her Zaman Cevap Değil Bölümü:** Başlık: "Her probleme yapay zeka gerekmez."
  - Akış: Problemi dinle → analiz et → AI gerekli mi? → Evetse uygun çözüm tasarla → Hayırsa basit çözüm öner ve bunun nedenini açıkla.
  - Satış łączında bu ilkeleri koru.
- **Güven Bölümü:** İlkeler:
    Önce problemi anlarız.
    Gereksiz teknoloji kullanmayız.
    Anlaşılır sistemler kurarız.
    Verdiğimiz sözün arkasında dururuz.
    Sonuca odaklanırız.

### 7. Hareket (Motion)
- **İzin verilen:** Yumuşak gradient hareketi (arka planda hızlı olmayan akış), metin avslama (fade‑in), gentil kart etkisi (hafif yükselme, gölge değişikliği), geçişte yumuşak kaydırma.
- **YASAK:** Sürekli floating nesneler, hızlı animasyonlar, parçacık sistemleri, "her şey parlar" efektleri, aşırı glassmorphism, neon dışı dışı dışı.

### 8. Yanıtlayıcı Tasarım (Responsive)
- **Mobil:** Tek başına tasarım, sadece küçülmüş masaüstü değil.
- **Öncelikler:** Tipografi okunurluğu, CTA görürlüğü, dokunma hedefi (≥48dp), okuma ritmi, görsel hiyerarşi.
- **İnsan×Makine kavramı:** Mobilde de anlaşılır olmalı, önekeler değil.

### 9. Design Sistemi (Kapsamlı)
Bu skill, aşağıdaki her bir parçayı kapsar:
- Renk (zemin, metin, gradient imza, uyarı/başarı renkleri)
- Tipografi (font ailesi, ağırlıklar, boyutlar, satır Höhen)
- Boşluk (8px temel grid, düzenli marjin/padding)
- Grid (12‑sütun, esnek)
- Butonlar (birincil, ikincil, danger, link stilleri)
- Kartlar (varsayılan, emphasized, outlined)
- Formlar (giriş, seçenek, onay kutusu)
- Navigasyon (yatay, dikey, mobil menü)
- Bölüm düzenleri (hero, problem, çözüm, süreç, güven, CTA)
- İkonlar (minimal, anlamlı, sadece gerekirse)
- Border (ince, sadece gerekirse)
- Gölge (hafif, sadece derinlik için)
- Gradient (imza ve uyarı için, kontrollü)
- Motion ilkeleri (yumuşak geçiş, kısa süreli efekt)
- Yanıtlayıcı davranış (breakpoints, font ölçekleme, dokunma)

### 10. Anti‑Genrik AI Ajansı Kuralı
Aşağıdaki ögeler **KESİNLİKLE YASAK**tır (çünkü "modern AI agency website" şablonlarını temsil eder):
- Büyük, parlayan beyin illustrasyonu
- Robot veya kyborg figürleri
- Sonsuz gradient blobları veya yuvarlak 3D küpler
- Random dashboard görüntüleri
- Stok iş insanları fotoğrafları (laptop başında)
- Anlamsız AI buzzword"leri ("10X", "next‑generation", "autonomous workflow orchestration")
- Aşırı glassmorphism (effektif cam benzeri efekt)
- Neon cyberpunk estetiği
- Terminal/kod ekranı dekorasyonu (kod satırları arka plan olarak)
- Sahte müşteri logoları veya testimoni
- Fazla renkli, çelişkili paletler

Her görsel öğenin nedeni olmalı ve "gözünüzü hoş undıran" dışında bir işlevi olmalıdır.

### 11. Görsel Hiyerarşi ve Dengesi
- **Görsel Hiyerarşi:** Marka → Temel vaat (İnsan×Makine slogan) → İş problemi → Pratik çözümler → İnsan×Makine felsefesi → Süreç → Güven → Son CTA.
  Her bölüm birbirini ağırlaştırmadan akmalı olmalı; bazı bölümler nefes alabilmek için daha hafif olabilir.
- **Denge Oranı (hedef):**
    %50 İnsan (karar, yaratıcılık, ilişki,empati)
    %25 İnsan + Sistem (insan yönlü teknoloji açıklamaları, iş odaklı arayüzler)
    %15 Yeni Nesil Teknoloji (fikir, ileri teknoloji olduğuna dair ipuçları)
    %10 Somut Teknoloji (gerçek kod, veri akışı, altyapı – sadece gerekliyse)
  Bu oran, siteyi bilimkurgu yapmaktan ve insan‑odaklı kalmasını sağlar.

### 12. Kalite Çubuğu
Son tasarım şu özellikleri göstermelidir:
- Premium (yüksek endüstri standartlarıyla rekabet eder)
- Özgün (şablon değil, kendi dili)
- Tutarlı (her sayfa aynı sistemDE)
- Modern (güncel UI/UX prensipleri)
- İnsan‑yönlü (işletme sahibi bu adreste kendi işini anlar)
- Teknolojik olarak güvenilir (araçlar gerçek, işe yarar)
- İş odaklı (her şey gerçek bir problemi çözer)
- Sakin ve güvenir (heyecanlandırıcı değil, güven veren)

### 13. Tasarım Karar Filtresi
Her büyük tasarım kararı (renk, font, layout, bileşen) için şu sorular sorulur:
1. Bu CyberGene’yi daha güvenilir kılacak mı?
2. Bu teknolojiyi daha anlaşılır kılacak mı?
3. Bu pratik iş değeri sağlayacak mı?
4. Bu insani‑öncelikli felsefeyi koruyacak mı?
5. Bu markayı daha farklı kılacak mı?
6. Bu gereklidir mi?
7. Bu sadece "gözünüzü hoş undıran" bir AI buzzword/efekt mi? (Eğer evetse, çıkartın.)

### 14. Son İdee
- Üst başlık: "İşletmenizi teknolojiye uydurmuyoruz. Teknolojiyi işletmenize uyduruyoruz."
- Alt başlık: "İnsan işini yapsın. Teknoloji yükü taşısın."

## 🏬 Showroom & Canlı Ürün Vitrini Mimarisi (Adaptif Konsol & Ticari Zeyilname)

### 1. Darboğazdan Giriş & Bilişsel Yük Disiplini ("Nereden Başlayalım?")
- **Teknoloji Şovu Yasağı & Görsel Şov İlkesi:** Showroom ve canlı ürün vitrinlerinde göz yoran karmaşık radarlar, milisaniye göstergeleri, mühendislik jargonları (`DÇ-00`, `BEKLEMEDE`, `S-01`, `PATCH-A`) ve devasa takımyıldız animasyonları KESİNLİKLE YASAK. Bunlar müşteri üzerinde "Çok karmaşık, yönetemem" korkusu (Cognitive Overload) yaratır. 'Görsel şov olsun' talebi soyut sci-fi animasyonları değil, **Somut İş Çıktı Kartlarını** (Randevu Defteri, Fatura Dekont Eşleşmesi, Teklif Özeti, WhatsApp Müşteri Takibi) ifade eder.
- **2 Panelli Ferah Düzen (`.studio-card`):** Ziyaretçi ilk 3 saniyede 2 şeye odaklanmalıdır: (1) Sol/Üst: Sektör seçimi -> Soruyu seç -> Canlı Sohbet (`Dijital çalışanınız · çevrimiçi`). (2) Sağ/Alt: Anında değişen net iş çıktısı (Randevu defteri, Fatura/Dekont eşleşmesi, Teklif taslağı).
- **Sektör Bazlı Derin Link Desteği (Deep Link):** `https://cybergene.co/showroom/?sector=dental#studio` linki Diş Klinikleri için doğrudan `Diş kliniği` çipi seçili ve deneyim kokpitine odaklanmış şekilde açılır. Müşteriye WhatsApp'tan gönderilecek en etkili niş açılış kapısıdır.
- **Problem-First Otonom Refaktör Protokolü:** Claude Code / Codex ile arayüz refaktör ederken hazır reçete vermek yerine; 2 temel problemi (bilişsel yük/jargon kalabalığı ve asıl değerin gömülü kalması) ve beklenen kabul kriterlerini (insani dil, 2 panelli yan yana düzen, canlı iş çıktısı şovu) tanımlayın, teknik çözümü ajanın tasarım zevkine (`taste-skill` / Anthropic zarafeti) bırakın.
- Ziyaretçiden zorunlu sektor seçimi beklemek yerine acı noktası seçimi (*"En çok hangi iş sizi yoruyor?"*) eklenebilir.
- Seçim yapmak mesaj göndermez veya konuşmayı sıfırlamaz; sadece canlı konsolu ve önerilen soruları bağlam olarak günceller.

### 2. Çift Konuşma Modu (Dual-Mode Toggle)
- Ziyaretçiye iki farklı perspektif sunun: `[ Müşteri gibi dene ]` (hasta/müşteri gözüyle simülasyon) ve `[ İşletmem için sor ]` (patron/yönetici gözüyle operasyon sorgusu).
- Canlı backend uç noktası (`POST /api/chat/message`) her iki modda da uygun ton ve yetki sınırlarıyla yanıt verir.

### 3. Somut Çıktı Vitrini & "Temsili Çıktı" Etiketi
- Soyut vaatler yerine canlı mockup ekranları (Randevu defteri, WhatsApp takibi, PDF fatura eşleme, Sabah Brifingi) gösterilmelidir.
- Tüm örnek ekranlar açıkça *"Temsili Çıktı / Temsili Ekran"* etiketi taşımalıdır; canlı LLM yanıtı ile statik örnek ekranlar birbirine karıştırılmamalıdır.

### 4. Sorumluluk & Sınır Şeffaflığı (Human-in-the-Loop)
- Ziyaretçinin yasal/tıbbi taahhüt veya kontrol kaybı korkusunu sıfırlamak için 3 açık katman sunulmalıdır:
  - *Sizden gerekenler* (ilgili fatura/müşteri kayıtları)
  - *Devralınan işler* (bilgi toplama, taslak hazırlama, hatırlatma)
  - *Sizde kalan kararlar* (nihai onay, hukuki/ticari değerlendirme, fiyat yetkisi)

### 5. İşletmeye Özel Başlangıç Özeti & Akıllı WhatsApp CTA
- Ziyaretçinin seçimlerinden "İşletmenizin Başlangıç Planı" özeti oluşturun.
- Buton (`Bu özetle görüşme iste ↗`) yalnızca seçilen yapılandırılmış parametreleri içeren bir WhatsApp mesaj taslağı üretmelidir.

### 6. Sub-Agent / Codex İçin Kavramsal Promptlama İlkesi
- Kodlama ajanı (Codex / Claude Code) ile UI/UX tasarlarken harfi harfine başlık sabitlemek yerine, **kavramsal tasarım çerçevesi, mimari hedefler ve kullanıcı psikolojisi** verilerek editoryal/tasarımsal serbestlik tanınmalıdır.
- Karmaşık matematiksel formüller ve nakit/ciro vaatleri yerine; 5 temel operasyonel korkuya (gece karşılama, %100 insan onayı, ön bilgi toplama, no-show azaltma, ekstra program öğrenmeme) odaklanan dokunmatik uyumlu **İnteraktif Slayt Kataloğu (Benefit Carousel)** kullanılmalıdır. Nakit kazanç sözü yasal ve etik olarak verilmez; yalnızca ölçülebilir süreç ve zaman farkı gösterilir.

### 7. Claude Code & Awwwards Tasarım Mimarisi Entegrasyonu
- Lüks, scroll tabanlı ve Awwwards kalitesinde web projeleri üretirken Claude Code ortamına 4 kritik tasarım skill'i (`design-dna`, `frontend-design`, `taste-skill`, `scroll-craft`) ve 5 temel MCP (`context7`, `playwright`, `notebooklm-mcp`, `sequential-thinking`, `figma`) dahil edilir.
- Devasa dokümanlar, renk rehberleri ve PDF spesifikasyonları prompt penceresini doldurmak yerine Google NotebookLM'e konulur ve `notebooklm-mcp` üzerinden sorgulanır. Bu sayede token harcaması ve bağlam maliyeti %99 oranında düşürülür.

---

## 🛠️ Önemli Tuzaklar (Pitfalls)
- **Multi-LLM Prompt Pipeline & Codex Astra Kullanımı:** Karmaşık frontend/i18n/widget revizyonlarında tek seferde kod yazdırmaya çalışmak yerine; Perplexity Pro / Claude Sonnet ile kusursuz teknik spec ve prompt üretin, ardından projeyi GPT-5.6 Astra (Codex) modeline teslim edin. Astra çoklu dosya yapısını (Astro i18n, React widget, Tailwind) bozmadan pürüzsüz üretir. Kodlama sonrası Pablo'da `npm run build` alıp `dist/` paketini sunucuya (`/var/www/cybergene`) aktararak canlıya alın.
- **Spaceship API & DMARC Güvenlik Aktivasyonu:** `cybergene.co` DNS ve e-posta kayıtları Spaceship API (`https://spaceship.dev/api/v1/dns/records/cybergene.co`, `X-API-Key` / `X-API-Secret`) üzerinden güncellenir. DMARC kaydında `p=none` (sadece izleme) bırakmayın; sahte/phishing gönderimleri engellemek ve Gmail/Outlook tarafında %100 Gelen Kutusu (Inbox) teslimatı sağlamak için `v=DMARC1; p=quarantine;` kaydını aktif edin. Spacemail doğrudan webmail adresi: `https://www.spacemail.com/login/`.
- **ChatGPT Reseller Hesabı & 2FA Doğrulama:** İtemsatış veya reseller ChatGPT Plus/Codex hesaplarında şifre ve 2FA (TOTP) anahtarı verilir. 2FA kodları için harici sitelere gitmeye gerek yoktur; Python `hmac`/`base64` ile canlı 6 haneli TOTP kodu üretilebilir. **Satıcının garantisinin iptal olmaması için şifre ve 2FA kesinlikle değiştirilmez**, doğrudan resmi web arayüzünde kullanılır. Tasarım/UI çalışmalarında Canvas ve Vision desteği için `GPT-4o` veya `GPT-5.6 Astra` modeli tercih edilmelidir.
- **Canlı Destek Chat Widget & İzolasyonlu Handoff Mimarisi:** Site üzerindeki canlı destek widget'ı doğrudan serbest LLM üretimine açılmaz. İlk katmanda doğrulanmış statik menü seçenekleri (CyberGene hizmetleri, teklif talebi, iletişim) sunulur. Ziyaretçi serbest metin yazdığında şablon yönlendirmesi yapılır; açıkça "Canlı desteğe bağlan" talep edildiğinde durum `handoff_requested` olarak Telegram botuna bildirim düşer. Jeff Telegram'dan yanıt verene dek ziyaretçiye canlı bağlanmış yalanı söylenmez; 60s süre aşımında dürüstçe WhatsApp (`https://wa.me/905520947032`) ve e-posta (`info@cybergene.co`) yönlendirmesi gösterilir. Ziyaretçiden gelen veriler hiçbir zaman Jeff'in ana terminal/SSH/MCP yetkilerine erişemez.
- **Codex & Pablo Canlı Doğrulama Döngüsü:** Codex'e proje klasörü (`C:\Users\lenovo\cybergene-web`) verilir. Codex güncellemeyi bitirdikten sonra dev sunucusu (`http://127.0.0.1:4322`) Pablo browser (`alfred browser`) ile öne getirilip `alfred screenshot` + `vision_analyze` ile kamuya sunulmadan önce doğrulanır.
- **Karmaşık & Anlaşılmaz 3D Kokpit Tuzağı:** Sayfayı teknik loglar, karmaşık terminal simülasyonları ve anlamsız 3D göstergelerle doldurmak. Müşteri ne gördüğünü 1 saniyede anlamıyorsa tasarım kötüdür. 3D'yi karmaşık göstergeler için değil, arkada pürüzsüz WebGL shader tuvali veya Awwwards 3D nesnesi olarak kullanın.
- **Ucuz Şablon Taklit Tuzağı:** ThemeForest / WordPress şablonlarından stok cyborg görselleri, ucuz butonlar ve göz yoran kayan yazılar eklemek CyberGene'i ucuz ajans seviyesine düşürür.
- **Jenerik Parçacık Noktaları Tuzağı:** Arka plana öylesine rastgele Three.js parçacık noktaları koymak 2020'den kalma ucuz HTML şablonu hissi verir. `github.com/topics/3d-website` (Awwwards / Active Theory / Lusion) standartlarına uygun olarak; Lenis ataletli scroll ve imleç hareketiyle dikey uzayda dönen, ışığı büken 3D Kuantum Çekirdek (Three.js r170 `MeshPhysicalMaterial` transmission + dispersion cam/krom icosahedron mesh) tercih edilmelidir.
- **Pencere Odaklama & Ekran Görüntüsü Yanılsaması Tuzağı:** Windows yerel makinesinde (Pablo) ekran görüntüsü alırken Telegram veya ChatGPT gibi masaüstü uygulamaları Chrome'un önüne geçebilir. Görsel doğrulama yapmadan önce Chrome pencerelesini `SetForegroundWindow` ile öne geçirin veya doğrudan `alfred browser <url>` çağırın; aksi halde yanlış pencere görüntüsü analiz edilip hatalı rapor üretilebilir.
- **Astro SSR / React Renderer Çakışma Tuzağı:** Astro projelerinde React 19 bileşenlerini `client:load` ile çağırırken `NoMatchingRenderer` veya `FailedToLoadModuleSSR` hatası alınabilir. Çözüm: 3D WebGL / Three.js sahnelerini doğrudan katı yerel `.astro` bileşeni içinde `<script>` etiketiyle yazın; 0ms latens ile sorunsuz çalışır.
- **Sıradan 50/50 İki Sütunlu SaaS Şablon Tuzak:** Sola metin, sağa 2D diyagram/kutu koymak 2020-2023 basmakalıp şablon hissi verir. Ortalanmış spatial hiyerarşi ve arkada derinliği olan 3D WebGL tuvali tercih edin.
- **Sayfa Katlanma Yeri (Viewport Fold) Kesilme Tuzağı:** Hero öğelerini dikeyde fazla geniş tutup alt tarafını ekranın/taskbar'ın altında kesmek. Dikey paddingleri daraltın ki tüm görsel 100vh içinde scroll gerektirmeden tam görünsün.
- **Aşırı Neon / Parlak Renk Kullanımı:** `#8CF06F` gibi neon yeşil "ucuz bot" hissi verir. Gradient imzası sadece vurgularda kullanın.
- **Türkçe Harf Duyarsızlığı:** Büyük harfleri elle yazın, programatik `.upper()` kullanmayın.
- **Logo Kullanımı:** Logo sadece altta ortada küçük (18px) olarak görünür; diğer yerlerde tekrar edilmez, boyutu değiştirilmez.
- **Navigasyon Karışıklığı:** Fazla menü maddesi, karışık catégoriler. Tek bir birincil CTA ve kısa içerik menüsü yeterlidir.
- **Motion Aşırı Yüklemesi:** Sürekli hareket eden nesneler, hızlı geçişler, parçacık sistemleri. Yumuşak ve amaçlı hareket tutun.
- **İçerik Fazlalığı:** Bölümlerde gereksizTek metin, boşluk doldurucu gereksiz başlıklar. Kısa ve net olsun.
- **Mobilde Unsur Kaybı:** İnsan×Makine görseli, başlık hiyerarjisi veya CTA sadece masaüstünde görünür. Mobilde de aynı öncelikleri koruyun.

## 🚀 Canlı Deploy Protokolü (cybergene.co)

### Mimari Gerçeği
- `cybergene-landing` Docker container'ı (`nginx:alpine`) → `/var/www/cybergene:/usr/share/nginx/html:ro` bind mount (read-only)
- Traefik (`coolify-proxy`) → 80/443 → `cybergene-landing:80`
- `/var/www/html/showroom/` yolu YOKTUR — doğru yol `/var/www/cybergene/showroom/`
- SSH + SCP gerekmez: Jeff zaten VPS içinde yaşıyor, doğrudan `sudo cp` yeterlidir

### Deploy Adımları (Sunucudan)
```bash
# 1. Rebuild (cybergene-web-repo'dan)
cd /home/hermes/cybergene-web-repo && npm run build

# 2. Versiyon damgasını güncelle (public/showroom/index.html)
# ?v=YYYYMMDD-N formatı (ör. 20260927-1)
patch public/showroom/index.html  # veya sed ile

# 3. Canlıya kopyala
sudo cp -r dist/* /var/www/cybergene/ && sudo chmod -R 755 /var/www/cybergene/

# 4. Container restart (nginx cache temizlenir)
docker restart cybergene-landing && sleep 3
```

### Zorunlu Doğrulama Sırası (Her Deploy Sonrası)
```bash
# 1. Dosya tarihi ve versiyon damgası — disk gerçeği
ls -lh /var/www/cybergene/showroom/
cat /var/www/cybergene/showroom/index.html | grep -o 'v=20260[0-9]*-[0-9]'

# 2. HTTP header — container gerçeği
curl -sI https://cybergene.co/showroom/app.js | grep -i "last-modified\|etag"

# 3. Canlı sayfa — internet gerçeği
curl -s https://cybergene.co/showroom/ | grep -o 'v=20260[0-9]*-[0-9]' | head -1

# 4. Container durumu
docker ps | grep cybergene-landing
```

**Doğrulama geçer koşulu:** Disk, HTTP header ve curl çıktısı aynı `v=YYYYMMDD-N` damgasını gösteriyorsa ✅

### Alternatif Deploy Yolu — Antigravity Bot (Bilgisayar Başında Değilken)
Bilal bilgisayar başında değilse `deploy.ps1`'i tetiklemenin en hızlı yolu `@Antigravity_cybrgn_bot`'a Telegram'dan doğrudan yazmaktır:
```
cd C:\Users\lenovo\cybergene-web && .\deploy.ps1
```
Jeff bu bota HTTP ile ping atamaz (token maskelenmiş, servis env'de yok). Bot çalışıyorsa Telegram'dan yanıt verir; çalışmıyorsa Pablo Bridge (`7700`) üzerinden dene.

### Pitfalls — Deploy
- `/var/www/html/showroom/` diye bir yol yok — yanlış yola cp yaparsan sessizce başarılı görünür, canlı değişmez.
- Container read-only mount olduğundan container içine cp yapılamaz — host'taki `/var/www/cybergene/` dizinine yaz.
- `sudo cp` sonrası `chmod -R 755` zorunlu — nginx worker farklı kullanıcıyla çalışıyorsa 403 döner.
- Versiyon damgası `public/showroom/index.html`'de değiştirilmeli — sadece `dist/` değiştirilirse bir sonraki build eski damgayı geri getirir.
- Kendi sunucudan `curl` atmak loopback'ten geçer, dış erişimi kanıtlamaz — ama bu durumda Traefik aynı host'ta olduğundan `curl -sI https://cybergene.co/...` güvenilirdir; asıl tuzak portun gerçekten dışarıya açık olup olmadığını test ederken geçerlidir.
- `npm install` timeout alırsa `node_modules/` mevcut olduğu sürece `npm run build` yine de çalışır — install başarısız olsa bile build dene.
- Tarayıcı cache ≠ sunucu cache: sunucudan `curl -s https://cybergene.co/showroom/ | grep 'v=2026'` doğru versiyon dönüyorsa sorun sunucu tarafında değil, kullanıcının tarayıcısındadır. Nginx/Docker cache temizleme bu durumda etkisizdir — incognito veya farklı cihazdan test et.
- Cloudflare yoksa `curl -sI https://cybergene.co/showroom/ | grep -i 'cf-\|cloudflare'` boş döner; bu durumda nginx cache temizleme (`rm -rf /var/cache/nginx/*`) ve container restart yeterlidir.
- Claude Code yerel makinede (`C:\Users\lenovo\cybergene-web`) yaptığı değişiklikleri sunucudaki repo (`/home/hermes/cybergene-web-repo`) otomatik almaz — yerel değişiklikler GitHub'a push edilmeden sunucu rebuild'i eski kodu derler. Deploy öncesi `git log --oneline -3` ile hangi commit'in build edildiğini doğrula.
- SupportBot veya herhangi bir React bileşeni build'e dahil edilmezse `src/components/` altında dosya var olsa bile `dist/_astro/` klasöründe JS bundle oluşmaz — `grep -rn 'SupportBot' dist/` ile bundle varlığını teyit et.
- **`dist/` `.gitignore`'da:** `cybergene-web` reposunda `dist/` klasörü `.gitignore`'a eklenmiştir. GitHub'a push edilen şey kaynak koddur, derlenmiş çıktı değil. Bu nedenle sunucu tarafından `git pull` + `npm run build` yapılmalıdır; sunucuya doğrudan `dist/` push etmek işe yaramaz. Sunucudaki `/home/hermes/cybergene-web-repo/` reposu kaynak kodu tutar, `npm run build` ile `dist/` üretilir, ardından `sudo cp -r dist/* /var/www/cybergene/` ile canlıya alınır.
- **Claude Code yerel değişikliklerini GitHub'a push etmeden sunucu rebuild yapma:** Claude Code `C:\\Users\\lenovo\\cybergene-web` üzerinde çalışır. Bu değişiklikler GitHub'a push edilmeden sunucudaki repo (`/home/hermes/cybergene-web-repo`) eski kodu içerir. Deploy öncesi `git log --oneline -3` ile commit'in güncel olduğunu doğrula; değilse Bilal'den `git push` yapmasını iste veya `@Antigravity_cybrgn_bot` üzerinden `cd C:\\Users\\lenovo\\cybergene-web && git push` tetikle.

## 📁 DESTEK DOSYALARI
- `references/3d-website-master-prompt.md` — 5 Aşamalı 3D WebGL (ThreeUI & Claude-Directory) tasarım doktrini ve kaynak haritası.
- `references/brand-brief-full.md` — Bilal'in sunduğu tam marka brief'i.
- `references/website-design-principles.md` — Detaylı renk, tipografi, bileşen ve motion spesifikasyonları (opsiyonel, genişletilebilir).

Not: Bu skill, cybergene-marka-kimligi ile bütünleşir; marka kuralları için ona bakınız.
