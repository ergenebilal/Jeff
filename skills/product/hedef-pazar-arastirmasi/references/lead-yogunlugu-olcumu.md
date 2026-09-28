# Lead Yogunlugu Olcumu ve Pazar Karsilastirmasi (calisan tarif)

## Google Places (New) — calisan kod deseni

```python
# GOOGLE_API_KEY ~/.hermes/.env icinde
url = "https://places.googleapis.com/v1/places:searchText"
body = json.dumps({"textQuery": query, "languageCode": "tr", "maxResultCount": 20}).encode()
req = urllib.request.Request(url, data=body, headers={
    "Content-Type": "application/json",
    "X-Goog-Api-Key": key,
    "X-Goog-FieldMask": "places.displayName,places.rating,places.userRatingCount,places.websiteUri,places.formattedAddress,places.nationalPhoneNumber,places.businessStatus"
})
```

Pitfall: `X-Goog-FieldMask` olmadan API 200 doner ama alanlar bos gelir — maske sart. Saha adlari dahil hicbir sey normalize edilmez.

Pitfall: **legacy `maps.googleapis.com/maps/api/place/textsearch/json` ulumasi REQUEST_DENIED "LegacyApiNotActivatedMapError" verir** — projede yeni (v1) API aktif, eski degil. Yalnizca `places.googleapis.com/v1/places:searchText` (New) kullan.

## Tek sorgu 15-20 sonuc verir — coklu sorgu + dedup sart

Bir `searchText` cagrisi max ~15-20 sonuc doner; tum pazarı gormek icin ayni nise es anlamli **5-6 farkli sorgu** at (`"{sehir} emlak ofisi"`, `"... gayrimenkul danismanlik"`, `"... danismanlik ofisi"`, `"... gayrimenkul ofisi"`, `"turyap ofisi"`, `"coldwell banker {sehir}"`), sonra yerId'ye gore dedup et. Tek sorgu pazar yogunlugunu EKSIK gosterir. Sehirden tasan sonuclari kesmek icin body'ye `locationRestriction.rectangle` (low/high lat-lng) ekle — `textQuery`'e bolge koymak yetmez, rectangle kati sinir koyar:

```python
body = json.dumps({"textQuery": q, "languageCode": "tr", "maxResultCount": 15,
  "locationRestriction": {"rectangle": {"low": {"latitude": 40.10, "longitude": 28.85},
  "high": {"latitude": 40.35, "longitude": 29.30}}}}).encode()
# her sorgu arasi ~1s uyku (rate limit)
# ciktiyi baska domain/host degil yerId ile dedup et
```

## WebsiteUri Sınıflandırması (dijital açık ölçümünde kritik)

Bir lead'in `websiteUri`'si çoğu zaman kendi sitesi degildir. Dijital açık oranını hesaplarken 'uri var' degil **gerçek sınıf** sayilir:

| `websiteUri` host | Sınıf | Dijital açık? |
|---|---|---|
| sahibinden.com / remax.com.tr / turyap.com (portal profili) | `PORTAL_ONLY` | EVET — kendi sitesi degil |
| instagram.com | `IG_ONLY` | EVET — site yok |
| bağımsız domain ama açılmıyor (timeout/HTTP hata) | `OLU_SITE` | EVET — ölü yatırım |
| bağımsız domain, açılıyor | `SITE_ACIK` | HAYIR — gerçek site |
| uri boş | `WEBSITE_YOK` | EVET |

Sınıflandırma host aramasiyla (`sahibinden.com|instagram.com|remax.com.tr|turyap.com`), sonra bağımsız domainler fiilen indirilip `aciliyor` testiyle. Yalnizca `SITE_ACIK` gerçek site sayilir.

**Saha ornegi (Bursa emlak, Eylul 2026):** Google Places'ta 'web siteli' görünen 54 ofisin sadece 9'unda gerçek çalışan site vardı; %67'si portal-only/ölü-sit/ıl/boş çıktı. 4.9★ + 144 yorumlu ofis sitenin açılmadigi örnegi, 'Google'da itibarın var ama siten ölü — o aramalar rakibe gidiyor' kapanisinin en keskin satis acisi olur (masa-basi % kayba degil gerçek tespite dayanir). Digital-gap ölçümü kodla (urllib), LLM sadece sentezde.

## Bursa olcumu (Eylul 2026 — tekrar ocecek referans)

| Nis | Sonuc/sayfa | Yorum ort | Web orani |
|-----|-------------|-----------|-----------|
| Dis klinigi | 20+ | ~296 | %95 |
| Sac ekimi | 18-20 | ~140 | %80 |
| Medikal estetik | 20+ | ~465 | %95 |
| Guzellik salonu | 20+ | ~653 | %70 |
| Emlak / mobilya | 20 | ~101-247 | %80 |
| Tadilat | ~20 | ~36 (dusuk!) | %75 |
| Avukat | 20 | ~150 | %100 |
| CNC/metal | 16-20 | ~5 (cok dusuk) | %80 |

Notlar:
- Avukat web %100 = pazar dijital olarak dogmus, acik az.
- Tadilat/CNC yorum ortalamasi cok dusuk = dijital olgunluk dusuk — audit icin bosluk olabilir ama isletme kucuk.
- Istanbul ayni nislerde 6-10x daha buyuk oyuncular uretiyor (yorum ort 1.5K+): hedef orta olcek Bursa.

## Puanlama tablosu format

Her nis icin tek satir: pazar buyuklugu (kaynak), musteri degeri (kaynak), lead yogunlugu (olcum), dijital acik (gozlem), rekabet (kaynak), ulasilabilir sayi (olcum), satilabilirlik (cikarim), yetenek uyumu (cikarim) → TOPLAM. Kaynaksiz hucre "VERI YOK".
