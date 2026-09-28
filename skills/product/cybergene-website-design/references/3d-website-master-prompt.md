# CYBERGENE 3D FÜTÜRİSTİK WEBSITE TASARIM DOKTRİNİ VE AŞAMA REHBERİ

## AŞAMA 1 — KAYNAK REPOLAR VE 3D MİMARİSİ
1. **ThreeUI (`https://github.com/MengTo/threeui`):**
   - Three.js WebGL prosedürel shader tuvalleri (`AtTheHorizon`, `Quantum Particle Mesh`).
   - Kullanım: Prosedürel 3D hero arka planı, imlece duyarlı parçacık/kristal efektleri.
2. **claude-directory (`https://github.com/pulkitxm/claude-directory`):**
   - SVG Node Ağaçları ve 3D-Tilt Cam Kartlar.
3. **3D Website Topics (`https://github.com/topics/3d-website` — Ödüllü Awwwards 3D Mimarisi):**
   - Reference: `tsogjavklann/awwwards-3d`, `Itssanthoshhere/Macbook-Landing-Page`.
   - Mimari Stack: Three.js r170 + GSAP (ScrollTrigger) + Lenis 1.1 (Smooth Inertia Scroll).
   - Mesh: Chrome / Glass Icosahedron Mesh with `MeshPhysicalMaterial` transmission + dispersion.

## AŞAMA 2 — MARKA KİMLİĞİ TOKEN'LARI VE LOGO
- **Resmi Logo (`LOGO.SVG`):** `C:\Users\lenovo\cybergene-web\LOGO.SVG` dosyası kilitli resmi logodur. Değiştirilemez, jenerik sembolle yer değiştirilemez. Header, Hero ve Footer'da belirgin biçimde kullanılır.
- **Zemin:** Koyu Antrasit Void (`#07090E`).
- **Metin:** Sıcak Kırık Beyaz (`#F4F4F6`).
- **Vurgu Rengi:** Mor (`#A855F7`) ➔ Mavi (`#3B82F6`) ➔ Yeşil (`#10B981`) gradient paleti (sadece gradient metin ve buton vurgularında).

## AŞAMA 3 — 5 BÖLÜMLÜ MASTER SAYFA YAPISI
1. **Hero Section:**
   - Hook: *"Yapay zekânın gücünü işinize taşıyın."*
   - Alt Metin: *"İşletmeniz için daha akıllı, daha verimli ve çalışma biçiminize uyum sağlayan AI sistemleri kuruyoruz."*
   - CTA: `İşletmenizi Konuşalım` | İkincil: `Nasıl Çalışıyoruz?`
   - Görsel: 3D Kuantum Cam Çekirdek sahnesi.
2. **Bölüm 2 (Otonom AI):**
   - Hook: *"İşletmeniz için çalışan AI."*
   - Alt Metin: *"Tekrarlayan işleri azaltan, operasyonu kolaylaştıran ve ekibinizin kapasitesini artıran sistemler."*
   - Görsel: 1 adet güçlü 3D dikey döner torus.
3. **Bölüm 3 (Marka Felsefesi):**
   - Ana Mesaj: *"İnsan karar verir. Teknoloji yükü taşır."*
   - **KATI KURAL:** Ekranda metin olarak "Human × Machine" YAZILMAZ!
   - Görsel: İki iç içe geçen 3D cam halkanın uyumunu temsil eden 3D görsel.
4. **Bölüm 4 (Hizmetler - Sadece 4 Adet):**
   - `AI Agents`, `AI Automation`, `AI Integration`, `Custom AI Systems`. (Sıfır kart kalabalığı).
5. **Bölüm 5 (Nasıl Çalışıyoruz?):**
   - Hook: *"Önce anlarız. Sonra kurarız."*
   - 4 Adım: `Dinleriz → Analiz Ederiz → Tasarlarız → Geliştiririz`.
6. **Final CTA & Footer:**
   - Hook: *"İşletmeniz için AI nerede gerçekten işe yarar?"*
   - Alt Metin: *"Önce probleminizi anlayalım. Sonra gerçekten fayda sağlayacak çözümü birlikte tasarlayalım."*
   - CTA: `İşletmenizi Konuşalım`.
   - Footer: Resmi CyberGene logosu.

## AŞAMA 4 — TEKNİK MİMARİ VE UYGULAMA PITFALLS
- **Astro Native Entegrasyonu:** React SSR çakışmalarını (`NoMatchingRenderer`, `FailedToLoadModuleSSR`) önlemek için Three.js WebGL tuvallerini doğrudan katı `.astro` bileşenlerinde `<script>` içinde yazın.
- **Pencere Odaklama Kuralı:** Alfred ekran görüntüsü alırken Chrome'un öne geçmesi için `alfred browser <url>` komutunu kullanın; masaüstünde Telegram/ChatGPT uygulaması Chrome'u kapatmasın.
- **Lisans Temizliği:** Tüm kullanılan açık kaynak bileşenlerin MIT / Apache 2.0 açık kaynak lisansı teyit edilmelidir.
