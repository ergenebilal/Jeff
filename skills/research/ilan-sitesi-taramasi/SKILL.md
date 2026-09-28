---
name: ilan-sitesi-taramasi
description: "Use when a Turkish listing/housing search is asked."
---

# İlan Sitesi Taraması (Türkiye)

Kullanıcı "şu ilçede kiralık/satılık daire ara", "sahibinden olsun", "en fazla X TL" gibi bir **ilan araştırması** istediğinde bu akışı uygula. Amaç: erişilebilir tüm kaynakları tarayıp, kriterlere uyan ilanları doğrulanmış telefon/link ile tek raporda teslim etmek.

## Kural 0 — "Sahibinden" site adı değil, SATICI TÜRÜ
Kullanıcı "sahibinden olsun" dediğinde kriter **mal sahibinden doğrudan kiralamak** (emlakçı komisyonu yok). `sahibinden.com` adıyla karıştırma. Her ilan sitesinde ayrı bir **"Kimden"** filtresi vardır (Sahibinden / Emlak Ofisinden / Müteahhitten) ve bu etiket ilan kartında/detayında ayrıca okunur. Raporda "mal sahibinden" ile "emlakçıdan" ilanları AYRI bölümlerde ver — komisyon farkı kullanıcının asıl derdi.

## Adım 1 — Erişim yoklaması (en ucuz iş önce)
Aday sitelerin her birine tek istek at, sonucu not et (komut: references/konut-ilan-kaynaklari.md §0). Yorumlama: `200 + büyük gövde` = açık · `403` = IP engeli · Cloudflare ara sayfası = bot kontrolü · **"butona basılı tut" / interaktif insan doğrulaması = otomatik geçilemez, TEK denemeden sonra bırak.**
Bot korumasını aşmaya çalışmak (stealth tarayıcı, headful Xvfb, user-agent değiştirme) bu işin en pahalı tuzağıdır: o challenge'lar bilerek otomatikleştirilemez tasarlanır, uzun süre yer ve tek ilan kazandırmaz. Engelli siteyi atla, Adım 4'e geç.

## Adım 2 — Açık sitede gizli JSON ucunu bul
Modern ilan siteleri (Next.js/BFF mimarisi) listeyi sunucu tarafında JSON ile besler. Sırayla dene:
1. **HTML'in kendisi**: `ld+json` blokları (`@graph` içinde `RealEstateListing`) — fiyat, başlık, oda, ilan linki gelir; `address`/`floorSize` çoğu zaman boş.
2. **BFF ucu**: tarayıcı ağ trafiğinde `bff.<domain>/pages/listing-search?path=<slug>` gibi bir uç; curl ile doğrudan çağrılır ve en zengin veriyi (ilan sahibi adı/türü, konum, özellikler, sayfalama, bölge ortalama kira) verir.
3. **Filtre/sayaç ucu**: `filter-api.<domain>/.../fields/slug/<slug>` — kategori (Kimden) başına **ilan sayısını** tek istekte döner.
`Sayaç ucunu, tam listeyi çekmeden ÖNCE çağır`: "bu ilçede kaç mal sahibinden ilanı var" sorusunun cevabı budur ve tüm envanteri çekmeye değip değmeyeceğini söyler.

## Adım 3 — Tam envanteri çek ve tekilleştir
- Sayfalama genelde **sitede** `?sayfa=N` yolundadır; JSON ucu sayfa parametresini yok sayıp hep ilk sayfayı dönebilir. Her iki yolu dene, HTML sayfalarını sırayla çek, her sayfadaki `ld+json` kayıtlarını topla.
- Aynı ilan birden fazla kaynakta ve farklı fiyatla görünür (biri bayat). **İlanın kendi kaynak sayfasındaki fiyat esastır**; liste/özet sayfasındaki fiyata rapor etme.
- Kayıtları ilan URL'i veya kimliği (URL sonundaki sayı) üzerinden tekilleştir; toplam sayıyı sitenin kendi sayacıyla karşılaştır.

## Adım 4 — Agregatörlere geç (engelli sitelerin yerine)
Büyük site engelliyse aynı ilanları toplayan agregatörler çalışır ve birçoğunda "Sahibinden" bölümü hazırdır (site bazlı kalıplar: references/konut-ilan-kaynaklari.md §2). Agregatör verisi bayat veya etiketi kaymış olabilir: agregatör "sahibinden" diyorsa raporda kaynağını yaz, ilanın kendi sitesinden teyit et.

## Adım 5 — Doğrulama (rapor yazmadan önce, zorunlu)
- Her ilanı **aynı gün** tekrar çek: fiyat ve **yayın tarihi** teyidi. Liste sayfası ile detay sayfası farklı fiyat gösterebilir.
- **3 aydan eski ilanı "muhtemelen tutulmuş" diye işaretle** — kullanıcı boşuna aramasın.
- Telefon: ekranda maskeli gösterilir (`+905

****6183`) ama **tam numara sayfa kaynağındaki `wa.me/<numara>` bağlantısında durur**. Metinden kopyalamaya çalışma, kaynağı oku.
- Sayfada görünen sabit hatlı (0216/0212) numara **sitenin müşteri hizmetleri** olabilir, ilan sahibinin numarası değil — öyle sunma.
- Numara vermeden önce `wa.me` bağlantısıyla eşleştir; yanlış numara vermek tüm raporu çöpe atar.

## Adım 6 — Teslim (bu kullanıcının formatı)
- **Tek dosya rapor** yaz (`/home/hermes/<konu>/<KONU>-RAPOR-<tarih>.md`) ve Telegram'a `MEDIA:/tam/yol.md` ile gönder. Dağınık dosya listesi teslim değildir.
- **Jargonsuz sade dil**; "yaptık/ettik" çoğul dil, "yaptım" değil. Teknik terim, dosya adı, uç nokta adı kullanıcıya giden metinde geçmez.
- Rapor sırası: (1) tepede sonuç — "kriterlere uyan N ilan", (2) mal sahibinden ilanlar: fiyat / mahalle / oda / m² / kim / telefon / link / özellik, (3) piyasa fotoğrafı — en düşük, medyan, ortalama ve "bütçen ortalamanın %X altında" cümlesi, (4) bütçeye uyan ama emlakçıdan olanlar (komisyon uyarısıyla), (5) **erişemediğin kaynaklar + kullanıcının kendisinin 1 dakikada bakacağı hazır link ve numaralı filtre adımları**, (6) önerilen sıradaki aksiyon + telefonda sorulacaklar (depozito, aidat, ısıtma, eşyalı mı, boşalma tarihi, aracı var mı).
- **Kapsam dürüstlüğü**: erişemediğin kaynağı "yok" sayma, kapsamı açıkça yaz ("erişebildiğim kaynaklarda şu kadar"). Kısmi sonucu "kapsamlı tarama" diye sunmak yasak; engelli kaynağın büyüklüğünü söyle ki kullanıcı kendi gözüyle baksın.
- Kullanıcının işini kolaylaştır: listeyi geri getirirse kıyas tablosu çıkaracağını söyle.

## Tuzaklar (hepsi zaman yaktı)
- İnteraktif bot challenge'ı denemek = en pahalı yol. Tek deneme, sonra alternatif.
- Liste sayfasındaki kart sayısına güvenip envanteri "toplam" sanma; sitenin sayaç ucundan doğrula.
- Aynı ilanın iki sitede iki fiyatı olur; detay sayfası + tarih teyidi yapılmadan fiyat yazma.
- Agregatörün "Sahibinden" etiketi HTML ayrıştırmasında komşu karta kayabilir; tek başına kanıt sayma.
- Fiyat kriterini sadece istekteki üst sınıra göre süzmek yetmez; kullanıcının bütçesi bölge ortalamasının altındaysa bunu açıkça söyle, "buldum" diye sevindirip piyasa gerçeğini saklama.

## Referans
- `references/konut-ilan-kaynaklari.md` — erişim yoklaması komutu, site bazlı erişim durumu, gizli uç noktalar, filtre/sayfalama URL kalıpları, ayrıştırma tarifleri.
