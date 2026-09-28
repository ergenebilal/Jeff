# Konut / İlan Kaynakları (Türkiye) — erişim, uç noktalar, tuzaklar

Site politikaları değişir. Her taramadan önce §0 yoklamasını yap; sonuca göre bu dosyayı güncelle. Aşağısı "son kontrol edilen durum", kalıcı doğa kanunu değil.

## 0. Erişim yoklaması (tek satır, her site için)
```
curl -s -m 25 -o /tmp/x.html -w 'http=%{http_code} boyut=%{size_download}\n' \
  -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36" \
  -H "Accept-Language: tr-TR,tr;q=0.9" "<url>"
```
Okuma: `200` + büyük gövde = taramaya uygun · `403` = datacenter IP engeli · gövdede Cloudflare ara sayfası = bot kontrolü · "butona basılı tut" = interaktif insan doğrulaması (otomatikleştirilemez, bir denemede kes).

## 1. Emlakjet — açık, birincil kaynak
- **Liste HTML'i** sunucu tarafında render edilir; ld+json içindeki `@graph` dizisi `RealEstateListing` kayıtlarını verir: `name` (başlık), `url`, `offers.price`, `additionalProperty` (Oda Sayısı, Kat). `address`/`floorSize` boş gelebilir → mahalle ve m² için BFF ucunu kullan.
- **BFF JSON ucu** (en zengin, tarayıcısız çağrılır):
  `https://bff.emlakjet.com/pages/listing-search?path=%2Fkiralik-daire%2F<il>-<ilce>&language=tr`
  → `listing.items[]` (id, title, url, price, features, location, agent{name,type}) · `listing.pagination` (pageSize 30, totalItems, totalPages, hasNext) · `deferred.locationInsights` (**bölge ortalama kira, m² birim değeri, yıllık artış** — piyasa fotoğrafı buradan).
  **UYARI:** bu uç `page` / `pageNumber` / `sayfa` / `offset` parametrelerini YOK SAYAR, hep ilk 30 kaydı döner. Tam envanter için HTML sayfalarını sırayla çek.
- **Filtre sayaç ucu:** `https://filter-api.emlakjet.com/filter/api/v1/filter/fields/slug/<kiralik-daire/il-ilce>`
  → `fields[]` içinde `key=owner` (Kimden) alanının seçeneklerinde **kategori başına ilan sayısı** gelir: Tümü / Emlak Ofisinden / Sahibinden / Müteahhitten. "Bu ilçede kaç mal sahibinden ilanı var" sorusunun cevabı tek istekte budur; tüm envanteri boşuna çekmeden önce bunu sor.
- **Filtre yolu URL'de:** `/kiralik-daire/<il>-<ilce>/sahibinden` · `/kiralik-villa/.../sahibinden`.
  **DİKKAT:** `<ilçe>/sahibinden` yolu bazen ilçe daraltmasını kaybeder, il geneline yayılmış sonuç döner (ilk kart ilçeden, kalanı başka ilçeler). Sayfadaki kart sayısına güvenme — sayıyı sayaç ucundan doğrula.
- **Sayfalama:** HTML'de `?sayfa=2`, `?sayfa=3`. İlan kimliği URL sonundaki sayıdır. Kart/detayda "MÜLK SAHİBİ" veya "Emlak Ofisinden" etiketi ilan sahibi türünü verir.

## 2. Agregatörler
- **emlakclick.com** — sahibinden bölümü `<ilce>-sahibinden-kiralik-daire` kalıbında. Liste kartı ld+json'unda `price`, `addressLocality`, `floorSize`, `additionalProperty` (Oda Sayısı, Kat). Detay sayfasında **"İlan Sahibi → Sahibinden → Bireysel"** etiketi = mal sahibi. Telefon metinde maskeli (`+905

****6183`) görünür ama **tam numara kaynaktaki `wa.me/90...` bağlantısındadır**.
- **ilanlar.com** — `/emlak/kiralik-konut-daire/<il>/sahibinden` (il + sahibinden filtresi). Detayda "EİDS Onaylı" etiketi ve yayın tarihi bulunur (tazelik kontrolü için iyi kaynak). Sayfada görünen **0216'lı sabit numara sitenin müşteri hizmetleridir**, ilan sahibinin telefonu değil — iletişim sayfadaki "İletişime Geç / Hızlı Mesaj" üzerinden.
- **emlakgo.net** — `/kiralik-daire/<il>-<ilce>?page=2`. Verisi emlakjet ile aynıdır (görseller `imaj.emlakjet.com`'dan gelir); yedek/karşılaştırma kaynağı. Kart ayrıştırması metin tabanlı olduğu için "Sahibinden" etiketi komşu karta kayar — tek başına kanıt sayma.
- **zingat** kapanmış (404), **mitula/trovit/nestoria** datacenter IP'den 401/403 dönebilir. Uzun denemeye değmez; engellenirse bırak.

## 3. Engelli kaynaklar → kullanıcıya devret
Sahibinden.com (Cloudflare + interaktif "butona basılı tut" doğrulaması) ve hepsiemlak.com (datacenter IP'ye 403) sunucudan taranamaz. Bunlar Türkiye'nin en büyük iki havuzudur, yani kapsamın önemli kısmı orada. Teslimde:
- **Hazır filtreli link ver**: `sahibinden.com/kiralik-daire/<il>-<ilce>` → "Kimden → Sahibinden" → "Fiyat: en yüksek <bütçe>".
- **hepsiemlak** için `<ilce>-kiralik-<satıcı-türü>/daire` kalıbı (sahibinden filtresi URL yolunda hazır) — yalnız kullanıcı kendi tarayıcısından açabildiğini teyit ederse sun.
- Numaralı adımlar yaz; kullanıcı listeyi geri gönderirse kıyas tablosu çıkar.
- **Erişemediğin kaynağı "yok" sayma**; kapsamı açık yaz.

## 4. Teslim öncesi son kontrol listesi
- Her ilan aynı gün tekrar çekildi mi (fiyat + yayın tarihi)?
- 3 aydan eski ilanlar "muhtemelen tutulmuş" diye işaretlendi mi?
- Telefonlar `wa.me` bağlantısından teyit edildi mi? Sabit hat = site müşteri hizmetleri ayrımı yapıldı mı?
- Bütçenin bölge ortalamasına göre yeri söylendi mi (%X altında/üstünde)?
- Mal sahibinden ve emlakçıdan ilanlar ayrı bölümlerde mi?
