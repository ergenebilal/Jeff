---
name: ticari-dogrulama
description: Use when turning a finding into an offer or price.
---

# Ticari Doğrulama Sıralaması (ZORUNLU)

## Temel ilke
Bir problemin **teknik olarak gerçek** olması, **ticari olarak acı verdiğini** veya müşterinin **ödeme yapacağını** kanıtlamaz. Üç ayrı iddiadır, üçü ayrı kanıt ister.

## Zorunlu sıra
1. **OBSERVE** — gerçek dünyadan bulgu → `OBSERVED`
2. **VERIFY** — birden fazla bağımsız sinyalle yanlış pozitifi ele → `VERIFIED` (ticari acı iddiası YOK)
3. **REASON** — ADE çalıştır → `ADE VERDICT`
4. **TEST INTEREST** — kontrollü temas, **ürün/fiyat satmadan** → `INTEREST VALIDATED/NOT VALIDATED/INCONCLUSIVE`
5. **VALIDATE NEED** — müşterinin ağzından ihtiyacı öğren → `NEED VALIDATED/...`
6. **TEST PAYMENT** — "istiyor mu" → "para öder mi" → `PAYMENT VALIDATED/REJECTED/UNKNOWN`
7. **QUANTIFY** — ekonomik etki, bütçe, alternatif maliyeti, zaman/kapsam
8. **PRICE** — ancak kanıt yeterliyse

## Adım 3'te ADE'ye sorulacak zorunlu sorular
- Bu problemin işletme için önemli olması **neden mümkün**?
- **Neden önemsiz olabilir**?
- Başka **makul açıklamalar** var mı?
- İşletme bunu **zaten başka bir yöntemle çözüyor** olabilir mi?
- Müşteri **neden para ödesin**? **Neden ödemesin**?
- **Rakip/alternatif** çözüm nedir?
- Bu hipotezi **en ucuz hangi deney** test eder?

## Adım 4 — ilgi testi kuralları (en sık ihlal edilen adım)

**YASAK:** fiyat, paket adı, "şunu yaparız", hizmet listesi, aylık ücret, retainer, teklif dosyası.
**SERBEST:** gözlenen bulgu, rakip karşılaştırması, "farkında mıydınız?" sorusu, kısa özet teklifi.

Mesaj iskeleti:
> Merhaba, [İŞLETME] için kısa bir dijital kontrol yaptım. [BULGU 1 — gözlenen]. [BULGU 2 — rakip karşılaştırması]. Bunun farkında mıydınız? İsterseniz 3 maddelik kısa özeti paylaşabilirim.

**Ölçülecek 4 sinyal** (bunlar doldurulmadan sonraki adıma geçilmez):
`cevap_verdi` · `ilgilendi` · `farkindaydi` · `gorusme_kabul`

**Ölçüm penceresi:** 7 gün (KILL FAST kuralı — motorun önerdiği 4 hafta sahaya inmez).
**Kill kriteri:** hedeflerin tamamı yanıtsız VEYA tamamı "kendim hallederim" → strateji ölür, uzatılmaz.

## Adım 5 — ihtiyaç doğrulama soruları (görüşmede)
Problemi biliyor muydunuz? · Şu anda nasıl çözüyorsunuz? · Bu size neye mal oluyor? · Daha önce çözmeye çalıştınız mı? · Çözülmesi ne kadar önemli? · Ne zaman çözmek istersiniz?

## Sık yapılan hatalar (gerçek ihlallerden)
1. **Fiyatı erkenden yazmak.** 1-2-3 yapılıp 4-5-6-7 atlanırsa ortaya "satılık ama alıcısız" teklif çıkar. Kanıt yerine artefakt üretmek = üretken görünmek tuzağı.
2. **ADE "TEST" verdictini "satışa geç" sanmak.** TEST = **ilgi testine geç** (adım 4). Satış izni değildir.
3. **Teknik kusuru ticari acı sanmak.** "Site ölü" gözlemi "para kaybediyor" iddiası değildir; ikincisi kanıt ister.
4. **Niş normunu kontrol etmemek.** Bir kusur o nişte yaygınsa (ör. 20 kliniğin 11'inde site yok) satış argümanı değildir. Önce "rakiplerde nasıl?" sorusunu yanıtla.
5. **Müşterinin güçlü olduğu alanı satmaya çalışmak.** Instagram'ı 7.153 takipçi / 451 gönderi olan kliniğe "içerik üretelim" demek teklifi öldürür.
6. **İlgi testinde bulgu yerine çözüm anlatmak.** Adım 4'te amaç müşterinin problemi fark edip etmediğini ölçmek — çözümü anlatmak sinyali kirletir.

## Kanıt katmanı etiketleri
`VERIFIED` · `OBSERVED` · `STRONGLY LIKELY` · `HYPOTHESIS` · `UNKNOWN` — raporda her iddia etiketlenir. UNKNOWN'ı gerçek gibi kullanma.

## Nerede dosyalanır
- Gönderim listesi + ölçüm: `/home/hermes/fpc/cevap-log.csv` (noktalı virgülle ayrılmış, BOM'lu)
- Raporlar: `/home/hermes/fpc/raporlar/`
- ADE kayıtları: `/home/hermes/fpc/raporlar/ade-muhakeme-*.md`
