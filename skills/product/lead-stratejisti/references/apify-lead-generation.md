# Apify Lead Generation — Kullanım Kılavuzu

Skills Hub'dan kurulu skill: `apify-lead-generation` (hub-installed, protected)

## Ön Koşullar

- `APIFY_TOKEN` ~/.hermes/.env'de tanımlı
- `mcpc` CLI kurulu (`npm install -g @apify/mcpc`)
- Hesap: `apricot_hornbill` (ergeneonline@gmail.com)

## API Kullanımı

### Actor ID Formatı

Apify API'sinde actor ID'lerinde `/` yerine `~` kullanılır:

| Platform | Actor ID |
|----------|----------|
| Google Maps | `compass~crawler-google-places` |
| Instagram profilleri | `apify~instagram-profile-scraper` |
| TikTok | `clockworks~tiktok-scraper` |
| Facebook sayfaları | `apify~facebook-pages-scraper` |
| Google Search | `apify~google-search-scraper` |
| YouTube | `streamers~youtube-scraper` |

### Python ile Actor Çalıştırma

```python
import urllib.request, json, time

token = "APIFY_TOKEN"  # .env'den oku
actor_id = "compass~crawler-google-places"

# Actor'ü başlat
run_input = {
    "searchStringsArray": ["Mudanya güzellik merkezi"],
    "maxResults": 5,
    "language": "tr",
    "region": "tr"
}

req = urllib.request.Request(
    f"https://api.apify.com/v2/acts/{actor_id}/runs",
    data=json.dumps(run_input).encode(),
    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    method="POST"
)
with urllib.request.urlopen(req, timeout=30) as resp:
    run = json.loads(resp.read())["data"]
    run_id = run["id"]

# Polling ile tamamlanmayı bekle
for _ in range(20):
    time.sleep(3)
    req = urllib.request.Request(
        f"https://api.apify.com/v2/acts/{actor_id}/runs/{run_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        status = json.loads(resp.read())["data"]["status"]
    if status == "SUCCEEDED":
        break

# Sonuçları al
if status == "SUCCEEDED":
    req = urllib.request.Request(
        f"https://api.apify.com/v2/datasets/{dataset_id}/items?limit=10",
        headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        results = json.loads(resp.read())
```

### Önemli Notlar

- **Token yazarken bash kullanma** — Python string concatenation kullan (bash `!`, `$` gibi karakterleri boğar)
- **Token 46 karakter**, `.env`'ye Python ile yaz
- **mcpc** ile Actor schema sorgulanabilir: `mcpc --json mcp.apify.com --header "Authorization: Bearer $APIFY_TOKEN" tools-call fetch-actor-details actor:="ACTOR_ID"`
- **First run:** Apify console'da yeni actor'ü ilk çalıştırmada onaylaman gerekebilir
- **Rate limit:** Apify ücretsız planda aylık $5 kredi verir, her run ~$0.01-0.05
