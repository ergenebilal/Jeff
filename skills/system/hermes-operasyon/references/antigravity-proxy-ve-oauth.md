# Google Antigravity OAuth Proxy — Mimari, Hesaplar ve Canlı Teşhis

Bu belge, Google Antigravity OAuth proxy eklentisi (`antigravity_mrhisyammm` / `hermes-antigravity-auth`) altyapısını ve sorun giderme adımlarını açıklar.

---

## 1. Mimari ve Çalışma Mantığı

- **Yerel Proxy:** Eklenti arka planda `127.0.0.1:8999` portunda OpenAI uyumlu hafif bir proxy sunucusu açar.
- **ThreadingHTTPServer Zorunluluğu:** Python varsayılan `http.server.HTTPServer` tek iş parçacıklıdır (single-threaded). Arka planda uzun bir LLM/thinking isteği (POST) çalışırken gelen tüm sağlık kontrolleri (GET `/v1/models`) ve paralel istekler kilitlenir (`HTTP 000 / timeout`). Sunucu mutlaka `ThreadingHTTPServer` (`daemon_threads=True`) ile koşturulmalıdır.
- **Upstream Zaman Aşımı (120s):** Ağır bağlamlı istemler ve muhakeme (thinking) modelleri için proxy içi `urlopen` timeout değeri en az 120s olmalıdır (30s yetersiz kalıp zamansız failover üretir).
- **Model Dönüştürme:** OpenAI `/v1/chat/completions` isteklerini Google CloudCode dahili API formatına (`v1internal:generateContent` / `streamGenerateContent`) çevirir.
- **Şema Temizliği:** Gemini `functionDeclaration` protobuf doğrulaması katıdır; OpenAI tool şemalarındaki desteklenmeyen alanlar (`exclusiveMinimum` vb.) otomatik temizlenir.
- **Model Haritalama:**
  - `gemini-3.5-flash` → `gemini-3-flash`
  - `claude-3-5-sonnet-latest` → `claude-sonnet-4-6`
  - `claude-3-opus-20240229` → `claude-opus-4-6-thinking`

---

## 2. Hesap Veritabanı ve Rotasyon

- **Veritabanı Yolu:** `~/.config/opencode/antigravity-accounts.json` (fallback: `~/AppData/Local/hermes/antigravity-accounts.json`).
- **Çoklu Hesap & Eşit Dağılım:** Hesaplar OAuth `refreshToken` ile saklanır. Yapışkan (sticky) hesap tüketimi önlenmiş olup, istekler havuzdaki tüm aktif hesaplar arasında Round-Robin (`0 → 1 → 2 → 3 → 0`) mantığıyla eşit dağıtılır.
- **Hızlı Devretme ve İzole Cooldown (Fast Failover):**
  - `claude` ve `gemini` model ailelerinin bekleme süreleri (cooldown) hesaba ve aileye özel bağımsız izlenir (`email:family`).
  - Upstream `urlopen` zaman aşımı hesap denemesi başına **15s** (120s değil) tutulmalıdır. 120s gibi yüksek değerler yanıt vermeyen bir hesapta 2 dakikalık gereksiz gecikme üretir; 15s darlığı sıradaki hesaba anında failover sağlar.
  - HTTP işleyicilerinde (`do_GET`, `do_POST`) socket yazma adımları `try...except (BrokenPipeError, ConnectionResetError, socket.error): pass` ile sarmalanmalıdır; erken kopan istemci socket'leri sunucu loglarını kirletmez.
  - Bir hesap Gemini'de 429/403 yerse, aynı hesabın Claude kotası etkilenmez veya havuzdaki 2. hesaba geçilir.
  - Hızlı İyileşme (Fast Recovery): 429/403 hatalarında bekleme kademesi 15s → 60s → 300s → 900s olarak uygulanır. 500/502/503/504 geçici sunucu hatalarında ise anında diğer hesaba geçmek üzere 10s kısa soğuma verilir.
- **Yedek Sağlayıcı (Fallback Providers):** Proxy havuzundaki hesapların tamamı kotaya takılırsa sistem kesintiye uğramasın diye `~/.hermes/config.yaml` içinde `fallback_providers: ['openrouter']` tanımlanmalıdır.

---

## 3. Gateway Bekçisi Entegrasyonu (Watchdog)

- `gateway-healthcheck.sh` script'i 5 dakikada bir (veya 1 dakikalık zamanlayıcıda) `http://127.0.0.1:8999/v1/models` ucunu aktif olarak probe eder.
- Yanıt 200 harici gelirse (`000` / `timeout`), bekçi 5 saniye sonra ikinci bir doğrulama yapar ve proxy/gateway servisini otonom olarak yeniden başlatır.

---

## 3. Telegram ve İstemci Zaman Aşımı (Timeout & Heartbeat) Yönetimi

Antigravity proxy arkasında çalışan modeller (Gemini 3.6 Flash / Claude 3.5 Sonnet) ağır bağlam işlerken İlk Token (TTFT) veya tam yanıt süresi **40-70 saniye** sürebilir.

- **Telegram Bot Zaman Aşımı Fixi:** Telegram istemcisinde (`Application.builder()`) varsayılan zaman aşımları yetersiz kalırsa bot bağlantıyı düşürür. `read_timeout=300`, `write_timeout=300` ve `connect_timeout=60` olarak ayarlanmalıdır.
- **Periyodik Sinyal (Continuous Typing Heartbeat):** Model yanıtı üretilirken Telegram kütüphanesinin bağlantıyı koptu saymasını önlemek için model çağrısı boyunca arka planda periyodik bir kalp atışı görevi (`asyncio.create_task` ile her 4 saniyede bir `send_action("typing")`) çalıştırılmalı, işlem tamamlandığında `finally` bloğunda iptal edilmelidir.

---

## 3. Canlı Teşhis ve Probe Script'i

Hermes veya CLI bağımsız olarak proxy ve OAuth hesaplarının canlı durumunu test etme:

```python
import json, urllib.request, urllib.parse, os

# 1. Local Proxy Canlılık
try:
    with urllib.request.urlopen('http://127.0.0.1:8999/v1/models', timeout=3) as r:
        print("Proxy Status: ACTIVE (HTTP 200)")
except Exception as e:
    print("Proxy Error:", e)

# 2. Hesapların OAuth & API Canlılığı
acc_path = os.path.expanduser('~/.config/opencode/antigravity-accounts.json')
data = json.load(open(acc_path))

ENDPOINT = 'https://daily-cloudcode-pa.sandbox.googleapis.com'
CLIENT_ID = '[REDACTED_CLIENT_ID]'
CLIENT_SECRET = '[REDACTED_CLIENT_SECRET]'

def get_token(ref):
    url = 'https://oauth2.googleapis.com/token'
    body = urllib.parse.urlencode({
        'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET,
        'refresh_token': ref, 'grant_type': 'refresh_token'
    }).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())['access_token']

for acc in data.get('accounts', []):
    email = acc.get('email')
    ref = acc.get('refreshToken')
    try:
        token = get_token(ref)
        url = f'{ENDPOINT}/v1internal:generateContent'
        body = json.dumps({
            'project': acc.get('projectId', 'alfredandjeff'),
            'model': 'gemini-3-flash',
            'request': {'contents': [{'role': 'user', 'parts': [{'text': 'ping'}]}], 'generationConfig': {'maxOutputTokens': 5}}
        }).encode()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'User-Agent': 'antigravity/windows/amd64',
            'X-Goog-Api-Client': 'google-cloud-sdk vscode_cloudshelleditor/0.1',
            'Client-Metadata': '{"ideType":"ANTIGRAVITY","platform":"PLATFORM_UNSPECIFIED","pluginType":"GEMINI"}'
        }
        req = urllib.request.Request(url, data=body, headers=headers)
        with urllib.request.urlopen(req) as resp:
            print(f"Account {email}: OK (HTTP 200 - Sıfır Cooldown)")
    except Exception as e:
        print(f"Account {email} Error:", e)
```

---

## 4. Tuzaklar

- `127.0.0.1:8999` dinlemiyorsa eklenti başlatılmamış demektir.
- `antigravity-accounts.json` dosyası hem OpenCode hem Hermes tarafından ortak kullanılır; birinde oturum açılınca diğerine otomatik yansır.
- Proxy logları: `~/.hermes/antigravity-proxy-errors.log` dosyasında tutulur. Hata teşhisinde burayı oku.
