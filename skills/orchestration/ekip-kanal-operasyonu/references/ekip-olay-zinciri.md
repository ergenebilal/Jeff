# Ekip Olay Zinciri — postane → toplayıcı → satış defteri

Amaç: bir temas olayını (`gönderildi` / `yanıt`) kayıt defterine **ölçülebilir** biçimde işlemek.
Boru: yerel ajan → n8n webhook (postane) → n8n koşu kaydı → toplayıcı (5 dk cron) → `fpc/cevap-log.csv`.

## 1. Kanal
- Uç: `http://100.124.217.48:5678/webhook/ekip-olay` (Tailscale içi; bu adres sunucunun kendi düğümüdür)
  · yedek: `https://n8n.aiergene.xyz/webhook/ekip-olay`
- Kimlik: `x-ekip-token` başlığı ya da gövdede `token`; değeri `EKIP_POSTANE_TOKEN` ortam değişkeninde
  (kabukta hazır gelir). Token'ı sohbete veya rapora yazma.
  **Token hijyeni:** varlığını `${VAR}` genişletmesiyle yazdırma — `echo "${TOKEN}"` ve
  `${VAR:+VAR}${VAR:-YOK}` kalıbı değeri transkripte düşürür ve token yanmış sayılır.
  Varlık kontrolü: `[ -n "$EKIP_POSTANE_TOKEN" ] && echo VAR || echo YOK`.
- Gövde: `{kim, ne, hedef, kanit, not}`; `zaman` verilmezse sunucu zamanı yazılır; yanıt olayın
  normalleştirilmiş halini + `olay_id` döner.
- Doğrulama düğümü `kim`/`ne` üzerinde `toLowerCase().trim()` uygular, **sonra** izinli listeye bakar:
  `kim` ∈ {alfred, jeff, dewey, bilal} · `ne` ∈ {gonderildi, yanit, tamam, hata, not, durum}
- **İsim kuralı:** sunucu = `jeff` · Bilal'in yerel Windows makinesi (Tailscale `lenovo`) = `alfred`.
  Yerel taraf `kim=jeff` yazarsa doğrulama kabul eder (normalize ediyor) → kayıt karışır; teknik kapı yok.
- **Alan adları katıdır:** gövdede `kim` + `ne` yoksa (ör. eş ajan `kaynak`/`tur` yazarsa) doğrulama
  `valid:false` döner, olay günlüğüne **hiç satır düşmez** ve gönderen tarafa anlamlı bir uyarı
  gitmez. "Postane canlı" doğru olabilir ama olay yoktur — iddiayı `wc -l` ile kontrol et.

## 2. Defter eşleşmesi — sessiz hata kaynağı
Toplayıcı, olayın `hedef` alanını defterin **`id` kolonuyla** birebir karşılaştırır (`V1`, `V6`, `V4`…).
İşletme adı, telefon ya da serbest metin yazılırsa satır güncellenmez ve **hiçbir hata çıkmaz**.
Yazılan alanlar:
- `ne=gonderildi` → `t0_gonderim` (yalnız boşsa) + `asama = 4-TEST_INTEREST (gonderildi)`
- `ne=yanit` → `cevap_verdi=evet`, `yanit_saati`, `yanit_dk = (yanit − t0)` dakika, `asama = ... (yanit geldi)`
- diğer tipler (`not`, `durum`) → `not` kolonuna `[kim:ne] metin` **eklenir** (doldurur, silmez, üzerine yazmaz)
- Yazımdan önce `cevap-log.csv` → `.cevap-log.yedek.csv` kopyası alınır.

## 3. Toplayıcı
- Cron job `ekip-postane-toplayici`: 5 dakikada bir, sessiz (yeni olay yoksa çıktı üretmez).
  Canlılık kanıtı = job kaydındaki son koşu zamanı + `ok` durumu.
- Elle çalıştırma güvenli ve idempotent:
  `python3 /home/hermes/.hermes/scripts/ekip_olay_al.py` → n8n
  `/api/v1/executions?workflowId=<ekip-postane-v1>` okur, `.ekip_son_kosu` işaretçisinden sonraki
  koşuları işler, işaretçiyi ilerletir; aynı koşuyu iki kez işlemez.
- Dosyalar: `fpc/ekip-olaylar.jsonl` (olay günlüğü) · `fpc/.ekip_son_kosu` (son işlenen koşu id) ·
  `fpc/.cevap-log.yedek.csv` (yazım öncesi kopya) · `fpc/.ekip_is_akisi_id` (workflow id).

## 4. Zincir testi (gönderim yapmadan)
**Tercih edilen yol — script:** URL ve token script'in içinde kalır, komut satırına sızmaz ve
onaysız/uzak yüzeylerde komut onay kapısına takılmaz. Canlı kopya `/home/hermes/.hermes/scripts/`.
```bash
cd /home/hermes/fpc && echo "ONCE: $(wc -l < ekip-olaylar.jsonl) olay"
python3 /home/hermes/.hermes/scripts/ekip_olay_gonder.py jeff not SENKRON-ZINCIR-TESTI \
  "zincir testi — GONDERIM DEGIL (16.09 00:38)" "sunucu saati + olay_id"
python3 /home/hermes/.hermes/scripts/ekip_olay_al.py      # elle tur; cron'u beklemeye gerek yok
echo "SONRA: $(wc -l < ekip-olaylar.jsonl) olay | isaretci: $(cat .ekip_son_kosu)"
tail -1 ekip-olaylar.jsonl
```
Yedek yol (script iki yolu sırayla dener): `https://n8n.aiergene.xyz/webhook/ekip-olay`.
Token kaynağı: `/home/hermes/.hermes/.env` içindeki `EKIP_POSTANE_TOKEN`.

**`hedef` seçimi:** zincir testinde serbest etiket (`SENKRON-ZINCIR-TESTI`) kullan — deftere hiç
dokunmaz, toplayıcı `defter: eşleşme yok` der. Defter id'si (`V1`) verirsen olay satırın `not`
kolonuna eklenir; defteri kirletmeden test etmek istiyorsan serbest etiket doğru seçimdir.
`ne=not` seçilir çünkü **mutasyonsuzdur**: `t0_gonderim`e dokunmaz. Testi `ne=gonderildi` ile yapmak
deftere sahte gönderim zamanı basar. Kanıt üçlüsü: webhook yanıtı (`ok:true` + `olay_id`), günlükteki
yeni satır (`kosu_id` dolu), toplayıcı turunun ilerlediği işaretçi (`.ekip_son_kosu`).

## 7. Olay kaynağını doğrulama — forensics (kim alanına güvenme)
`kim` alanı yazarlık kanıtı değil (bkz. §1). Gerçek kaynağı n8n koşu kaydı verir:
```bash
python3 /home/hermes/.hermes/scripts/ekip_kosu_izle.py <kosu_id>
# → /api/v1/executions/<id>?includeData=true ; webhook düğümünün headers + body'sini yazdırır
```
Okuma kuralları:
- **`user-agent` ayırt edicidir:** `PowerShell/7.x` + `Mozilla/5.0 (Windows NT …)` = Bilal'in yerel
  makinesi; `curl/7.81.0` (Ubuntu 22.04 varsayılanı) = Linux kabuğu, yani ya sunucu ya yerel
  makinedeki bir Linux ortamı; `python-urllib` = script'li çağrı. Tek başına isim kanıtı değil,
  gövde metniyle birlikte oku.
- `host` başlığı çoğu zaman `100.124.217.48:5678` (sunucunun kendi Tailscale IP'si) gelir — her iki
  taraf da aynı adrese bağlandığı için **ayırt edici değildir**, kanıt sayma.
- Gövdedeki serbest metin kimin yazdığını gösterir: yerel tarafın kendi jargonu/gövde şekli
  (ör. `{kaynak, tur}`) ile sunucunun şeması (`{kim, ne, hedef}`) ayrışır.
- Aynı dakikada iki koşu varsa ikisini de oku: biri kayda girmiş, diğeri geçersiz düşmüş olabilir.
- Koşu listesi (`/api/v1/executions`) toplayıcının okuduğu kaynaktır; oradaki `kosu_id` sırası ile
  `ekip-olaylar.jsonl` satırlarındaki `kosu_id` birebir eşleşmeli. Eşleşmiyorsa araya başka bir
  yazıcı girmiş demektir.

## 5. Kanal kısıtları
- Sabit hatlı kayıt (`hat=SABIT`, `kanal_plan=ARAMA`) WhatsApp gönderimini teknik olarak alamaz;
  dalga listesine girecekse arama olarak planlanır ya da listeden çıkarılır.
- Gönderim sırası: metin sunucuda hazırlanır → yerel taraf gönderime hazırlar → **Bilal onaylar ve
  kanalı seçer** → yerel taraf zaman damgası + kanıtla bildirir → olay postaneye düşer → toplayıcı
  deftere işler → yanıt geldiğinde `yanit_dk` gerçek sayıyla ölçülür.
- Başarı tanımı: "mesaj gitti" değil, zincirin son halkasının **ölçülmesi** (`t0` + `yanit_dk`).

## 6. A2A kanal ölçümü (postaneden bağımsız)
A2A giriş/çıkışının kaydı: `/home/hermes/.hermes/a2a_audit.jsonl` — her satır
`{ts, direction, peer, task_id, summary}` (`direction` ∈ {inbound, outbound}).

```bash
python3 - <<'EOF'
import json, datetime
rows=[json.loads(l) for l in open('/home/hermes/.hermes/a2a_audit.jsonl',encoding='utf-8',errors='ignore') if l.strip().startswith('{')]
for r in rows:
    print(datetime.datetime.fromtimestamp(float(r['ts'])).strftime('%m-%d %H:%M:%S'), '|', r['direction'], '|', r['task_id'], '|', str(r['summary'])[:70])
EOF
```
- Aynı `summary` **birden fazla satırsa** panel tekilleştirmesi yok demektir; her teslimde yeni
  `task_id` üretildiği için `task_id` üzerinden tekilleştirme işe yaramaz (içerik hash'i gerekir).
- Gateway tarafı teyit: `grep "inbound message" ~/.hermes/logs/*.log | tail` — oturum kimliği
  (`chat=ctx-…`) her teslimde değişir, yani yeni oturum + yeni model çağrısı açıldığının kanıtıdır.
- Bu dosya **sadece A2A** tarafını görür; postane olayları `fpc/ekip-olaylar.jsonl`'de. İki sayı
  karşılaştırılırken karıştırılmaz.

**Kendi tur süren (gecikme ölçümü):**
```bash
grep -E 'inbound message|response ready' ~/.hermes/logs/gateway.log | tail -12
# inbound 16:00:46 → response ready time=73.9s  ⇒ tur sonuna kadar geçen gerçek süre
```
- Tur süresi `time=XXs` alanındadır (araç çağrısı sayısı `api_calls` ile birlikte okunur; uzun tur =
yüksek `api_calls`).
- **Eş tarafın bekleme süresini ölçmek:** eş arayüzdeki "yanıt üretemedi" satırının zaman damgasından,
ait olduğu mesajın kendi `inbound message` zamanını çıkar. Birden fazla mesajda aynı fark çıkıyorsa
bu sabit bir deadline'dır (ölçülen: **180 sn**), ağ arızası değil.
- Aynı `chat=ctx-…` için `response ready` satırı **hiç yoksa** tur hâlâ çalışıyor demektir; "cevap
dönmedi" diye rapor etmeden önce bu satırı ara.

**Kendi kuyruğunu temizle:** kesilen turda üretilen cevap yine de eş arayüze gidebilir (`Sending
response (N chars)` satırı abort'tan sonra da düşer). Kesilme sonrası "hiç gitmedi" varsayma; satırı
oku, gitti/gitmedi ayrımını kayıttan yap.
