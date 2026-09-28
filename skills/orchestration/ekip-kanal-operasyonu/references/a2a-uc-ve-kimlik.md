# A2A Ucumuz (sunucu = jeff) — port, kimlik, zaman aşımı

Eş ajan "sana ulaşamıyorum / offline görünüyorsun" dediğinde ve "seni hangi adresten çağırayım"
sorusunda bu dosya kullanılır. Karşı tarafın arayüzünü okuma tarifi ayrı: `es-ajan-arayuzu.md`.

## 1. Port haritası — hangi uç ne işe yarar

| Port | Ne | Kart yolu |
|---|---|---|
| **9900** | **A2A ucu** (agent-card + JSON-RPC) — eşin çağıracağı yer | `GET /.well-known/agent-card.json` → **200**, ~12 ms |
| `9119` | Panel UI (`hermes serve`) | `/.well-known/*` → **302** `/login?next=...` → **uç DEĞİL** |

- **302 = burada uç yok.** `/login`'e düşen bir yoklama "kart kayıp" sonucu üretir; eş sonra "hat kopuk"
  diye rapor eder. Doğru cevap: "vurduğun port panel, A2A 9900'de".
- Aday portları sırayla yokla, gövdeyi değil durum kodunu oku:
  `for p in 9900 9119 8644 8642 8890; do curl -s -m 5 -o /dev/null -w "p=$p http=%{http_code} t=%{time_total}\n" http://127.0.0.1:$p/.well-known/agent-card.json; done`
- Aynı ölçümü **tailnet adresinden** de yap (eşin gördüğü yol odur): `http://<tailnet-ip>:9900/...`.

## 2. Yapılandırma nerede ve neyi kanıtlar

- `~/.hermes/gateway.env` (0600): `A2A_HOST`, `A2A_PORT`, `A2A_AGENT_NAME`, `A2A_BEARER_TOKEN`.
  A2A plugini gateway süreci içinde koşar; ayar oradan okunur.
- Canlı değeri process ortamından doğrula (secret'ı ekrana yazmadan):
  `tr '\0' '\n' < /proc/<gateway-pid>/environ | grep -E '^A2A' | sed -E 's/(TOKEN|SECRET|KEY)=.*/\1=<gizli>/'`
- **"0.0.0.0 istedim" kanıt değil:** token yokken kod `A2A_HOST`'u yok sayıp **127.0.0.1'e düşer**
  (uyarı loglar). Dinlenen soketi ayrıca doğrula: `ss -tlnp | grep <port>`.
- **Token varsa eş kimliği anahtardan çözülür** (ör. `ip:<tailnet-ip>`); token yoksa kimlik yalnız
  sokak adresidir ve eş adı taşınmaz → yazarlık iddiası kanıtlanamaz. Eşin "adım şu" demesi yetmez,
  anahtarın kimliği üretmesi gerekir.

## 3. Kartın ilan ettiği adres İSTEKTEN türetilir — kusur sanma

Kod: `plugins/platforms/a2a/adapter.py` → `_request_public_url()` = `A2A_PUBLIC_URL` >
`X-Forwarded-Host`/`Host` (şema `X-Forwarded-Proto`'dan) > boş; boşsa `http://<bind-host>:<port>/`.

- Sonuç: kartı **localhost'tan** çağırırsan kart `http://127.0.0.1:9900/` ilan eder; eş kendi adresinden
  çağırırsa kendi adresini yazar. Yani `127.0.0.1` görmek **arıza işareti değildir**.
- **Yanlış-bulgu tuzağı:** "kart loopback ilan ediyor, eş bu yüzden yanlış yere gidiyor" iddiasını
  yazma. Hüküm için: kodu oku (yukarıdaki tek satır) ya da kartı **eşin kullandığı adresten** çek.
- Adresi kanıtlamak için `-H "Host: ..."` ile taklit yapma — gereksiz ve onay kapısına takılır;
  mekanizma yukarıdaki kod satırından okunur. Kodu okuyup çürütmek, ölçüm komutunu zorlamaktan ucuzdur.

## 4. Zaman aşımı — fren hangi tarafta

- Kendi tavanımız: `_reply_timeout()` → `A2A_REPLY_TIMEOUT` (varsayılan **300**). Bu ortamda
  `gateway.env`'de tanımsız → 300 geçerli; kendi audit'imizde `[agent did not reply in time]` tam bu
  tavanda düşer.
- Eşin tavanı ayrı (ölçülen **180 sn**). **Kendi tavanını yükseltmek eşin duvarını kaldırmaz** →
  ayar şişirme; doğru düzeltme eşin senkron beklemeyi bırakmasıdır (`message/stream` veya `tasks/get`
  + push; kartta `streaming: true`, `pushNotifications: true`).
- Tur disiplini: eş ping'ine **60–90 sn** içinde kısa cevap; ağır işi kanala sokma.

## 5. Eşe verilecek doğru tek satır

> A2A ucum `http://<tailnet-ip>:9900/`; sağlık yoklaması `GET /.well-known/agent-card.json` (200, ~12 ms).
> `9119` panel UI'dir, oradan kart görünmez.

## 6. Ölçüm düzeni

Çıktıyı dosyaya indir, sonra ayrıştır (paralel koşuda satırlar karışmasın):

```bash
curl -s -m 8 -o /tmp/ac.json -w "http=%{http_code} t=%{time_total}s\n" http://<host>:9900/.well-known/agent-card.json
python3 -c "import json;d=json.load(open('/tmp/ac.json'));print('url:',d['url']);print([i['url'] for i in d['supportedInterfaces']]);print(d['capabilities'])"
```

Süre (`t=`) eşe verilecek sayıdır; `url` alanı tek başına kanıt değildir (§3).

## 7. Tur kayıtları — hangi mesaj cevaplandı, hangisi aktarıldı

Bilal kanalı gündelik adla söylediğinde ("gruba mesaj gönder", "oraya yaz") hangi borudan söz ettiğini
buradan çözülür; ayrı grup/köprü kurmak gerekmez — bu hattan verilen tur cevabı eşin arayüzündeki
grup penceresine düşer.

```bash
tail -5 ~/.hermes/a2a_audit.jsonl                      # ts, direction, peer, task_id, summary
ls -t ~/.hermes/a2a_conversations/ | head -5           # ctx-*.jsonl → tam metin (user/agent satırları)
grep "inbound message" ~/.hermes/logs/gateway.log | tail -20   # platform=a2a ... chat=ctx-…
```

- `a2a_audit.jsonl` satırları: `{ts, direction: inbound|outbound, peer, task_id, summary}`.
  **`summary` kırpıktır** — hüküm için ilgili `a2a_conversations/ctx-<id>.jsonl` dosyasını oku.
  Dosyada tek başına `user` satırı varsa o tur **cevaplanmamıştır**; `direction=inbound` olup eşleşen
  `outbound` satırı olmayan `task_id` de aynı işareti verir.
- **Önek yazarlıktır:** `[Bilal] …` = Bilal'in sözü (eş aktardı), `[Alfred] …` = eşin kendi sözü.
  Aktarılan satırı eşin iddiası sayma; eşin kendi teşhisi ayrı satırdır.
- `ts` alanı unix saniyedir; yorum için yerel saate çevir (`datetime.fromtimestamp`) — "kim önce yazdı"
  sorusu bu sırayla yanıtlanır.
- Bilal iptal ettiğinde (`[Bilal] … iptal …`) o iş durur; eşe kapatma talimatı yazarken işin kendi
  tarafında olup olmadığını `ps aux | grep -i <iş>` + dosya aramasıyla ölç, görmediğin emeği sahiplenme.
