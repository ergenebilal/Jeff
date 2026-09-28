---
name: saha-satis-lead-uretimi
description: Use when a field-sales target list must be built.
---

# Saha Satışı İçin Lead Üretimi

> Bir ürün/platform/hizmet için **kapı kapı gidilecek hedef listesi** isteniyorsa (partner işleri dâhil).
> Kapsam kuralı: partner işinde istenen **sadece lead + pazarlama stratejisidir** — bizim ürün/hizmetimiz plana karıştırılmaz.

## Akış

### 1. Izgara taraması
Google Places API (New) `places:searchText`; alan maskesi: `id, displayName, formattedAddress, nationalPhoneNumber, websiteUri, rating, userRatingCount, types`.
Sorgu kalıbı `"<segment> <ilçe> <şehir>"` (örn. `diş hekimi Nilüfer Bursa`), `maxResultCount=20`, `languageCode=tr`, `regionCode=TR`.
- **Tekilleştirme place id ile** — aynı işletme birden çok segment sorgusunda çıkar.
- Ölçek: 20 segment × 3 ilçe ≈ 675 ham kayıt; 10 mekân tipi ≈ 192 mekân. Çağrılar arasına ~0.25 sn.
- Segment seçimi hedefin işine göre (dekor/duvar sanatı → kafe, restoran, butik otel, coworking, showroom, spor salonu, klinik).
- **Boş sonuç ≠ sonuç yok:** uzun tek turda (60+ sorgu) API `429` döndürür. Hatayı yutup `[]` sayarsan "o segmentte kimse yok" sanırsın. Hata mesajını yazdır, kotayı bekleyip eksik sorguları ikinci turda tamamla, raporda **hangi grupların eksik kaldığını** açıkça belirt.

### 2. Bireysel / kurum ayrımı
- Ünvan ön eki (`Uzm./Op./Prof./Doç./Dt./Dr./Dyt./Psk.`) veya ad-soyad → **bireysel**, kapıda karar verici var.
- `hastanesi / tıp fakültesi / T.C. / bakanlığı / eğitim ve araştırma / belediye / vakıf / dernek` ve zincir markalar → **ayıkla** (karar mercii yerinde yok).
- Sayıyı raporda göster: "675 ham → 148 kapı hedefi".

### 3. Zenginleştirme — her satırda üç kolon
1. **Platform kaydı:** `https://<platform>/?s=<işletme adı>` aramasında profil linki (`/doktor/...`, `/urun/...`) var mı?
   → **kaydı var = sıcak lead** ("profiliniz hazır, sahiplenin") · **yok = soğuk** ("adınız hiç çıkmıyor").
2. **Kendi dijital zemini:** site var mı/açılıyor mu, SSL geçerli mi, mobil uyumlu mu, telefon tıklanabilir mi (`href="tel:`), WhatsApp var mı, ölçüm var mı (`gtag|googletagmanager|analytics.js`), sitede Instagram linki var mı.
   **Instagram handle'ı site kodundan ayıklarken gürültü gelir:** varlık yolları (`rsrc.php` gibi), dosya uzantılı değerler (`.js/.css/.ico/.jpg`), iki harfli dil kodları (`tr/en`), rezerve yollar (`p|reel|reels|explore|accounts|tv|stories|embed`) ve CDN parçaları (`static.cdninstagram.com`). Eleme ölçütü **uzantı/rezerve/iki-harf/CDN-parçası** olmalı — nokta varlığı değil: gerçek hesaplar `ergene.ai` gibi nokta taşır, noktayı eleme sayma. Hiçbir handle doğrulanmadan yazılı mesaja girmez; "hesabınızı inceledim" cümlesi yanlış handle'la giderse güven anında biter.
   Google'daki "web sitesi" bir **rakip platform sayfası** olabilir (örn. profil doktortakvimi.com'a işaret eder) — bu en güçlü satış kozlarından biri, ayrı etiketlenir.
3. **Hacim sinyali:** yorum sayısı + puan (yorum = müşteri trafiği = ödeyebilme gücü). Kıyas için aynı nişteki rakiplerin yorum sayıları da çekilir ("sizde 4 yorum, aynı işi yapan X'te 101").

### 4. Öncelik puanı ve çıktılar
Puan = yorum hacmi (kademeli) + sitesi yok/erişilemedi + Instagram yok + telefon var + platformda kaydı yok + puan ≥4.5 + sektör bonusu.
- Her satırda **"neden uygun"** kolonu olur: sanat/dekor o mekânda nereye gider (lobi, fotoğraf köşesi, bekleme alanı, showroom). Bu kolon yoksa liste sahada okunmaz.
- **Zincir/kurumsal işletmeler işaretlenir ve geriye alınır:** uluslararası zincirler merkezî satın alma kullanır, karar verici kapıda yoktur. Listenin üstü bağımsız işletmeler olur.
- **CSV** (Türkçe başlık, telefon + adres) — telefonda açılır, sahada kullanılır.
- **Kapı dosyası** (hedef başına): doğrulanmış tespitler + o hedefe özel açılış cümlesi + işaretleme kutuları (`girildi · görüşüldü · ilgilendi · kabul · ödedi`).
- **Yürünebilir rota:** bölge kümeleri, günde 10-12 kapı, 3 güne dağıtılmış.
- Geniş listeler **yatay PDF** (skill: `rapor-pdf-teslimi`).

### 5. Kanal ortağı (specifier) katmanı — listeyle BİRLİKTE üretilir

Son müşteri listesi tek başına **eksik teslimdir**. Aynı turda satın almayı *belirleyen* ofisler de taranır: iç mimarlık, mimarlık, dekorasyon, mobilya showroom, etkinlik dekor, **çerçeve atölyesi/galeri**. Bir ofisle kurulan ilişki o ofisin bütün projelerine girer — kapı kapı gezmekten üstün katmandır.

- Kanal listesi **ayrı CSV + yatay PDF** olarak teslim edilir; her satırda ticari çerçeve görünür (komisyon mu, bayi fiyatı mı).
- Bu katmanı kullanıcı sorana kadar bekletme — sorduğunda liste yarım kalmış demektir.
- **Aynı turda her ortak için AYRI yazılı teklif metni üretilir — üç parça:** kısa ilk mesaj (WhatsApp/DM, ~3 paragraf) · e-posta gövdesi + konu satırı (detaylı sürüm) · 3 gün sonra tek takip. Tek şablonu N kez kopyalamak teslim değildir: her metin firmanın kendi adından/ilçesinden türeyen **doğrulanmış** veriyle kişiselleşir, ortak tipine göre farklı çerçeve kurar.
- **Doğrulanmamış gözlem cümlesi yasak:** "Instagram'da hesabınızdaki işleri inceledik", "sitenizdeki projeleri inceledik" gibi cümleler kurulmaz — incelenmeyen içerik hakkında iddia alıcının ilk sorusunda çöker. Kişiselleştirme firmanın kendi işinden gelir: adındaki uzmanlık (mutfak-banyo, tadilat, çerçeve-tablo, mobilya, mimarlık), ilçe, faaliyet tipi; yorum sayısı yalnızca tek başına sayı olarak. Veri yoksa cümle atlanır, uydurulmaz.
- Metinler **studio/çoğul dille** yazılır ("biz üretiyoruz, uğrarız, uygun olur mu?") — tekil girişim dili ("ben üretiyorum, gelirim") yasak. **Ticari şartlar (komisyon, bayi fiyatı, fiyat bandı) ilk mesaja konmaz**; ilk mesaj üç paragrafı geçmez, pazarlık e-posta/görüşmede yapılır.
- **Teslim öncesi kapı (altı kalem):** uydurma gözlem · tekil dil · kanal biçimi işaretleri · tekrar eden cümle · imzadaki çalışmayan link · başlıkta ham Places adı.
- Metin "portfolyo ve şartname kartı yanımda" der — bu iki materyal yoksa metin havada kalır; aynı teslimde **eksik olarak işaretlenir**.
- Detay (ticari çerçeve, şartname kartı, yaklaşım metni, ölçüm): `references/mekan-ve-kisi-hedefleri.md`

### 6. Uzak temas icra paketi — mesajı hazırlamak işi BİTİRMEZ

Liste hazır, metin yazılı olduğu hâlde gönderim yapılmıyorsa darboğaz insani adımdır (altı oturum üst üste "gönderim 0" böyle çıktı). O adımı 5 saniyeye indiren paket üretilir; üretim tarifi: `references/ilk-temas-icra.md`.

- **Kanalı veri seçer, tercih değil.** Listede `hat` alanı `mobil` → WhatsApp · `SABIT` → **arama** (sabit hatta WhatsApp denemek o teması sessizce öldürür; ayrı arama metni yazılır).
- **Tek dokunuş linki:** numarayı uluslararası biçime çevir (`0…` → `90…`), onaylı metni URL-encode edip `https://wa.me/<no>?text=<metin>` linkine göm. Tıklayan tek tuşla gönderir.
- **Metin birebir gider** — kısaltma, emoji, "iyileştirme", fiyat/süre/garanti ekleme yok. Metin değişirse hangi cümlenin işe yaradığı ölçülemez.
- **Her hedef için kayıt satırı şablonu** pakete konur (tarih alanı boş). Şablonsuz devir, ölçümsüz icra üretir.
- **Başarı tanımı kayıttır:** gönderim saati + dönen yanıtın işlenmesi. "Liste hazır" veya "mesaj gitti" başarı değildir.

## Saha doğrulama kuralları (kapıya yanlış bulguyla gitmek yasak)
- **URL ile durumu ayrı alanlarda tut:** `site_url` + `site_durum`. Durumu `site` alanına yazmak adresi ezer; sonraki doğrulama `unknown url type` ile patlar.
- **Tek başarısız çekim "site bozuk" demek değildir:** sunucu tarafı çekim engellenir/zaman aşımına uğrar, tekrar denemede açılabilir. Etiket: *"erişilemedi — kapı öncesi tekrar bak"*, **aynı gün tazelenir**.
- **İlçe ayrıştırma tuzağı:** adreslerde birleşen nokta bulunur (`Ni̇lüfer` = i + U+0307). Eşleştirmeden önce `\u0307` temizlenir, yoksa ilçe boş döner ve rota kurulamaz.
- **Liste yaşı** raporda yazılır; 2 haftadan eskiyse yeniden taranır.
- **İlk temas kapıdır, WhatsApp değil.** WhatsApp: bir gün önce randevu + ziyaret sonrası takip. Kişisel numaradan günde 7+ soğuk mesaj spam işaretine yol açar.

## Referans
- `references/mekan-ve-kisi-hedefleri.md` — dikey detayları: mekân hotspot skorlaması, B2B görüşme malzemesi, kanal ortakları + **kişiye özel yazılı teklif metni üretimi**, hekim/ilan platformu vakası.
- `references/ilk-temas-icra.md` — uzaktan ilk temasın icra paketi: kanal tipini veriden belirleme, tek dokunuş gönderim linki üretme, kayıt satırı şablonu, icra pitfall'ları.
