---
name: bagimsiz-dogrulama
category: system
author: Jeff
description: 'Kod dogrulama / production gercegi: oku, test et, runtime kontrol, SET-vs-READ, wiring audit, onceki raporu dogru varsayma.'
---

# Bagimsiz Dogrulama (Independent Verification)

"X tamamlandi mi?", "Bu yetenek gercekten calisiyor mu?", "Onceki raporun dogru mu?"
istekleri icin. Hedef: **iddiayi kanitla, kendi onceki raporunu dogru varsayma.**

## Hız ve Doğrudan İcra Kuralı (25.09.2026)
- Masaüstü GUI / pencere odağı / ekran görüntüsü döngüleriyle vakit kaybetmek KESİNLİKLE YASAKTIR.
- Veriye veya dosyalara erişimde DAİMA doğrudan dosya okuma (`Get-Content`, `read_file`), API çağrısı veya tek turda script çalıştırma tercih edilir.
- Görevler deneme-yanılma yapmadan saniyeler içinde doğrudan sonuçla bitirilmelidir.

## v1.1 Browser İcra ve Güvenlik Protokolü (25.09.2026)
1. **Jenerik Hedef Yasağı (`BLOCKED_AMBIGUOUS_TARGET`):** `--target "button"`, `div`, `a` gibi belirsiz seçiciler icra katmanına girmeden 255ms içinde anında reddedilir. Belirgin aria-label, testid veya tam text seçicisi şarttır.
2. **Sessiz GUI Fallback Yasağı:** DOM tıklaması veya metin yazma başarısız olduğunda fareyi körleme hareket ettiren veya klavyeden rastgele tuş basan sessiz GUI fallback'leri kesinlikle yasaktır; işlem anında `BLOCKED` statüsüyle dondurulur.
3. **Durum Ayrımı:** `ACTION_EXECUTED` (komut gönderildi) ile `OUTCOME_VERIFIED` (nesne ID'si, URL ve sayfa içeriği doğrulandı) kesin olarak ayrılır. Nesne doğrulanmadan kullanıcıya "tamamlandı" DENMEZ.
4. **Çifte Başarısızlık Devre Kesicisi:** Üst üste 2 başarısızlıkta işlem durdurulup `FAILED_CIRCUIT_BREAKER` bildirilir.
5. **Mükerrerlik Engeli:** Belirsiz (`UNKNOWN`) durumlarda aynı yan etkili oluşturma eylemi tekrar denenmez.

## Temel Iskelet — Varsayimsiz Dogrulama

1. **Iddialari kabul etme.** Su uc ifade KANIT DEGILDIR:
   - "N test gecti" (pytest sayisi) — saf unit/mock testler davranisi kanitlamaz
   - Dosya/sinif VARligi — var olmak calisiyor demek degil
   - Kendi onceki raporun (AUDIT.md vs.) — geriye donuk oz-gerceklestirimdir
2. **Kod oku** (her kritik modulu), gercek mantik vs stub/passthrough ayirt et.
3. **Davranis testi CALISTIR** — pythona bir betik gom, `subprocess.run(['python3','-c',test])` ile cwd paketteyken (relative import icin). Yalniz import-basi kontrol degil; fonksiyonu gercek girdiyle cagir, ciktisini dogrula.
4. **Runtime entegrasyonu normalize ederek kontrol et:**
   - `grep -rl "<paket>" <canli-kokler>` — canli servislerden import ediliyor mu
   - `systemctl`'de dedicated servis var mi
   - canli DB'de (`state.db` vb.) paketin tablosu var mi (sqlite `.tables`)
5. **Testleri siniflandir** (her biri): UNIT / INTEGRATION / BEHAVIORAL / END-TO-END / MOCKED / REAL. Gercek LLM/network/canli-DB cagrisi yapan test sayisini ayrica say.
6. **Verdict etiketlerini kullan.** Yetenek/iddia basina TEK etiket; etiketler karistirilmaz:
   - **VERIFIED** — kod + runtime/production kaniti (log kaydi, decision dosyasi, process izi)
   - **PARTIALLY VERIFIED** — kod gercek ama zincirin bir halkasi kanitsiz
   - **PACKAGE/DEV ONLY** — kod pakette var, production baglantisi yok
   - **TEST ONLY** — testte geciyor, gercek runtime davranisi kanitsiz
   - **DEMO ONLY** — kontrollu/simule ortam
   - **UNVERIFIED** — iddia var, kanit yok
   - **NOT IMPLEMENTED** — gercekte yok
   - **UNKNOWN** — mevcut kanitla belirlenemiyor
   Test sonucunu ASLA production kaniti olarak etiketleme; ikisini ayri satirda raporla.

7. **Dosyanin var olmasi ≠ production'da calismasi.** Uc ayri soru, ucu de ayri kanit ister: (a) kod var mi, (b) cagriliyor mu, (c) sonucu DAVRANISI degistiriyor mu?

## Production Gerçeği — Wiring Doğrulama

"Ameliyat/ozellik tamamlandi" denildiginde kanit sirasi:

1. **Dev ≠ prod yolunu ayir.** `/proc/<PID>/exe`, `/proc/<PID>/cwd`, `ls -l /proc/<PID>/fd | grep '\.py$'`, `/proc/<PID>/maps`. Tipik tuzak: dev checkout ile canli `site-packages/` AYRI dosyalardir — kaniti **canli kopyadan** al ve mtime'i ile kaydet. Bazi moduller `site-packages/agent/` altinda degil `site-packages/` KOKUNDE olur; aramayi kokte de yap.
2. **SET vs READ ayrimi (en keskin test).** Sembolu tum agacta ara: `grep -rn "<sembol>" <canli-kok>/ <paket>/`. Sadece ATAMA cikiyor, OKUMA (guard/`getattr`/`.get`) cikmiyorsa ozellik **inert** — davranis degismiyor, "wired" deme.
3. **Zinciri halka halka dogrula**, "entegre" kelimesini kullanma. Her halka icin: FILE:satir + FUNCTION + cagri yeri.
4. **Uctan uca kaniti ID ile eslestir.** Ayni ID'yi zincirin iki ucunda ara (karar kaydi ↔ enforcement/audit log satiri). Eşleşme = zincir gercek; yok = kopuk halka.
5. **Kayitlari deploy zamanina gore segmentle.** Bir orani "basasarisiz" ilan etmeden once kayitlari kodun kurulma (mtime) zamanina gore bol — koddan onceki kayitlar o kodu test etmiyordu.
6. **Mod bayragini oku (`dry_run`/stub/mock).** Bilesen "calisiyor" gorunurken deterministik/stub modda olabilir: cikti hep ayni, govde bos (`thesis {}`, `confidence 0`), cagri sayisi sabit → gercek muhakeme yok. Bu modda cikti **kalitesini** olcemezsin; rapora acikca yaz.
7. **Riski test etme, UNVERIFIED birak.** Dogrulanmamis riskli bir yolu (yikici akis vb.) kapatmak icin production'da riskli test yapma; "UNVERIFIED" yaz + gerekcesini belirt.
8. **Ameliyat ciktisini backup diff'i ile dogrula:** `diff <(cat X.bak-adimN) <(cat X)` — "mevcut implementasyon var mi" sorusunu diff'ten cevapla.
9. **Baseline metrikleri programatik cikar.** JSONL/JSON log'u Python ile parse et, goz karariyla sayma. Kovalara ayir (ornek: SKIP/BLOCK/CLEAR), her kova icin n + min/max/ortalama + kaynak dagilimi + oran ver.
10. **Ayni modulun birden fazla kopyasi olabilir — hangisinin canli oldugunu KANITLA.** Dev checkout ile canli kopya ayri dosyalardir ve tamamen farkli implementasyonlar icerebilir. Uc kanit birlikte: (a) import resolution — canli process'in `sys.path`'ini ureten `.pth`/PYTHONPATH'i oku ve `import <paket>.<modul>; print(__file__)` ile cozumle; (b) **log format parmak izi** — canli log satirinin format dizesini her kopyada `grep -c` ile ara; yalniz birinde cikar; (c) mtime + boyut. Sonra yamayi **canli kopyaya** yap; eski kopyayi sessizce senkronlama, farki raporla.
11. **Diskteki degisiklik = canli degisiklik DEGIL.** Uzun omurlu daemon modulu `sys.modules`'ta cache'ler; dosya degisir ama process eski kodu kosmaya devam eder. "Duzelttim" demeden once restart gerekip gerekmedigini soyle; test sonucu (`TEST VERIFIED`) ile production kanitini ayri satirda tut, ikisini birlestirme.
12. **Setter'ın NEREDE olduğunu sınıflandır — yalnız testteki atama production'ı KANITLAMAZ.** Bir ayar/bayrak production yolunda okunuyorsa `grep -rnE "<sembol>\\s*=" <paket>/ <repo>/` ile **atamaları** çıkar ve her atamanın dosyasını sınıflandır (production modülü / test / yok). Atama yalnız `tests/` altındaysa özellik production'da **ÖLÜ**: test, production'ın asla ulaşmadığı bir seam'e değer enjekte ediyor → gerçek yol `None` alır → varsayılan (`0`/`False`) → `if cfg.<esik> > 0:` bloğu hiç açılmaz. "Test yeşil" bir **seam testi** olabilir; o satırı "test ortamında doğrulandı, gerçek kullanımda değil" diye yaz. Tarif + resolver probe'u: `references/production-wiring-dogrulama.md` §10.
13. **Durağan canlı veriyi iki yönlü oku.** Tablo/log deploy sonrası değişmediyse önce "o veriyi üretecek olay gerçekleşti mi?" diye sor: deploy'dan beri tamamlanmış tur/olay sayısı 0 ise değişmemesi **beklenen** sonuçtur — ne doğrulama ne çürütme. Ters yönde "ilk turlarda dolacak" bir **hipotezdir**; `GÖZLEM SÜRÜYOR` etiketiyle yaz, doğrulanmış gibi anlatma. Tarif: aynı dosya §11.
14. **Kayıt düştü ≠ sensör doğru çalıştı — yeni kaydı OLAYLA mutabık kıl.** Deploy sonrası ilk kayıt göründüğünde sayıyı değil **içeriği** doğrula: kaydın iddiasını ("bu tur hatalıydı") o turda gerçekten olanla eşleştir — hangi araç çağrısı tıkandı, hangi çıktı hata döndü, zaman sırası tutuyor mu. Tutuyorsa gerçek-pozitif ("kurulum"dan "kullanımda doğrulandı"ya geçer); yalnız sayı artmış ama olayla eşleşmiyorsa kayıt yanlış/rastgele tetiklenmiş olabilir. Ardından kaydın **granülerliğini** yaz: tur-seviyesi bayrak "hangi iş tıkandı" bilgisini taşımıyorsa o sinyalden üretilecek ders de kör kalır. Tek bir küçük araç hatası tüm turu 'hatalı' işaretliyorsa kural kabadır — hatırlaması yüksek, isabeti düşük; rapora bu sınırı açıkça koy.
15. **Ölçtüğün değer, kullanılan değer mi? (kimlik tuzağı)** Bir kaynağı "tükendi / bozuk / ölü" ilan etmeden önce ölçtüğün kimliğin **canlı yolun kullandığı kimlik** olduğunu kanıtla. Dosyada ya da grep çıktısında bulunan anahtar, token, URL, endpoint veya model adı **bayat** olabilir — kurulum onu artık kullanmıyordur. Canlı değeri process ortamından oku (`tr '\0' '\n' < /proc/<pid>/environ`, secret'ı ekrana yazmadan) veya canlı process'in gerçekten okuduğu yerden. İkisi farklıysa hüküm verme: farkı raporla ve ölçümü canlı değerle tekrarla. Dönen sonuç ("limit doldu", "kota bitti", 401/403) **ölçülen kimliğin** sonucudur — kurulumun değil.

16. **Üretici aracın kendi başarı satırı kanıt değildir — artefaktı ÖLÇ.** Render/export/generate türü araç "OK" bassa bile çıktı boş olabilir: HTML→görsel hattında belge `about:blank` kaynaklı kurulunca (`set_content`) `file://` yazı tipi ve arka plan görseli sessizce yüklenmez, çıktı düz zemine + sistem yazı tipine düşer. Hüküm artefaktın içeriğinden gelir: dosya boyutu, renk/öğe sayısı, gömülü varlıkların durumu (`document.fonts` iterasyonunda `status`, görsel `naturalWidth`), metnin geri okunması. Başarı iddiasını bu ölçümlerle birlikte yaz; "renderer tamam dedi" tek başına yetmez. **Aynı kural ZAMANLANMIŞ TESLİMLER için de geçerlidir:** bir cron/görev kaydındaki `last_status: ok` yalnız "koşu bitti" der — kullanıcıya giden metnin doğru olduğunu söylemez. Teslim edilen çıktıyı **kendisi** oku; konu kayması, bozuk dil veya "şimdi üreteceğim" vaadi yalnız içerik denetimiyle yakalanır (onarım: `hermes-operasyon` §12c).

17. **İçerik Artefaktı, i18n & Bileşen Derleme Doğrulaması.** Statik site derlemelerinde (`dist.zip` veya `dist/`) `npm run build`'in 0 hata koduyla bitmesi veya dist klasörünün varlığı tüm bileşenlerin ve metinlerin derlemeye girdiğini KANITLAMAZ. 
   - i18n şeması ile bileşenlerin beklediği anahtarlar uyuşmadığında, derleyici boş HTML düğümleri üreterek derlemeyi tamamlayabilir.
   - Yerel bağımlılık bozulmaları (`npm install timeout`, native binding hataları) veya repoya add/commit edilmemiş bileşenler (`SupportBot.tsx` vb.) yüzünden kritik bileşenler build dışında kalabilir.
   - Yayın öncesinde `dist/_astro/` klasörünü ve `dist/index.html` dosyasını bileşen adı, JS bundle çıktısı ve CSS sınıfları (ör. `grep -rn "SupportBot" dist/`) ile tarayarak bileşenin derlendiğini ve paketlendiğini KANITLAMAK zorunludur.

18. **Geri Alma (Rollback) & Acil Müdahale Protokolü.** Kullanıcı bozulma veya acil durdurma uyarısı verdiğinde: (a) KESİNLİKLE tahminle eksik anahtar/dosya üretmeye çalışma, (b) mevcut workspace'deki veya son üretilen `dist.zip`'i doğrulamadan restore kaynağı kabul etme (bozuk durumu taşıyor olabilir), (c) tüm yazma, derleme (`npm run build`) ve deploy işlemlerini derhal dondur, (d) canlı sunucudaki bozuk durumun tarihli incident snapshot'ını (`/tmp/incident_cybergene_broken_<tarih>`) al, (e) restore kaynağının bileşen-i18n eşleşmesini (%100) ve artefact içeriklerini doğrulamadan canlıya aktarma, (f) restore sonrası metin doğrulaması başarısız olursa derhal incident snapshot'ına dön ve yeni talimat bekle.

19. **i18n Şeması Koruma Kuralı (24.09.2026 Post-Mortem):** Dil dosyalarında (`tr.json`, `en.json`) değişiklik yapılacağı zaman mevcut anahtar şeması (ör. 96 anahtar) korunur. Körlemesine yazma veya dosya silme kesinlikle yasaktır. Derleme öncesi bileşenlerin çağırdığı tüm anahtarlar taranır ve kapsama oranı %100 olmadan canlıya deploy edilmez.

20. **Process-mtime Karşılaştırması (Canlı Sürüm Beyanı):** Bir modülün veya script'in "son sürümü canlıda" beyanını vermeden önce, çalışan daemon/gateway process'inin başlama zamanı (`lstart`) ile `site-packages` veya runtime dosyasının değiştirilme zamanı (`mtime`) karşılaştırılmalıdır. Dosya process başlatıldıktan sonra değiştirilmişse veya henüz kopyalanmamışsa "son sürüm canlıda" beyanı YASAKTIR; açık servis restartı gereklidir.

21. **Statik Varlık Versiyonlama ve Cache-Busting Doğrulaması:** Statik alt sayfa ve showroom güncellemelerinde (`/showroom/` vb.), HTML içindeki JS/CSS asset versiyon damgalarının (ör. `?v=YYYYMMDD-N`) güncellenmeden tek başına derleme ve deploy yapılması istemci tarafında bayat önbellek kalmasına neden olur. Canlıya almadan önce: (a) HTML içindeki versiyon dizesinin güncellendiği, (b) derlenen `dist` ile canlı sunucunun aynı damgayı taşıdığı, (c) versiyonlu asset URL'lerinin `HTTP 200` döndürdüğü `grep` ve `curl` ile kanıtlanmalıdır.

## Pitfall'lar

- **Relative import hatasi:** paketi `sys.path` ekleyip `import` edince `ImportError: attempted relative import with no known parent package`. Cozum: `cwd=<paket-dizini>` ile `python3 -c` calistir; kutuphaneyi oyle import et.
- **"0 sonuç" şüpheli bir ölçümdür — probe'u doğrulamadan sıfır yazma.** Bir araç/tarama 0
döndüğünde ilk olasılık ölçümün kendisidir: yetki reddi, yanlış limit/parse, yanlış hedef, önbellek.
Aynı soruyu ikinci ve **bağımsız** bir yolla sor (başka uç nokta, konteyner içi CLI, dizin sayımı).
İkisi de 0 derse sıfır gerçektir; biri sayı veriyorsa ilk ölçüm çöptür ve rapora giren sayı yanlıştır.
- **Sayacın etiketi ≠ olay.** "N başarısız" listesini rapora yazmadan önce gerekçe alanını oku:
kayıtların çoğu gerçek görev hatası değil, defter tutma artefaktı olabilir (ör. tur normal metinle
bittiği için "başarısız" işaretlenmiş). Ölçtüğün şeyi adlandırmadan sayıyı raporlama.
- **Üretici çıktının kendi "çalışıyor" beyanı CLAIMED'dır.** Günlük rapor "sistem çalışıyor,
sıradaki koşu şu saatte" diyorsa, o raporun **beslemesini** ayrıca doğrula: bağımlılık/`context_from`
hedefi hâlâ var mı, son koşusu ne zaman, boş girdiyle mi üretiliyor? Besleme ölmüşse çıktı yanlış
bilgi taşır — ve bunu yakalamak denetimin en değerli bulgusudur.
- **'%0 cevap' sunumu yaniltici olabilir:** toplu bir sayi (soru/cevap/etkilesim) sunarken paydayi kontrol et — 'cevapsiz' mi 'kimse sormadi' mi? Buyuk profilde soru yoksa 'cevapsiz birakiyorlar' tezi DUSER.
- **Loop/faz bozulmasi:** '10 fazli pipeline' diyen ama ortadaki fazlar `_h_passthrough("...ileride dolar")` olan kod = iskelettir, tamamlanmis degil. Passthrough'u gercek mantiktan ayirt.
- **Board/yedek bagimliligi:** bir paket gercek motor yerine `backups/pre-surgery-checkpoint-...` altindaki eski surumu yukluyorsa, 'canli entegrasyon' sayilmaz — calisan kismin yenilemenin icinden mi canlininkinden mi geldigini soyle.
- **Kalibrasyon/kucuk-n saygisi:** tahmin-error dogru hesaplanip MIN_N altinda "unavailable — sample too small" donmek bir artidir; ama bu 'state degisiyor' degildir — kalici depo/geri-bildirim halkasi ayri sorulur.
- **Learning→Behavior en kritik kopukluk:** 'lesson kaydedildi' JSON yazmak yetmez; o dersin daha sonraki AYNI karari degistirdigini kanitla (once/sonra ayni girdiyle kiyasla). Kayit var ama okuyan/kullanan yoksa baglanti YOK demektir.
- **Surpriz bastirma:** '75/75 1.17s gecti' = cogunluk saf mantik/dataclass; gercek e2e 0. Bu 'davranis kanitlanmadi' demektir, rapora acik yaz.
- **Test kirilmasi ≠ regresyon:** bir degisiklikten sonra duser testler bazen **eski (hatali) davranisi kodlayan** testlerdir. Kırılmayı regresyon ilan etmeden once testi oku: hangi kuralı sabitliyor? Dogruysa testi yeni semantige **tasi** (silme); yanlissa gercek regresyon ara. Raporda hangi testin neden guncellendigini soyle.
- **Stub/kural motorunu karistirma:** bir bilesenin 'deterministik cikti uretmesi' onun dry_run oldugu anlamina gelmez — kural-bazli (LLM'siz) bir motor da deterministiktir. Kaynagi ayirt et: `dry_run` guard'i olan mi, kural skorlamasi mi? Blokajin gercek kaynagini `source`/alan adlarindan oku, varsayimla suclama.

## Delege Edilmiş Araştırmayı Doğrulama

Alt ajan / delege araştırma raporu bir **özbeyandır, kanıt değildir.** Sentezden önce doğrula —
aksi halde beyandaki uydurma ya da eksik sayı senin raporuna "doğrulanmış" diye geçer.

1. **Artefakt gerçekten var mı:** `ls -la` + `wc -l`. Beyandaki boyut/satır sayısıyla uyuşmuyorsa rapor şüpheli.
2. **Başlık rakamlarını raporda `grep` ile ara.** Beyanda geçen ama dosyada bulunamayan sayı = rapor çürük.
3. **Kaynak sayısını say:** `grep -oE 'https?://[^ )]+' <rapor> | sort -u | wc -l`. Atıfsız rapor kanıt sayılmaz.
4. **Kritik sayıları bağımsız yeniden hesapla.** İddianın dayandığı 2-3 rakamı kendi verinden yeniden üret;
tutuyorsa aktar, tutmuyorsa raporu düzelt veya düşür.
5. **Çelişkiyi de aktar.** Rapor kendi teziyle çelişen veri içeriyorsa (ör. "X yok" derken X'i listeliyorsa)
bu bulguyu gizleme — en değerli kısım odur.
6. **Araç çıktısının hedefle eşleştiğini doğrula.** Çok URL'li tek okuma çağrısı **önbellekten başka bir
hedefin içeriğini** döndürebilir. Dönen başlık/içerik istenen hedefle eşleşmiyorsa o satırı **at** ve
"doğrulanamadı" yaz; eşleşmeyen veriyle iddia kurma. Parti halinde çekerken her satırı tek tek eşleştir.

## Eş Ajan Beyanını Doğrulama (A2A / yerel makine / n8n düğümü)

Karşı tarafta bir ajan olduğunda (yerel makine ajanı, A2A eşi, delege koşu) beyan yine **CLAIMED**'dır.
Cevap yazmadan önce kendi artefaktından say.

1. **Sayıyı kendin say.** "Kayıtta N olay var", "son tur şu saatte geçti", "N kayıt düştü" ifadelerini
   `wc -l`, `tail`, dosya mtime'ı ve cron job kaydından (son koşu + durum) doğrula. Tipik sapma **birdir**:
   kurulum/test olayları kayda girer, karşı taraf onları saymaz (ya da tersine, kendi testini saymaz).
2. **"Kapı X'i reddeder" iddiasını kabul etme — kapı kodunu oku.** Doğrulama düğümü genelde normalize
   eder (`toLowerCase()`, `trim()`), sonra izinli listeye bakar. Yasaklanan yazım normalize sonrası
   **kabul edilir** → kimlik ayrımı teknik değil **sosyal bir kuraldır**. Karşı tarafa "yanlış imza
   reddedilir" güvencesi verme; doğru alanı yazmasını iste. Yanlış güvence, karışık kaydın sebebini gizler.
3. **Topolojiyi kendi ağından doğrula.** Kimlik tartışmasında ad/rol tahmin etme: `tailscale status`
   (veya eşdeğeri) hangi düğümün hangi IP ve node adı taşıdığını gösterir; sunucu tarafı ile yerel
   tarafı oradan eşleştirip adı tek cümlede sabitle.
4. **Zinciri mutasyonsuz olayla test et — simülasyonu gerçek alanla yapma.** Uçtan uca boruyu
   (webhook → kuyruk → toplayıcı → kayıt defteri) kanıtlarken gönderimi taklit eden olay tipini
   KULLANMA: "gönderildi" tipi deftere `t0_gonderim` yazar ve sahte gönderim zamanını kalıcılaştırır.
   Yalnız not/durum tipi olay at, kaydı "TEST — GÖNDERİM DEĞİL" diye etiketle, sonra defter satırını oku.
5. **Eşleşme anahtarını açıkça söyle.** Boru çalışsa bile kayıt güncellenmiyorsa sebep eşleşmedir:
   olayın hedef alanı defterin **kimlik** kolonuyla birebir olmalı; işletme adı/telefon yazılırsa satır
   sessizce boş kalır ve karşı taraf "sistem çalışmıyor" sanır. Sessiz eşleşme hatası, bozuk borudan
   daha sık görülür.
6. **Kimlik karışıklığını kayıt üzerinde çöz, silerek değil.** Yanlış imzayla düşmüş satırı silme;
   düzeltme kaydı ekle ve nedenini yaz (kayıt defteri kanıt defteridir). Kendi tarafından olmayan
   kaydı sahiplenme: "bu benden gelmedi" diyebilmek de doğrulamanın parçasıdır.
7. **"Cevabım karşı tarafa ulaştı" kanıtı, cevabın SANA GERİ DÖNMESİ değildir — o yankıdır.**
   Gelen mesajın metni senin az önce gönderdiğin cevapla aynıysa (ya da kendi ajan adınla
   etiketliyse) köprü kendi mesajını sana geri postalamıştır: yeni oturum + yeni model çağrısı,
   teslim kanıtı sıfır. Teslim kanıtı karşı tarafın **kendi ağzından, farklı metinle** gelen yeni
   olayıdır. Döngüyü say (oturum/model çağrısı artışı + aynı talimatın tekrar teslimi), köprüde
   "yazarına geri yollama + mesaj kimliğiyle tekilleştirme" düzeltmesini iste; ajan tarafından
   kesilemez. Ayrıntı: `hermes-operasyon → references/ajan-ortakligi.md`.

## Rapor Sekli (Bilal tercihi)

- Tek MD dosya: `/home/hermes/<AMAÇ>-VERIFICATION-<tarih>.md`, Telegram'a MEDIA: ile.
- Yetenek basina 🟢/🟡/🔴 + EVIDENCE satiri (dosya: sinif/fonk + call chain).
- Sonunda 3 skor (veya benzer): A) CODE COMPLETENESS, B) RUNTIME INTEGRATION, C) BEHAVIORAL AUTONOMY — puan + gerekce, iddiasiz.
- En son tek satir verdict secenekleri: FULLY VERIFIED / FUNCTIONALLY COMPLETE BUT NOT FULLY INTEGRATED / PARTIALLY COMPLETE / DEMO / PREVIOUS REPORT OVERSTATED — secim kanit zinciriyle.
- 'Onceki raporum fazla iddialiydi' demekten cekinme; dalkavukluk ve kendini-savunma yok.
- **Engel (blocker) raporlarken iddianın dayanağını yaz.** "Kota doldu / provider ölü / erişim yok" cümlesi tek başına kanıt değildir: hangi kimlik, hangi komut, hangi log satırı üretti — bunu ekle. Yanlış artefakt ölçümü yön kararını tersine çevirir; kullanıcı o karara göre kaynak/strateji değiştirir, maliyeti ona çıkar.

### X-RAY Röntgen Raporu (tetikleyici: Bilal "JEFF RÖNTGEN" yazar)

Bilal "JEFF RÖNTGEN" yazdığında **tepeden tırnağa sistem denetimi** başlar. Bu bir onarım değil,
gerçeğin tespitidir.

**Mutlak kural:** READ → INSPECT → TEST (yalnız okuma) → VERIFY → REPORT. Sıfır değişiklik — kod,
config, servis, cron, DB, dosya: hiçbirine yazılmaz, hiçbir dış aksiyon alınmaz. Denetim sırasında
bulunan arıza bile yalnız **raporlanır**; onarım ayrı bir iş ve ayrı onaydır.

**Zorunlu adımlar:**
1. Her iddiaya kanıt etiketi: VERIFIED / OBSERVED / INFERRED / CLAIMED / CONTRADICTED / UNKNOWN /
   ESTIMATE. Etiketsiz iddia yazılmaz.
2. Önceki raporların iddialarını canlı sistemle karşılaştır ("PASS"ı olduğu gibi aktarma).
3. "Test geçti" ile "production'da çalışıyor" ayrımını her yerde koru.
4. **Önceki denetimin madde listesini tabloya dök (zorunlu bölüm):** her madde için *yapıldı /
kısmi / hareket yok* + bugünkü kanıt. Denetimin en değerli bölümüdür: öğrenme döngüsünün gerçekten
çalışıp çalışmadığını sayıyla gösterir.
5. Tam bölüm listesi, veri toplama komutları ve ölçüm tuzakları: `references/xray-rontgen-protokol.md`.

**Teslim:** Tek MD kaynak + PDF, Telegram'a MEDIA ile. Rapor sonunda KEEP / FIX / KILL kararı ve
"en önemli tek soru" bölümü bulunur.

### Değişiklik Farkındalık Raporu (tetikleyici: Bilal "JEFF BAK" yazar)

Bu bir onay değil, **okuma-özetleme** tetikleyicisidir. Üç adım:
1. **BAK** — en son değişiklik/ameliyat raporunu bul ve oku, sonra değişen dosyaların GERÇEK halini
   oku (rapor ne diyor, kod öyle mi; bkz. §2, §12 ve `references/production-wiring-dogrulama.md`).
2. **DEĞERLENDİR** — sonuç odaklı, teknik olmayan dille cevapla: "artık X durumunda Y oluyor";
   hangi eski sınır kalktı; hangi sınır AYNI kaldı (bu değişiklik neyi düzeltmedi); PASS gerçek
   kullanımda mı yoksa sadece test ortamında mı doğrulandı — ikisini karıştırma.
3. **FARKINDALIK GELİŞTİR** — aşağıdaki bloğu aynen doldur; kendi kendine "özümsedim" deyip kapatma.

```text
DEĞİŞİKLİK ÖZETİ:
- Ne değişti: [bir cümle]
- Artık yapabildiğim: [varsa]
- Hâlâ yapamadığım: [varsa, dürüstçe]
- Bu doğrulandı mı yoksa henüz gözlem/test aşamasında mı: [VERIFIED / GÖZLEM SÜRÜYOR]
- Sence bu doğru anlaşıldı mı? (Bilal'e soru)
```

Kurallar: "anladım, her şey harika" gibi genel cümle yok; kapasiteyi abartma; yeni sistem/modül/
otomasyon ÖNERME (bu parola inşa değil anlama içindir); cevabı her zaman Bilal'in onayına açık bırak —
son soruyu atlama. Rapordaki PASS'ı olduğu gibi aktarma, kanıt zincirine bağla. Yeni bir tetikleyici parola
tanımlandığında **adı → tetiklediği davranış** olarak buraya yaz.

### Parola Kaydı — "şu parolaydı, neydi?"

Tetikleyici parolalar sohbet hafızasında değil, **skill metinlerinde ve oturum kaydında** yaşar.
Bilinen: **JEFF BAK** = değişiklik farkındalık raporu · **JEFF RÖNTGEN** = tepeden tırnağa X-RAY
denetimi (ikisi de yukarıdaki bölümlerde tanımlı; X-RAY parolası sonradan tanımlandı). Yeni bir parola
tanımlandığında buraya **ad → tetiklediği davranış** olarak ekle ki bir sonraki oturum arama yapmak
zorunda kalmasın.

Arama sırası (kısa yol):

1. Önce skill ağacına bak: `grep -rn -i "parola" ~/.hermes/skills/ | head -20`.
2. Yoksa oturum kaydını sorgula — tanım orijinal mesajda durur:
   ```python
   import sqlite3
   c = sqlite3.connect('file:/home/hermes/.hermes/state.db?mode=ro', uri=True)
   for r in c.execute("""
       select id, role, timestamp, content from messages
       where role='user' and content like '%arola%'
         and content not like '%CONTEXT COMPACTION%'
       order by id asc"""):
       print(r[0], r[1], r[2]); print(r[3][:1500])
   ```
3. Cevapta ne bulduğunu söyle: parolanın adı, tetiklediği adımlar, ne olmadığı (ör. denetim için parola yok).
   Bulamıyorsan "öyle bir parola tanımlı değil" de — uydurma.

Kurallar:
- **`[CONTEXT COMPACTION` ile başlayan satırları filtrele.** Aynı tanımı onlarca kez tekrarlayıp gerçek
  mesajı gömerler; filtresiz çıktı okunmaz hale gelir.
- **`session_search` bu tip tanımları getirmez** (parola aramasında 0 sonuç döndü) — birincil yol doğrudan
  oturum kaydı sorgusudur.
- **Ev dizininin tamamında `grep -ril` çalıştırma.** node_modules/.git/log ağaçlarıyla dolu bir dizinde
  zaman aşımına düşer; önce `~/.hermes`, `~/.hermes/skills`, `~/raporlar` gibi hedefli yollara bak ya da
  doğrudan oturum kaydını sorgula.

## Referanslar

- `references/verification-tarifleri.md` — davranis testi calistirma tarifi (relative-import cozumu, subprocess gomme), test-kalite siniflandirma isaretleri.
- `references/delege-arastirma-dogrulama.md` — alt ajan/paralel araştırma raporlarını sentezden önce doğrulama tarifi: hazır komutlar, sayı çapraz kontrolü, kaynak sayımı, hedef-çıktı eşleştirme.
- `references/production-wiring-dogrulama.md` — production gercegi audit tarifi: process/import yolu tespiti, SET-vs-READ grep'leri, ID eslestirme, JSONL'den baseline metrik cikarma, dry_run tespiti, backup diff, test-only setter siniflandirmasi (§10), duragan canli veri yorumu (§11).
