# Olay Kanall — ajanlar arası tek hat (n8n ile kurulum)

**Ne zaman:** iki veya daha fazla ajan (sunucu + kullanıcının yerel makinesi + devredilen işçiler) arasında iş bildirimi taşınacaksa. Dosya taşıma/kullanıcı üzerinden aktarma 3 ajandan sonra tıkanır.

Canlı örnek kurulum: `ekip-postane-v1` iş akışı — webhook `POST /webhook/ekip-olay`, uç noktası `http://<sunucu-tailscale-ip>:5678/webhook/ekip-olay`.

## 1. Sözleşme (önce bu, sonra teknoloji)

Olay gövdesi: `{kim, ne, hedef, kanit, not}`

| Alan | Zorunlu | Değerler |
|---|---|---|
| `kim` | ✅ | `alfred` · `jeff` · `dewey` · `bilal` (whitelist — tanınmayan ad reddedilir) |
| `ne` | ✅ | `gonderildi` · `yanit` · `tamam` · `hata` · `not` · `durum` |
| `hedef` | — | kayıt defterindeki hedef no (ör. `V1`) veya serbest etiket |
| `kanit` | — | dosya adı / ekran görüntüsü adı / mesaj kimliği |
| `not` | — | kısa açıklama |

- Başlıkta token (`x-ekip-token`); token'sız veya yanlış token'lı istek **kayda girmez**, `401 {ok:false, sebep:...}` döner.
- Gönderen taraf yalnız `ok:true` gördüğünde "bildirdim" sayar.
- `gonderildi` → defterde gönderim saati; `yanit` → cevap saati + **kaç dakikada döndüğü**. Ölçüm bu iki alandan doğar.

## 2. n8n'i API'den kurma (arayüz şifresi gerekmez)

```bash
K=$(python3 -c "import json;print(json.load(open('/home/hermes/.config/n8n-api.json'))['api_key'])")
curl -s -H "X-N8N-API-KEY: $K" "https://n8n.aiergene.xyz/api/v1/workflows?limit=100" -o /tmp/wf.json -w "%{http_code}\n"
```

**Önce doğrula, sonra "API kapalı" hükmü verme.** 401 gelirse başka anahtar dosyası ara (`~/.hermes/n8n_api.env` eskimiş olabilir); çalışan anahtar `/home/hermes/.config/n8n-api.json` içindedir. Yol/metot tahmin etme — canlı şema: `https://n8n.aiergene.xyz/api/v1/openapi.yml`.

| İş | Uç nokta |
|---|---|
| Oluştur | `POST /api/v1/workflows` (`name`, `nodes`, `connections`, `settings`) |
| Güncelle | **yok** — `PATCH`/`PUT` 405. Değişiklik = **sil + yeniden oluştur** |
| Yayınla | `POST /api/v1/workflows/{id}/publish` (`/activate` 2.34'te 405) |
| Kimlik oluştur | `POST /api/v1/credentials` `{name,type,data:{...}}` → dönen `id` düğümde kullanılır |
| Koşu kaydı | `GET /api/v1/executions?workflowId=..&includeData=true` ← hata ayıklamanın tek güvenilir kaynağı |

## 3. Düğüm tuzakları

1. **Code düğümü hatası sessizdir:** fazladan bir parantez → koşu `error`, uçtan `ok` dönmez. Hatayı koşu kaydından oku (`resultData.error.message` + `lastNodeExecuted`), tahminle düzeltme yapma.
2. **Zincir sonrası veri kaybı:** bir düğümden sonra (ör. Telegram) `$json` **o düğümün** çıktısıdır. Önceki düğümün verisini döndürmek için `{{ $('Düğüm Adı').item.json.alan }}`.
3. **`responseMode: responseNode` her dalda yanıt düğümü ister** — eksikse çağıran boş gövdeyle 200 alır (sessiz arıza).
4. **Webhook başlığı** okunacaksa `headerParameters.parameters` altında tanımlanmalı; sonra `$json.headers['x-...']`. Gövde: `$json.body`.
5. **Token karşılaştırmasını Code düğümünde yap** (IF sürüm farklarına takılmaz), sonucu `valid:true/false` çıkar, IF ile dallandır; red dalında `options.responseCode: 401`.
6. **Konteynerde `$env` yok** — ortam değişkeni bekleyen düğüm kurulumu bozar. Paylaşılan sır `~/.hermes/.env` (600) + Code düğümüne gömülür; mümkünse `POST /credentials` ile kimlik oluşturulur.
7. **Konteyner host dosyasına yazamaz** (host ağı, uid 1000:1000, docker hacmi kullanıcıya kapalı) — kalıcı kayıt için düğümden dosya yazmaya çalışma; aşağıdaki toplayıcı desenini kullan.

## 4. Teslim kanıtı — düğüm "ok" demesi yetmez

```python
resultData['runData']['<Bildirim Düğümü>'][0]['data']['main'][0][0]['json']['result']['message_id']
```

Gerçek mesaj numarası + sohbet adı gelmiyorsa gönderim olmamıştır. **Aynı disiplin: var olan iş akışına güvenme, koşusuna bak** — var olmayan kimliğe bağlı düğüm iş akışını bozmaz, yalnız tetiklendiğinde patlar (canlı bir örnek bulundu: adı olan ama hiç koşmamış bir köprü).

## 5. Sunucu tarafı toplayıcı deseni (n8n → kalıcı kayıt)

- Script `~/.hermes/scripts/<ad>.py`: `GET /executions?includeData=true` → yeni koşuları süz → olayı `jsonl` dosyasına ekle → "son işlenen koşu no" işaret dosyasını güncelle (yeniden işlemeyi önler).
- İş akışı no'yu ve işaret dosyasını **kalıcı** yere yaz — `/tmp` yeniden başlatmada kaybolur.
- Cron: `no_agent=True` + `script=<dosya adı>` (göreli olacak, `~/.hermes/scripts/` kökü). **Yeni olay yoksa stdout boş olmalı**; yoksa her turda boş bildirim gider.
- Defteri (CSV/DB) güncelleyen eşleme fonksiyonunu **canlı kopya üzerinde değil, kopya dosyada** test et — deneme kaydı canlı kaydı kirletir. Yazma öncesi otomatik yedek al.
- Aşama etiketlerini mevcut sözlüğe uydur (ör. `4-TEST_INTEREST (gonderildi)`) — yeni bir numaralandırma icat etme.

## 6. Uçtan uca kabul kriteri

Kurulum "çalışıyor" sayılmaz, **şu dördü kanıtlanana kadar**:
1. Yanlış token → 401 + sebep,
2. Doğru token → 200 + olay gövdesi geri döner,
3. Bildirim gerçekten ulaştı (mesaj kimliği/numarası okundu),
4. Cron kendi başına yakaladı (koşu kaydı `ok`, olay kalıcı dosyada).
