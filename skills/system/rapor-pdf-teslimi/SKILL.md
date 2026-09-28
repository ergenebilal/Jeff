---
name: rapor-pdf-teslimi
description: Use when a report or deliverable PDF is wanted.
---

# Rapor → PDF → Telegram teslimi

## Ne zaman
Bilal "rapor oluştur", "strateji çıkar", "pdf olarak ilet", "kapsamlı bir rapor" dediğinde. Beklenen: **tek dosya, tam içerik, PDF** — dağınık dosya listesi değil.

## Zorunlu akış
1. **Önce markdown yaz** (proje klasöründe kalsın) — PDF yeniden üretilebilsin, kaynak metin kaybolmasın.
2. **PDF'e çevir:**
   ```
   python3 ~/.hermes/skills/system/rapor-pdf-teslimi/scripts/md_pdf.py girdi.md cikti.pdf "Rapor Başlığı"
   ```
   Geniş tablolu liste (7+ kolon) için yatay: `... md_pdf.py --csv-kapi liste.csv cikti.pdf`
3. **Doğrula (atlanmaz):** sayfa sayısı + dosya boyutu + **Türkçe harfler**. `pypdf` ile metni çıkar; `şğıİöüçŞĞÖÜÇ` görünmeli. Yatay istendiyse `page.mediabox.width > height` olmalı.
   Ardından **otomatik kusur denetimi** (regex taraması, PDF metni üzerinde) — hepsi 0 olmalı:
   `<br>|&nbsp;|&lt;` · `[ÍÃÅþýð\u0307]` · `Yıldırım'de|Mudanya'de` · `\S  +\S` (çift boşluk) · `\w·` (kaybolan satır kırılması) · `^>\s*$` (tek başına alıntı işareti).
   Yapısal tutarlılık: blok sayısı hedeflenen sayıya eşit mi, numaralandırma 1..N sıralı mı.
   **Doğrulama scriptini `write_file` ile `.py` olarak yaz, `python3 dosya.py` ile çalıştır.** Komutu terminal satırına gömme: doğrulama regex'lerinin kendisi (`&nbsp;`) komut metninde ampersand taşır ve guard komutu arka planlama sanıp reddeder — bir tur kaybedersin.
   Hazır script: `python3 scripts/pdf_dogrula.py <pdf> [--yatay] [--bekle "<metin>"]` — bu kontrollerin tamamını tek komutta yapar, kusur bulursa çıkış kodu 1 döner. Rapora özel ek kontrol gerekiyorsa scripti kopyalayıp genişlet; satır içi komut yazma.
4. **Teslim:** yanıtta her dosya için ayrı `MEDIA:/mutlak/yol` satırı + üstüne **jargonsuz sade dil** özeti (içinde ne var + en kritik 3-5 bulgu). Tabloyu sohbet mesajına yapıştırma — Telegram'da bozulur, PDF gönderilir.

## Pitfall'lar (her biri bir kez zaman kaybettirdi)
- **`landscape=True` tek başına yatay yapmaz:** sayfa CSS'inde `@page { size:A4 }` varsa Chromium CSS'i üstün sayar. Yatay için CSS'te `size:A4 landscape` yazılmalı.
- **Fontlar `set_content()` ile yüklenmez:** doküman kaynağı `about:blank` olur, `file://` font/görsel sessizce düşer (`document.fonts` durumu `error`), PDF sistem fontuyla çıkar. HTML'i diske yaz, `pg.goto('file://'+yol)` ile aç.
- `pg.pdf()` öncesi `await document.fonts.ready` bekle; arka plan görseli varsa `img.decode()` ile yüklenmesini bekle.
- **Türkçe glif kontrolü zorunlu:** kullanılan TTF'ler ş/ğ/İ/ı içermeli; doğrulamayı PDF metninden yap, varsayma.
- `text-transform:uppercase` Türkçe başlıklarda yanlıştır (i→I); büyük harfler elle yazılır.
- **Markdown kaynağına ASLA HTML yazma (`<br>`, `&nbsp;`, `<b>`).** Dönüştürücü `html.escape()` uygular; etiket PDF'te **düz metin olarak** basılır (85 mesajlık metinde 1601 kez `<br>` göründü, kelimeler birbirine yapıştı). Kural: her satır için bir `>`; çok satırlı blok dönüştürücüde kendiliğinden birleşir, boş `>` satırı paragraf arası boşluk üretir. Tek `>` + `<br>` yöntemi terk edildi.
- **Kaynak veriyi NFC'ye normalize et (Türkçe bozulma kökü).** Google Places / API verisi `İ` harfini `I` + U+0307 (birleşik nokta) olarak döndürür; ekranda "İş Birliğı", "Önizleme", garip boşluklar olarak görünür. `unicodedata.normalize('NFC', t).replace('I\u0307','İ')` ile JSON/CSV temizlenir (bir işte 1568 bozuk işaret düzeldi). Hem render hem veri dosyası normalize edilir.
- **Türkçe ek uyumu ilçe adlarında:** `{ilçe}'de` şablonu "Yıldırım'de" üretir (yanlış). İlçe→ek sözlüğü tutulur (Nilüfer'de, Osmangazi'de, **Yıldırım'da**, Mudanya'da, Gemlik'te, İnegöl'de, Gürsu'da, Kestel'de). Yeni şehir/ilçe eklendiğinde sözlük güncellenir.
- **PDF'ten kopyalanan metin bozuk çıkmasın:** CSS'te `font-variant-ligatures:none; font-kerning:none; text-rendering:geometricPrecision; hyphens:none`. Ligatür (`ﬁ`) ve kerning, metin çıkarımına sahte boşluk sokar ("say falık").
- **Font dışı sembol kullanma:** `① ② ③` gibi glifler yedek fonta düşüp ekstra boşluk/bozulma üretir — `1) 2) 3)` yaz.
- **Emoji de aynı sınıfa girer — özellikle TABLO hücrelerinde:** `✅ ❌ 🟢 🟡 🔴` yedek emoji fontuna düşer ve arkasında fazladan bir boşluk glifi bırakır; `\S  +\S` (çift boşluk) kapısı satır satır tetiklenir (12 sayfalık bir denetim raporunda 22 isabet, hepsi emoji satırları). **Kapıyı gevşetme — sembolü metne çevir:** `✅→OK`, `❌→YOK`, `⚠→KISMİ`, `🟢/🟡/🔴→` başlıktaki sözcük (`KORU`/`ONAR`/`BIRAK`). Başlık ve gövdedeki `·  —  →  ₺` gibi işaretler standart fontlarda olduğu için kalabilir.
- **Görsel doğrulama yolu:** `pdftoppm`/`pdf2image`/`wand` bu makinede olmayabilir; sayfayı rasterize etmek gerekirse PyMuPDF (`fitz`) kullan — `fitz.open(pdf)[i].get_pixmap(dpi=100).save(png)`. Metin tabanlı denetim (pypdf) her zaman birinci yol; raster yalnız gözle bakmak gerektiğinde.
- **Kapak/başlıkta ham veri adı kullanma:** 100 karakterlik Google işletme adı başlığa girerse düzen çöker. `kisa_ad()` ile ilk anlamlı parça alınır (ilk `&`, `|`, `(` veya ` - ` öncesi; 34 karakter sınırı; tümü büyük yazılmış kelimeler Türkçe-güvenli başlığa çevrilir).
- **Kalan markdown işaretleri PDF'te görünür kalır:** metin başka bir kanal için biçimlendirilmişse (`*kalın*` WhatsApp biçimi) PDF'e girmeden yıldızlar temizlenir. Kaynağı yazarken iki render üretilir: kanal biçimi (CSV) + düz metin (PDF).
- Çok kolonlu tablo dikey A4'te sıkışır: yardımcı kolonları (puan/öncelik) çıkar ya da yataya geç.
- Dosya adları numaralı ve okunur olsun (`1-...pdf`, `2-...pdf`) — indirme sırası belli olsun.

## İçerik kuralları (Bilal'in beklentisi)
- **Durum/ilerleme raporu isteniyorsa veri toplama blokları ve rapor iskeleti hazır:** `references/durum-raporu-veri-toplama.md` (sistem ölçümü, gelir hunisi sayıları, bölüm sırası). Sayılar oradan gelir; ölçülmeyen sayı rapora yazılmaz.
- **Kapsamlı** tek doküman: numaralı bölümler, her iddia veriye bağlı, tarih/kaynak yazılı.
- Doğrulanmış veri ile varsayım ayrılır; "erişilemedi / doğrulanamadı" etiketi açıkça yazılır.
- Fiyat, ciro, süre gibi sayılar uydurulmaz; mümkünse hedefin/kullanıcının kendi verisinden çıpa alınır (kendi fiyat listesi, kendi ölçümü).
- **Sonuç raporlarında "hazırladık" ile "sonuç aldık" ayrı satırlarda durur.** Huni tablosu (gönderilen / yanıt / görüşme / satış) sıfır olsa da yazılır; sıfır sayı gizlenirse rapor "iş yapıldı" izlenimi verir ve karar yanlış yere kayar. Kaydı tutulmamış olabilecek satırı kesinleştirme: "son kayıt tarihi X, sonrasında elle yapıldıysa işlenmemiş" diye etiketle.
- Bilal'e giden mesajda **sayı içeren tablo yapıştırma**; en kritik 3-5 bulguyu düz satırlar halinde sade dille anlat, tabloyu PDF'e bırak.
- Sonunda **tek sayfa özet** (yapılacaklar sırası) bulunur.

## Script
- `scripts/md_pdf.py` — markdown→PDF (başlık, tablo, liste, kalın, alıntı destekli) ve CSV→yatay PDF. Bağımlılık: `playwright` (Chromium).
- `scripts/pdf_dogrula.py` — teslim öncesi PDF denetimi: sayfa/karakter sayısı, Türkçe glif kontrolü, kusur regex'leri, `--yatay`, `--bekle "<metin>"`. Bağımlılık: `pypdf`. Kusur bulursa çıkış kodu 1.
