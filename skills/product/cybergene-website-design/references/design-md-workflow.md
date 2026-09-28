# DESIGN.md Yaklaşımı — CyberGene Frontend İçin

## Kaynak Repo
`github.com/VoltAgent/awesome-design-md` — 73 markanın tasarım dili tersine mühendislikle çözülmüş, her biri `DESIGN.md` formatında. Google Stitch formatı — düz markdown, Figma/JSON gerektirmez. AI ajanına "bu DESIGN.md'yi baz al, şu sayfayı yap" demek yeterli.

## CyberGene İçin En Yakın Referanslar
- **VoltAgent** (`getdesign.md/voltagent/design-md`) — void-black canvas, emerald accent, terminal-native. Bizim paletimize en yakın.
- **Framer** (`getdesign.md/framer/design-md`) — bold, motion-first, design-forward. Hero bölümü için ilham.
- **Linear** (`getdesign.md/linear.app/design-md`) — ultra-minimal, precise, purple accent. Temizlik referansı.
- **Vercel** (`getdesign.md/vercel/design-md`) — black-white precision. Sadelik örneği.

## Kullanım Protokolü
1. Hedef DESIGN.md'yi indir: `curl -o DESIGN.md https://getdesign.md/<marka>/design-md`
2. Proje köküne at: `C:\Users\lenovo\cybergene-web\DESIGN.md`
3. Aider/jcode'a görev ver: "Bu DESIGN.md'yi baz al, ama CyberGene marka kimliğiyle (antrasit zemin, Mor→Mavi→Yeşil gradient, Archivo Black başlık) yeniden yaz."
4. İnsan×Makine felsefesi ve anti-generic-AI-ajans kuralları her zaman üstünde tutar.

## Ȕnemli Uyarı
DESIGN.md dosyaları tersine mühendislik ürünü — marka dilini doğrudan müşteri sitesine taşımak ticari risk taşır. Referans olarak kullan, birebir kopyalama.

## Mevcut Site Stack (cybergene-web)
- **Framework:** Astro (src/components/*.astro)
- **Stil:** Tailwind CSS + global.css (design tokens CSS variables olarak)
- **Fontlar:** Archivo Black (başlık), Manrope (gövde), JetBrains Mono (badge/mono)
- **Renk tokenları:** `--bg-base: #0B0F0D`, `--purple: #A855F7`, `--blue: #3B82F6`, `--green: #10B981`
- **Konum:** `C:\Users\lenovo\cybergene-web\`
- **Dev server:** `cd C:\Users\lenovo\cybergene-web && npx astro dev --port 4321`
- **Bileşenler:** Hero, Navbar, Services, ProblemSection, SolutionsSection, HumanMachineSection, ProcessSection, HonestAiSection, Trust, Contact, Footer, WhyCyberGene

## Astro Bileşen İpuçları & Dosya Transfer Pitfalls

### 1. Astro Native SVG vs React Hydration
- Astro projelerinde dikey/curved animasyonlu akışlar (Animated Beam, telemetri panelleri vb.) için React `client:load` veya `client:only` kullanmak yerine yerel `.astro` bileşeni içinde yerleşik SVG `<animate>` ve SVG `stroke-dashoffset` animasyonu tercih edin.
- **Neden:** React client hydration gecikmelerini, `No matching renderer found` SSR hatalarını ve ilk mount sırasında `getBoundingClientRect()`'in 0 dönmesi sonucu oluşan boş render bug'larını engeller. 0ms gecikmeyle her cihazda anında ve sorunsuz çalışır.

### 2. Windows Node'a Büyük Dosya Transferi (CLI Limit Pitfall)
- Pablo / Alfred üzerinden Windows node'una 5KB+ büyük dosya yazarken inline PowerShell komutlarına tek satırda dev Base64 dizesi koymak `The command line is too long` (Windows 8191 karakter CLI sınırı) hatası verir.
- **Çözüm:** Dosyayı sunucuda `/tmp/` altında hazırlayın, ardından Python ile 1500 byte'lık parçalara bölerek PowerShell `[System.IO.FileMode]::Append` veya parça Base64 akışı ile parçalı olarak aktarın.

## Dev Server Başlatma (Pablo Üzerinden)
Pablo `CREATE_NO_WINDOW` ile çalıştığından `&` operatörü PowerShell'de çalışmaz. Background başlatmak için:
```bash
alfred shell "powershell -command \"Start-Process cmd -ArgumentList '/c cd C:\\Users\\lenovo\\cybergene-web && npx astro dev --port 4321' -WindowStyle Hidden\""
# Ardından 10 saniye bekle, sonra alfred browser 'http://localhost:4321'
```
