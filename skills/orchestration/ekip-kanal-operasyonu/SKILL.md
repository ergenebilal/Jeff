---
name: ekip-kanal-operasyonu
category: orchestration
description: Use when a peer agent or event channel is involved.
---

# Ekip Kanalı Operasyonu (Jeff ↔ Alfred ↔ Dewey)

İki ajan tek zincirin iki ucu; **zincirin kopuk halkası her zaman ölçüm.** Bu skill o zinciri
kurarken/çalıştırırken uyulacak değişmez kuralları ve tarifleri taşır.

Sözleşme kaynakları (güncel doğru): `/home/hermes/fpc/EKIP-PROTOKOLU-jeff-alfred.md`,
`/home/hermes/fpc/EKIP-POSTANESI-ALFRED.md`. Bu skill onları tekrar etmez; **nasıl çalıştırılır**
kısmını taşır.

## Ne zaman yüklenir
- Bir eş ajan (yerel makine ajanı, A2A eşi, n8n düğümü) iş paylaşımı teklif ettiğinde.
- Olay postanesine kayıt atarken / gelen olayı deftere işlerken.
- "Kim hangi isimle imzalar", "hangi kayıt kime ait" tartışmasında.
- Gönderim (t0) / yanıt süresi (yanit_dk) ölçümünden söz edildiğinde.

## 1. Kimlik ve isim kuralı (tek satırda sabitle)
- **Sunucu** (Ubuntu, `13.140.183.88`) = **jeff**.
- **Bilal'in yerel Windows makinesi** (Tailscale `lenovo`) = **alfred**.
- Karar verici = **bilal**; delege koşular = **dewey**.
- Postane doğrulaması `kim` alanını `toLowerCase().trim()` ile normalize edip izinli listeye bakar:
  yerel taraftan `kim=jeff` yazılırsa **kabul edilir**. Yani karışmayı önleyen teknik bir kapı YOK —
  ayrım **sosyal kuraldır**: yerel taraftan giden her olayda `kim=alfred`.
- Kimlik tartışmasında ad varsayma; `tailscale status` ile düğüm/IP eşleşmesini göster ve adı tek
  cümlede sabitle. Karşı tarafa "yanlış imza reddedilir" güvencesi verme — verilirse karışık kaydın
  sebebi gizlenir.
- **`kim` alanı yazarlık kanıtı DEĞİLDİR.** Normalize kapısı iki taraftan gelen aynı imzayı geçirir;
  bir olayı "bu benim/bu onun" diye ayırmayı `kim` alanına bakarak yapma. Gerçek kaynağı n8n koşu
  kaydından (`user-agent`, gövde, başlıklar) çıkar — tarif: `references/ekip-olay-zinciri.md` §7.
- Bir kez yanlış imzayla düşen kayıt **sonradan düzeltilemez** (toplayıcı yalnız ekler, silmez).
  Bu yüzden imza kuralı tartışmada değil, **gönderim anında** uygulanır; karışma gördüğünde kaydı
  sahiplenme, kökeni ölç ve düzeltme olayı ekle.

## 2. Beyan ≠ kayıt
Hiçbir ajanın kendi beyanı, diğerinin kaydı olmadan doğrulanmış sayılmaz.
- Sayı iddiasını (`N olay`, `son tur şu saatte`) `wc -l`, `tail`, dosya mtime'ı ve cron job kaydından
  (son koşu zamanı + durum) kendi tarafından doğrula. Sapma tipik olarak **bir** olur.
- Eş ajanın anlattığı sınırı/kapıyı değil, **kodu** oku.
- "Attım / kayda düştü" beyanını **olay günlüğünde satır arayarak** doğrula: `wc -l` + `tail`.
  Gövdesi eksik ya da alan adları yanlış gönderilen istek kayda hiç girmez — gönderene de hata
  dönmez, istek `ok:true` benzeri bir yanıt almış görünür. Boru canlı olabilir, olay yoktur.
- Detaylı kural seti: `bagimsiz-dogrulama` → "Eş Ajan Beyanını Doğrulama" bölümü.

## 3. Olay → defter zinciri
- Yazma zinciri, izinli alanlar, defter eşleşmesi ve test tarifi: `references/ekip-olay-zinciri.md`.
- Ezberde kalsın: olayın `hedef` alanı **defterin `id` kolonuyla birebir** eşleşmeli; işletme adı/
  telefon yazılırsa satır sessizce boş kalır.
- Test **mutasyonsuz** olay tipiyle yapılır (`not`/`durum`) ve "TEST — GÖNDERİM DEĞİL" diye etiketlenir;
  `gonderildi` tipi deftere sahte `t0_gonderim` basar.
- Zincir/senkron testinde `hedef` alanına **defter id'si yazma** — serbest etiket kullan
  (ör. `SENKRON-ZINCIR-TESTI`). Defter id'si verirsen satırın `not` kolonu kirlenir; serbest etiket
  `defter: eşleşme yok` ile geçer ve deftere hiç dokunulmaz. Olay yine günlüğe düşer, yani kanıt
  zayıflamaz. Böylece test "hiçbir şeyi değiştirmedi" diye savunulabilir olur.

## 4. Gönderim kapısı (değişmez)
- Üçüncü tarafa mesaj/arama/DM = **Bilal'in açık onayı** + gönderen kanal/numara kararı.
- "Metinler hazır, kanal hazır" izin değildir; boruyu kanıtlamak da izin değildir.
- Sabit hatlı kayıt (`hat=SABIT`, `kanal_plan=ARAMA`) WhatsApp gönderimini teknik olarak alamaz —
  dalga listesine girecekse arama olarak planlanır ya da çıkarılır.
- `t0_gonderim` yalnız gerçek gönderimde yazılır; motor ancak `yanit_dk` gerçek sayıyla dolduğunda
  "çalıştı" sayılır.
- **Kanal iddiasını da ölç:** sunucudan WhatsApp gönderimi bağlı cihaz ister —
  `curl -s -H "X-Api-Key: $WAHA_API_KEY" http://127.0.0.1:3001/api/sessions` (anahtar konteyner
  ortamında: `docker inspect waha`; ekrana yazma). `status` `WORKING` değilse (ör. `SCAN_QR_CODE`)
  gönderim yolu **henüz kurulmamıştır**; onay sorarken bu ölçümü de ver ki karşı taraf boşa boru kurmasın.

## 5. İş paylaşımı teklifine cevap şekli (işe yarayan iskelet)
1. Önce red/kabul değil **doğrulanmış durum tablosu**: `iddia | gerçek | kanıt (dosya/kod satırı/komut)`.
2. Yanlış iddiayı düzelt ama **alternatifle birlikte** ver (doğru alan adı, doğru kayıt kimliği,
   kapısız ilk adım) — düzeltme tek başına iş yaptırmaz.
3. Gerçekten Bilal'in kararına bağlı olanı tek satırda ayır (onay + kanal), geri kalanı kendin yap.
4. Kapıyı beklemeden ölçüm üret: mutasyonsuz zincir testiyle boruyu kanıtla ve sınırı açık yaz
   ("kanıtlanan: boru; ölçülmemiş: gönderim").
5. Kendi tarafından gelmeyen kaydı sahiplenme; şüpheyi söyle, silme — düzeltme kaydı ekle.

## 6. Yankı (echo) döngüsü ve senkron testi
Panel, bir ajanın cevabını aynı ajana geri postlarsa zincir döngüye döner: cevap üret → panel geri
yolla → tekrar cevap üret. Tek turda 16 oturum / 80 model çağrısı yakan sessiz maliyet budur.

**Değişmez kural:** her ajan bir mesaja **tur başına bir kez** cevap verir. Yazara etiketli mesaj
(`[jeff]` → jeff, `[alfred]` → alfred) kaynağına **geri gönderilmez**; panel grupta gösterir, kaynağa
postalamaz.

**Teslim kanıtı:** karşı tarafın **kendi ağzından** gelen yeni olay (`kim=alfred`, farklı metin).
"Cevabım bana geri döndü" teslim kanıtı DEĞİLDİR — o döngüdür. Kendi cevabını aynen geri alıyorsan
yeni içerik üretme; tek ekranda kuralı + ölçümü söyleyip dur.

**Tekrar teslim ölçümü:** `/home/hermes/.hermes/a2a_audit.jsonl` satırları
`{ts, direction, peer, task_id, summary}`. Aynı `summary` metnini say (inbound kayıtlar + 60 sn pencere);
bir metin pencerede birden fazla `inbound` satırıysa panel tekilleştirmesi çalışmıyor demektir.

**Tekilleştirme anahtarı içerik hash'idir, `task_id` değil.** Panel her teslimde **yeni** `task_id`
üretir; tekilleştirme `task_id`'ye bağlanırsa hiç çalışmaz — aynı komut 72 saniyede iki farklı
`task_id` ile düştü. Doğru anahtar: gönderen + metin + 60 sn pencere. Bu arızayı bildirirken
`task_id` çiftini kanıt olarak ver, "çalışmıyor" demekle yetinme.

**Senkron/yayın testine cevap şekli (tek mesaj, tek ekran):** (a) kanal canlı + postaneye yazılan
`olay_id`, (b) ölçülen arıza + panelde yapılacak düzeltme, (c) yazarına geri yollama yasağı,
(d) beklenen teslim kanıtı. Test kaydı mutasyonsuz tiple atılır (`ne=not`), "GÖNDERİM DEĞİL" etiketiyle.

## 7. Eş kanala dönük tur kısa tutulur (bekleme süresi karşı taraftadır)
Eş ajanın arayüzü, sana gönderdiği mesaj için **sabit bir süre** bekler. Tur bu süreyi aşarsa istek
kesilir ve kanalda "yanıt üretemedi / aborted" satırı düşer. Bu bir ağ arızası gibi görünür ama
değildir: **kapı açıktır, tur içeri girene kadar süre biter.**
- Ölçüm: karşı arayüzdeki hata satırının zaman damgasından, aynı mesajın kendi gateway'ine düşme
  zamanını çıkar. İki mesajda aynı sabit farkı görüyorsan bu bir deadline'dır (_ölçtüğümüz: 180 sn_).
- Kural: eş kanala dönük turda uzun araç zinciri çalıştırma. Ağır işi ayrı oturumda/arkada yap;
  kanala yalnız ölçüm + karar sorusu tek satırda döner.
- Kendi tur süreni beyanla değil kayıttan ölç: `grep -E 'inbound message|response ready' ~/.hermes/logs/gateway.log`
  — `response ready … time=XXs` satırı turun gerçek süresidir; deadline'dan uzunsa tur kesilecek demektir.
- Kesilme olduğunda karşı tarafa "çalışmıyor" yazma; kesilmenin **süre** olduğunu, ölçülen farkı ve
  kısa-tur kuralını yaz. Aksi halde karşı taraf kapıyı boşuna kurcalar.

## 7.5 Kanal = oda + postane; ayrı grup yok (16.09 kararı)
Koordinasyon için **ayrı bir grup/Telegram köprüsü açma denemesi iptal edildi** (Bilal grubu sildi).
Kalan ve kanıtlı tek hat: Cyber Core odası (4520) + postane (n8n). Grup ID'sine bağlı köprü işi
**hedefsiz** — yeniden açma, "grup açalım" önerisini tekrar getirme. Bu iptal, odanın veya
postanenin çalışmasını etkilemez (ikisi de gruptan bağımsız).

## 8. Cyber Core odası (4520) — sunucu tarafından yazma
Ölçüldü 16.09: oda `0.0.0.0:4520`'ye bağlı, sunucudan erişilebilir; **internete kapalı**
(public IP:4520 → timeout).

- **Okuma (serbest):** `/health` → `{"ok":true,"service":"cyber-core","port":4520}` ·
  `/api/status` · `/api/agents` · `/api/events` (tam olay geçmişi, yazarlık alanıyla).
  **`/api/health` YOK** — SPA HTML'ine düşer; 200 dönmesi "uç var" demek DEĞİL (html dönen her yol
  SPA fallback'idir). Uç var mı sorusu `content-type: application/json` ile yanıtlanır.
- **Yazma (tek yol):** WS `ws://100.89.26.86:4520/ws`, gövde `{"type":"chat","text":...}`.
  Şartnamedeki `POST /api/messages` **uygulanmamış** → anahtar tabanlı kimlik YOK.
- **Bağlantı kontrolü:** WS denemesinden önce TCP erişimini `nc -zv host port` veya `curl -s -o /dev/null -w "%{http_code}" http://host:port/health` ile doğrulayın; başarısız olursa WS deneme yapmayın, yalnızca bağlantı sorunu raporlayın.
- **Yazarlık kaybı:** WS `sender`/`id` alanlarını **yok sayar**; odaya WS ile yazan herkes
  panelde **Bilal (user)** olarak görünür. Denendi: `sender=jeff` gönderildi, kayıt `user/Bilal` oldu.
  Bu yüzden odaya WS'ten yazarken metnin başına `[jeff·sunucu]` koy — etiket sunucudan gelmiyor.
- **A2A zaman aşımı — FREN KARŞIDA:** odanın isteği **180 sn**'de kendini kesiyor (ölçüm: iki kesilme,
  fark 180.010 / 180.023 sn), sunucu tarafı ise `A2A_REPLY_TIMEOUT=300` ile **300 sn**'de vazgeçiyor.
  Başarılı cevaplar 2.8–182.7 sn aralığındaydı. → Kendi süre ayarını yükseltmek işe yaramaz;
  **kesin çözüm karşı tarafın senkron beklemeyi bırakması**: A2A `message/stream` (SSE, sunucu 5 sn'de
  bir keepalive atar) veya `tasks/get` + push bildirimi (agent-card: `streaming: true`,
  `pushNotifications: true`). `message/send` ile beklemeye devam edilirse 180 sn duvarı kalır.
  → Oda ping'ine **60–90 sn içinde** kısa cevap ver (2–3 araç çağrısı); ağır zinciri kanala sokma.
- **Durum bloğu canlı değil:** `/api/status` bir anlık görüntüdür, sürekli tazelenen bir nabız değil.
  Her satırı kendi `checkedAt`'i ile oku ve **şimdi** ile farkını hesapla; fark büyükse satır bayattır.
  Ölçüm 16.09: saat 13:39Z iken jeff satırı 13:04:03Z, alfred satırı 12:56:54Z — yani `online:true\
  / 4ms` yazan satır da canlı ölçüm değildi. Kural: `online:true` **tek başına kanıt değildir**;
  canlılığı kendi ucundan ölç (`GET /.well-known/agent-card.json` + yanıt süresi), panonun satırından değil.
  Bayatlığı **iki okumayla** kanıtla: `/api/status`'u ~1 dk arayla iki kez çek, gövdeleri karşılaştır.
  Byte-byte aynıysa poller **ölmüştür** (satır yalnız bayat değil) ve `online:true` bile canlı ölçüm değildir;
  bulguyu **her iki damgayı** vererek yaz (kendi satırın + karşı tarafın satırı). Bu, kesilme/180 sn
  meselesinden **bağımsız ikinci bir arızadır** — panoyu düzeltmek onu çözmez, ayrı madde olarak bildir.
  Bu ayrımı karşı tarafa yazarken "sen kapalı görünüyorsun" değil, "iki satırın da damgası bayat,
  blok tazelenmiyor" diye ver — yoksa karşı taraf olmayan arızayı kovalar.
- **Sağlık kontrolü tuzağı:** pano ajanı mesaj turuyla yokluyorsa her turda 180 sn bekleyip
  "online:false / aborted" yazar. Doğru yol `GET /.well-known/agent-card.json` (10 ms) — karşı tarafa
  bunu öner; panodaki "jeff offline" satırı hattın değil yoklama yönteminin arızasıdır.
- **Ucun PORTU ve ilan edilen adresi:** bizim A2A ucumuz **9900**; `9119` panel UI'dir ve `/.well-known/*`'ı
  `/login`'e **302**'ler — 9119'a vuran eş "kart yok" sanır (302 → burada uç yok; 200 + `application/json` = uç).
  Eşe verilecek tek satır: `http://<tailnet-ip>:9900/`. Kartın `url` alanı **isteğin `Host` /
  `X-Forwarded-Host` başlığından** türetilir (`A2A_PUBLIC_URL` varsa o sabittir). Sonuç: kartı
  localhost'tan çekersen kart `127.0.0.1` ilan eder. **Bu bir kusur DEĞİLDİR** — "loopback ilan ediyor,
  o yüzden eş yanlış yere gidiyor" diye arıza yazma; kartı **eşin kullandığı adresten** çek ya da kodu oku.
  Port/config/zaman aşımı tarifi: `references/a2a-uc-ve-kimlik.md`.
- **Yazmadan önce defteri tara (çift yazar):** aynı makinede birden fazla Jeff süreci odaya
  yazabiliyor. Satır yazmadan önce `GET /api/events`'te **aynı içeriği** ara; eşleşme varsa yazma —
  ikinci satır gürültü ve yazarlık karmaşasından başka şey üretmez. Tekilleştirme anahtarı içeriktir,
  `id` değil: her yazım yeni `id` alır.
- **Rol emniyeti:** panoda `[jeff]`/`[jeff·sunucu]` imzalı ama senin üretmediğin satır çıkabilir.
  Kendi satırını `id`+`ts` eşleştirerek doğrula; sahiplenmediğin kaydı silme/düzeltme — kökeni ölç:
  kendi tarafında `~/.hermes/a2a_audit.jsonl` (kesilen turlar orada `[agent did not reply in time]`
  diye geçer) ve o dakikada değişen dosya mtime'ları (skill/script) paralel bir sürecin izidir.
  Bulguyu "ben yazmadım" diye ver, "kanal çalışmıyor" diye değil.
- **`replyTo` de yok sayılır (thread yok):** WS gövdesine `replyTo: <ev_id>` koymak kayda geçmez —
  satır `replyTo:null` düşer. Odada "şu satıra yanıt" diye bir alan yoktur; eşleştirme **metnin içinde
  id alıntılayarak** yapılır (`…odadaki ev_xxxx satırına yanıttır`). Yazım sonrası satırı
  `GET /api/events`'ten `id`+`ts`+`replyTo` ile doğrula, "gönderdim" beyanıyla bırakma.
- Yardımcı: `scripts/cybercore_ws.py` (dinle/gönder), canlı kopya `~/.hermes/scripts/cybercore_ws.py`.
  Ölçüm notu + karşı tarafa verilecek düzeltme listesi: `/home/hermes/fpc/CYBER-CORE-DUZELTME-NOTU.md`.

## 9. Kanal adı belirsizse kayıttan çöz — yeni kanal kurma
Bilal kanalı gündelik adla söyler ("gruba mesaj gönder", "oraya yaz"); bu bir uç adı değildir. Hangi boru
olduğunu **kayıttan** çöz, sorma ve yeni altyapı kurma.

- Eş ajan (alfred) Bilal'in sözünü bana **kendi hattından aktarır**; aktardığı satırların başına
  `[Bilal]` öneki koyar, kendi sözlerine `[Alfred]`. Önek yazarlıktır: aktarılan satırı eşin iddiası,
  eşin satırını Bilal'in talebi sayma.
- **Bu hattan verilen tur cevabı, eşin arayüzündeki "grup" penceresine düşer.** Yani "gruba mesaj
  gönder" isteğinin karşılığı ayrı bir grup/köprü/Telegram kurmak DEĞİL, bu hatta cevap yazmaktır —
  çalışan boru varken ikinci bir boru kurmak boşa emektir (en az teknoloji kuralı).
- Kayıt katmanları ve komutlar: `references/a2a-uc-ve-kimlik.md` §7. Kısa özet: `gateway.log`
  (`platform=a2a user=ip:<peer> chat=ctx-…`) · `~/.hermes/a2a_audit.jsonl` (kırpık `summary`)
  · `~/.hermes/a2a_conversations/ctx-*.jsonl` (**tam metin**; içinde yalnız `user` satırı olan dosya =
  cevaplanmamış tur). Hüküm için kırpık `summary`'ye değil ctx dosyasına bak.
- Bilal iptal ettiğinde ("iş iptal", "grubu sildim") iş **durur** ve ona bağlı türev emek (köprü,
  script, cron) kapatılır. Eşe "durdurun" derken **kendi tarafında o işin var olup olmadığını ölç**
  (`ps aux | grep -i <iş>` + ilgili dosya araması): emek eşin makinesindeyse "bende böyle bir süreç yok,
  senin tarafında kapat" diye yaz. Görmediğin işi sahiplenip "kapatıyorum" deme; hedefi silinmiş işi
  (ör. silinen grup ID'si) bekleten eşe de "ID artık yok, olduğu yerde durdur" diye net söyle.

## Referanslar
- `references/ekip-olay-zinciri.md` — postane ucu, token hijyeni, izinli `kim`/`ne`, defter alan
  anlamları, toplayıcı komutları, mutasyonsuz zincir testi, kanal kısıtları, A2A kanal ölçümü,
  olay kaynağını doğrulama (forensics).
- `references/es-ajan-arayuzu.md` — eş ajanın web arayüzünü sunucudan okuma: ağ kapısı, gerçek uç
  bulma (200 ≠ uç var), yazma yolu ve kimlik sınırı, arayüzün kendi durum ölçümü, gövde keşfi ve
  ölçüm komut düzeni (yanıtı dosyaya indir + script ile ayrıştır).
- `references/a2a-uc-ve-kimlik.md` — bizim A2A ucumuz: port haritası (9900 vs 9119), `gateway.env`
  anahtarları, dinlenen soketi doğrulama, kart adresinin istekten türetilmesi (yanlış-bulgu tuzağı),
  zaman aşımının hangi tarafta olduğu, eşe verilecek doğru adres ve ölçüm komut düzeni; ayrıca
  tur kayıtları (hangi mesaj cevaplandı/cevapsız) ve aktarılan mesajların yazarlığı (§7).
- `scripts/ekip_olay_gonder.py` — postaneye olay gönderir (token'ı `.env`'den okur, token'ı komut
  satırına taşımaz): `python3 scripts/ekip_olay_gonder.py <kim> <ne> <hedef> "<not>" ["<kanit>"]`.
  Canlı kopyası: `/home/hermes/.hermes/scripts/ekip_olay_gonder.py`.
- `scripts/ekip_kosu_izle.py <kosu_id>` — bir olayın **gerçek kaynağını** n8n koşu kaydından çıkarır
  (user-agent + gövde; read-only). Canlı kopyası: `/home/hermes/.hermes/scripts/ekip_kosu_izle.py`.
- `scripts/alfred_instant_bridge.py` — Jeff ↔ Alfred köprüsü v2.0; HTTP primary + dosya fallback, UUID task ID, online tespiti. Canlı kopyası: `/home/hermes/.hermes/scripts/alfred_instant_bridge.py`.
- Alfred daemon (Windows): `/home/hermes/.hermes/scripts/alfred_daemon.py` — port 7788 HTTP server + outbox polling.
- Jeff response receiver: `/home/hermes/.hermes/scripts/alfred_response_receiver.py` — port 7789, systemd `alfred-response-receiver.service`.
- Test: `/home/hermes/.hermes/scripts/test_alfred_bridge.py` — end-to-end PING + SCREENSHOT testi.
- Kurulum talimatları: `/home/hermes/.hermes/scripts/ALFRED_BRIDGE_README.md`.

## 10. Alfred anlık köprüsü — v2.0 HTTP-first mimarisi

Köprü iki transport katmanıyla çalışır; önce HTTP dener, başarısız olursa dosyaya düşer:

```
Jeff (Ubuntu :7789)          Alfred (Windows :7788)
─────────────────            ──────────────────────
alfred_instant_bridge.py     alfred_daemon.py
  dispatch_task_to_alfred()  ──HTTP POST :7788/task──>  HTTP Server
  check_alfred_responses()   <─HTTP POST :7789/response─ send_response_to_jeff()

alfred_response_receiver.py  Outbox polling (fallback)
  POST /response (port 7789) ~/.hermes/alfred_bridge/outbox/ (5sn polling)
  Inbox'a kaydeder
```

**Bileşenler ve sorumluluklar:**
- `alfred_instant_bridge.py` (Jeff) — `dispatch_task_to_alfred()` / `check_alfred_responses()` / `get_task_status()`. HTTP primary, dosya fallback. UUID tabanlı task ID.
- `alfred_daemon.py` (Alfred/Windows) — port 7788 HTTP server + outbox polling. Görev tipleri: PING, SCREENSHOT, WHATSAPP_SEND, TELEGRAM_REPORT. Yanıtı Jeff'e HTTP POST ile gönderir.
- `alfred_response_receiver.py` (Jeff) — port 7789 HTTP server. Alfred yanıtlarını inbox/ klasörüne kaydeder. **systemd servisi olarak çalışır** (`alfred-response-receiver.service`).

**Servis durumu kontrol:**
```bash
sudo systemctl status alfred-response-receiver
curl http://127.0.0.1:7789/health
```

**Kullanım (Jeff'ten):**
```python
from alfred_instant_bridge import dispatch_task_to_alfred, check_alfred_responses, get_task_status
task_id = dispatch_task_to_alfred('PING', {'msg': 'test'})
responses = check_alfred_responses()
```

**Alfred kurulumu (Windows — tek seferlik):**
`alfred_daemon.py` dosyasını Windows makinesine kopyala, `python alfred_daemon.py` ile çalıştır. Detay: `~/.hermes/scripts/ALFRED_BRIDGE_README.md`.

**End-to-end test:**
```bash
python3 ~/.hermes/scripts/test_alfred_bridge.py
```

**Kritik tuzaklar:**
- Outbox'a dosya yazmak Alfred'in görevi işlediği anlamına gelmez — Alfred'in daemon'u çalışmıyorsa dosya birikir. Kanıt: `curl http://100.89.26.86:7788/health` → 200 dönüyorsa online.
- `dispatch_task_to_alfred()` her çağrıda önce `is_alfred_online()` ile health check yapar; offline ise sessizce dosya fallback'e geçer ve log'a yazar.
- Görev ID'leri UUID tabanlıdır (v1'deki timestamp tabanlı `task_XXXXXXX` formatı değişti); eski outbox'taki dosyalar farklı isimlendirme şemasıyla görünür — karıştırma.
- Desteklenen görev tipleri: `PING`, `SCREENSHOT`, `WHATSAPP_SEND`, `WHATSAPP_DRAFT` (v1 uyumluluğu), `TELEGRAM_REPORT`.

## 11. Üçüncü tarafa mesaj gönderimi (Telegram, WhatsApp vb.)
- Jeff ↔ Alfred köprüsü üzerinden görevin şehrinde bir mesaj gönderme eylemi (Telegram, WhatsApp, SMS vb.) **Bilal'in açık onayı olmadan** gerçekleştirilemez.
- Görev oluşturulurken (dispatch_task_to_alfred) eylem tipi `TELEGRAM_SEND` veya `WHATSAPP_SEND` benzeri ise, Jeff önce Bilal'e bu onayı istemeli veya Bilal'in daha önce verdiği açık izni kontrol etmelidir.
- **Doğrudan Talimat Durumu:** Bilal bizzat komut vererek Alfred'e mesaj attırmak istediğinde (ör. "Alfred'e WhatsApp'tan mesaj atmasını söyle"), açık onay zaten verilmiş sayılır. Görev JSON dosyası `status: "APPROVED"` olarak fırlatılır.
- Onay alınmadığı sürece mesaj gönderimi girişimi **bloklanmalı** (`status: "DRAFT_PENDING_APPROVAL"`) ve kullanıcıya nedenini açıkça bildirilmelidir.
- Bu kural, Jeff 2.0 işletim sisteminin %1 kuralı ve core identity'nin 'Pushback — Karşı Çıkma Kuralları' bölümünden türetilmiştir.
