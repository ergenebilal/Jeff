# Ortak/Platform Ölçümü ve Pazar Fiyat Çıpası

## Ne zaman
- Potansiyel iş ortağı, platform veya hedef müşteri hakkında karar verilecekse
- Kendi teklifinin fiyatı kanıta bağlanacaksa (fiyat uydurma yasağı)
- "Bu iş büyük görünüyor" izlenimi sayıyla sınanacaksa

## 1. Envanteri say (tarayıcısız, halka açık)
Sitemap, bir işletmenin gerçek büyüklüğünü en hızlı veren kaynaktır.

```bash
curl -sL https://<site>/sitemap_index.xml | grep -oE '<loc>[^<]+</loc>'
curl -sL https://<site>/sitemap_index.xml | grep -c '<sitemap>'
```

Alt sitemap adları envanteri söyler:
- `product-sitemap*.xml` → WooCommerce ürünleri. Bir "listeleme" işi kurulmuşsa **ürün = listelenen kişi/kurum** (örn. hekim profili); sayısı doğrudan envanterdir
- `post-sitemap` / `page-sitemap` → içerik hacmi (SEO yatırımı göstergesi)
- `pa_*`, `product_cat`, `*_tag` → facet/taksonomi sayfaları = SEO derinliği, **müşteri değil**

Her alt sitemaptaki `<loc>` sayısını ayrı say ve tek tabloya yaz. Taksonomi URL'lerini "içerik" ya da "müşteri" sayısı gibi sunma. `sitemap.xml` 301 dönebilir; `sitemap_index.xml` çoğu WordPress kurulumunda doğru yoldur.

## 2. Para gerçekten dönüyor mu
- Fiyat sayfasını `page-sitemap` içinden bul: `fiyatlandirma`, `paketler`, `premium`, `<kitle>-ozel`
- **Ödeme kuruluşu adı** (PayTR, iyzico, Stripe, LemonSqueezy) geçiyorsa ürün fiilen satılıyor. Yalnızca "bize ulaşın" varsa **fiyat bilinmiyor** diye yaz — tahmin etme
- Fiyat tablosu markdown çıkarımında sıklıkla kaybolur (görsel/tablo bileşeni). **Ham HTML'de ara**:
```python
import re, urllib.request
html = urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})).read().decode('utf-8','ignore')
re.findall(r'([0-9][0-9.,]{2,7})\s*(?:TL|₺)', html)                 # fiyat adayları
re.findall(r'ayl[ıi]k[^<]{0,40}', html)                           # "Aylık 2.500 ₺"
re.findall(r'(Standart|Prestij|Premium|Pro|Başlangıç)', html, re.I)  # paket adları
'paytr' in html.lower()                                            # ödeme kanalı kanıtı
```
- Aylık ve yıllık fiyatı birlikte al; hangi taahhüde bağlı olduğunu yaz. "İlk N müşteri için lansman fiyatı" gibi kayıtlar fiyatın geçici olduğunu gösterir.

## 3. Karşı tarafın sosyal kanalını okurken
- Takipçi/gönderi sayısını ve **son gönderi tarihini** iki bağımsız okumada doğrula (`instagram-public-okuma`); tek okuma kanıt değildir. Son gönderi tarihi kanalın canlı olup olmadığını söyler; bio'daki kayıt/satış linki iş modelini verir.
- Gönderi görsellerinin CDN bağlantıları oturuma bağlıdır, sonradan indirilemez. Görsel dil için sayfayı aynı tarayıcı oturumunda aç, ekran görüntüsü al.

## 4. Rapor kalıbı (bu sırayla)
1. **Doğrulanan veriler** — her satır kaynaklı (sitemap sayımı, canlı sayfa okuması); doğrulanamayan "doğrulanamadı" etiketli
2. **Fiyat çıpası** — pazarda bu ihtiyaç için ödenen gerçek bedel + kaynağı
3. **İki tarafın envanteri** — varlık / gelir / zayıf nokta / güçlü nokta tablosu
4. **2-3 iş birliği modeli** — her biri için artı / eksi / uygunluk (hız, ölçek, sermaye ihtiyacı)
5. **Sorulacak sorular** — cevap almadan teklif konuşulmaz
6. **Riskler ve kırmızı çizgiler**
7. **Tek net önerilen adım** (pilot)

## 5. Görüşmede sorulacak zorunlu sorular
1. **Kaç müşteri ÜCRETLİ abone, aylık ciro ne?** (kayıt sayısı ciro değildir)
2. Müşterilerden gelen şikâyet ne? Bizim tezimizi doğruluyor mu?
3. **Kendi müşteri kitlenize bizi önermemize izin verir misin?** (kanal erişimi en değerli kalem)
4. Karşı taraf neyi büyütmek istiyor: mevcut işi mi, yeni gelir hattı mı?
5. Karar kimde, gelir payı nasıl?
6. Diğer girişimleri nerede duruyor, orada iş var mı?

## 6. Kırmızı çizgiler
- Kayıtlı müşteri sayısını ciro gibi sunma.
- Ortağın doğrulanmamış iddiasını kendi teklifine taşıma.
- Sermaye isteyen modele girme; sermayesi olmayan taraf için model **emek + sistem karşılığı gelir payı** olmalı.
- Fiyat, ödeme sinyali gelmeden konuşulmaz; ortaklık konuşması yerine ölçülebilir pilot öner.
- Mevzuat kısıtı ortaktan bağımsızdır: sağlıkta karşılaştırma/garanti/fiyat dili iki tarafta da yasak.
