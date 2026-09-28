# Canva Connect API — OAuth 2.0 + PKCE Flow (Working, 16.06.2026)

> Durum: OAuth flow basarili, access_token + refresh_token aliniyor.
> PDF uretimi icin henuz kullanilmiyor — Playwright daha kararli (Canva API listing ve brand template kisitlari nedeniyle).

## OAuth Akisi (PKCE — Calisan Versiyon)

### 1. PKCE Parametreleri Olustur ve Kaydet

```python
import secrets, hashlib, base64, json, os

verifier = secrets.token_urlsafe(64)
digest = hashlib.sha256(verifier.encode()).digest()
challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()

# KALICI KAYDET (~/.hermes/canva_pkce.json)
pkce_data = {"verifier": verifier, "challenge": challenge, "created_at": datetime.now().isoformat()}
with open(os.path.expanduser("~/.hermes/canva_pkce.json"), "w") as f:
    json.dump(pkce_data, f, indent=2)
```

**Neden kaydetmek zorunlu?** Bilal linke tikladiktan sonra code gelir. Code'u token'a cevirmek icin verifier lazim. Verifier kaybolursa token alinamaz ve Bilal'e tekrar link yollamak gerekir. Bu 2+ kere tekrarlanmamali.

### 2. Authorization URL

```
https://www.canva.com/api/oauth/authorize
  ?client_id=OC-AZ6tSp28HQ95
  &redirect_uri=https://ergeneai.com/canva-callback
  &response_type=code
  &scope=design:content:read%20design:content:write%20brandtemplate:content:read%20brandtemplate:content:write%20asset:read
  &code_challenge=<S256_CHALLENGE>
  &code_challenge_method=S256
```

Scope'lar:
- `design:content:read` — tasarim icerigini okuma
- `design:content:write` — tasarim olusturma
- `brandtemplate:content:read` — brand template icerigini okuma
- `brandtemplate:content:write` — brand template yazma
- `asset:read` — asset metadata okuma
- NOT: `brandtemplate:meta:read` eklenmedi — brand template listeleme icin gerekli ama Enterprise plan gerekli

### 3. Callback Proxy Altyapisi (Traefik + socat)

Canva, kullanici yetkilendirince redirect_uri'ye yonlendirir:
```
https://ergeneai.com/canva-callback?code=<AUTH_CODE>
```

**Mimari:**
```
Kullanici (tarayici)
  -> ergeneai.com/canva-callback?code=...
    -> Traefik (Docker) -> HTTPS handling + Lets Encrypt
      -> socat container (alpine/socat:latest)
        -> --add-host host.docker.internal:host-gateway
          -> host:8889 (/opt/hermes/hq/server.py)
            -> code /tmp/canva_code.txt'ye yazilir
```

**socat container kurulumu:**
```bash
docker rm -f canva-proxy 2>/dev/null
docker run -d --name canva-proxy \
  --restart unless-stopped \
  --network coolify \
  --add-host host.docker.internal:host-gateway \
  --label 'traefik.enable=true' \
  --label 'traefik.http.routers.canva-callback.rule=Host(`ergeneai.com`) && PathPrefix(`/canva-callback`)' \
  --label 'traefik.http.routers.canva-callback.priority=100' \
  --label 'traefik.http.routers.canva-callback.entryPoints=https' \
  --label 'traefik.http.services.canva-callback.loadbalancer.server.port=8889' \
  --label 'traefik.http.routers.canva-callback.tls=true' \
  --label 'traefik.http.routers.canva-callback.tls.certresolver=letsencrypt' \
  alpine/socat:latest tcp-listen:8889,fork,reuseaddr tcp-connect:host.docker.internal:8889
```

**Server.py callback handler (port 8889):**
```python
if path == "/canva-callback":
    query = parsed.query  # "code=eyJ...&state=..."
    with open("/tmp/canva_code.txt", "w") as f:
        f.write(query)
    # HTML sayfasi goster: "Canva Yetkilendirme Basarili"
    # JS fallback: fetch('/api/canva-code?q='+encodeURIComponent(window.location.search))
```

### 4. Code'u Oku

Bilal "tamam" dediginde /tmp/canva_code.txt kontrol et:
```bash
cat /tmp/canva_code.txt
# Output: code=eyJraW...4IQA  (JWT formatinda, ~1300+ byte)
```

1361 byte civarinda olmali — bir JWT. Daha kisa veya "..." iceriyorsa truncate olmus olabilir.

### 5. Code -> Token Donusumu

```python
import urllib.request, urllib.parse, json

with open("/home/hermes/.hermes/canva_pkce.json") as f:
    pkce = json.load(f)
verifier = pkce["verifier"]

with open("/tmp/canva_code.txt") as f:
    code = f.read().strip().replace("code=", "", 1)

data = {
    "grant_type": "authorization_code",
    "code": code,
    "client_id": "OC-AZ6tSp28HQ95",
    "client_secret": "<CLIENT_SECRET>",
    "redirect_uri": "https://ergeneai.com/canva-callback",
    "code_verifier": verifier,
}

req = urllib.request.Request(
    "https://api.canva.com/rest/v1/oauth/token",
    data=urllib.parse.urlencode(data).encode(),
    headers={"Content-Type": "application/x-www-form-urlencoded"},
)

with urllib.request.urlopen(req, timeout=15) as resp:
    result = json.loads(resp.read())

# Token'ı kaydet
with open("/home/hermes/.hermes/canva_token.json", "w") as f:
    json.dump(result, f, indent=2)
```

**Response:**
```json
{
  "access_token": "eyJraW...hPlQ",
  "refresh_token": "eyJhbG...AjSg",
  "token_type": "Bearer",
  "expires_in": 14400,
  "scope": "design:content:read design:content:write brandtemplate:content:read brandtemplate:content:write asset:read"
}
```

### 6. Token Yenileme (Cron ile)

```bash
curl -s -X POST "https://api.canva.com/rest/v1/oauth/token" \
  -d "grant_type=refresh_token" \
  -d "refresh_token=<REFRESH_TOKEN>" \
  -d "client_id=OC-AZ6tSp28HQ95" \
  -d "client_secret=<CLIENT_SECRET>"
```

Cron job: `canva-token-refresh` (her 3 saatte bir, deliver=local, 4 saat token suresi icin yeterli)

## Calisan API'ler

| Endpoint | Method | Status |
|----------|--------|--------|
| /rest/v1/users/me | GET | OK — user_id + team_id doner |
| /rest/v1/assets/{assetId} | GET | OK — asset metadata |
| /rest/v1/designs | POST | OK — yeni tasarim olusturma |
| /rest/v1/oauth/token | POST | OK — token alma/yenileme |

## Calismayan / Kisitli API'ler

| Endpoint | Method | Hata | Cozum |
|----------|--------|------|-------|
| /rest/v1/designs | GET | 403 | design:content:read listing yetkisi vermiyor. Sadece ID ile sorgulama. |
| /rest/v1/brand-templates | GET | 403 missing_scope: brandtemplate:meta:read | Enterprise plan gerekli |
| /rest/v1/autofills | POST | Enterprise only | Enterprise plan gerekli |
| /rest/v1/exports | POST | ? | Apps SDK gerekiyor olabilir |

## Bilinen Kisitlar

1. **client_credentials DESTEKLEMEZ** — sadece authorization_code veya refresh_token
2. **Auth code 10 dk gecerli** — Bilal linke tiklayip "tamam" dediginde hemen token'a cevir
3. **Design listing endpoint'i YOK** — designs listesi alamazsin, sadece ID ile tek tek sorgula
4. **Brand template'ler Enterprise plan gerekli** — PDF icin Playwright kullan
5. **Redirect URI HTTPS zorunlu** — ergeneai.com uzerinden Traefik ile proxy cozumu calisiyor
6. **Scope eklemek icin yeni auth lazim** — Bilal tekrar yetkilendirmeli

## Token Dosyalari

| Dosya | Icerik |
|-------|--------|
| ~/.hermes/canva_token.json | {access_token, refresh_token, token_type, expires_in, scope} |
| ~/.hermes/canva_pkce.json | {verifier, challenge, created_at} |

## OAuth Dongusune Girme Kurali (Kritik)

**Ayni OAuth adimini 2 kereden fazla tekrarlama.** Bilal linke tiklar, "tamam" der. Token alinamazsa (code expired, secret yanlis, proxy calismiyorsa) ayni yontemi tekrar deneME. Yontem degistir:

1. Ilk denemede PKCE + callback calisir -> duzgun calismali
2. Calismazsa -> proxy'yi kontrol et (container, log), sonra yeni link ver
3. Ikinci denemede de calismazsa -> Playwright'a gec, Canva'yi rafa kaldir

## Playwright PDF (Kararli Alternatif)

Canva API kisitlari nedeniyle PDF'ler Playwright ile HTML->PDF olarak uretilir:
- Konum: `/opt/hermes/scripts/pdf-playwright.py`
- Tasarim: Premium v2 (Plus Jakarta Sans, full-bleed cover, score cards, issue cards)
- Kalite: 250-270 KB, profesyonel gorunum
- Hiz: 7 lead PDF + email ~30 saniye
