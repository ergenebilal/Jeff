# Opencode-Go `x-opencode-session` Header Zorunluluğu — Kron Job Etkisi

## Olay (08.09.2026)

OpenCode Go provider yeni sürümde `x-opencode-session` header'ı zorunlu hale getirdi. Bu header'tı göndermeyen tüm istekler `HTTP 400: Error from provider (Console Go): Request is missing x-opencode-session` hatası veriyor.

**Etkilenen yapılar:**
- Tüm cron job'lar provider'ı `opencode-go` olanlar (cronjob action=update ile override yapılabilir)
- `hermes` vision analyze (auxiliary.vision.provider = opencode-go)
- `hermes` auxiliary.task'lar (compression, approval, mcp, title_generation — hepsi opencode-go)

## Etkilenen 6 Cron Job (08.09.2026 olayında)

| Job ID | Isim | Eski Provider | Yeni Provider | Sonuç |
|---|---|---|---|---|
| `cc1508f1014e` | dental-lead-gen | opencode-go / mimo-v2.5 | nous / solar-pro4:free | ✅ |
| `9da0c57904f2` | NotebookLM Health Check | opencode-go / mimo-v2.5 | nous / solar-pro4:free | ✅ |
| `68b617237110` | gunun-firsat-brifi | opencode-go / mimo-v2.5 | nous / solar-pro4:free | ✅ |
| `62fba83b49d4` | saglik-sabah-rutin | opencode-go / mimo-v2.5 | nous / solar-pro4:free | ✅ |
| `2d0a6e937a25` | saglik-aksam-kontrol | opencode-go / mimo-v2.5 | nous / solar-pro4:free | ❌ 429 (geçici) |
| `99ed138e81b3` | saglik-haftalik-tartim | opencode-go / mimo-v2.5 | nous / solar-pro4:free | ✅ |

Fix komutu (her job için):
```
cronjob action=update job_id=<JOB_ID> model='{"model":"upstage/solar-pro4:free","provider":"nous"}'
```

## Vision Analyze Etkisi

`vision_analyze` tool'u auxiliary.vision provider'ını kullanıyor — config.yaml'da `opencode-go`. Bu nedenle image analizi de aynı `x-opencode-session` hatasını veriyor:

```
Error code: 400 - {'type': 'error', 'error': {'type': 'MissingSessionID', 'message': 'Error from provider (Console Go): Request is missing x-opencode-session...'}}
```

**Fix:** auxiliary.vision.provider'ı değiştirmek için config.yaml düzenlenmeli (patch reddediyor — python+yaml+os.replace kullan). Veya vision için ayrı bir provider/ayrintı eklenmeli. Şu an için vision tool'u çalışmıyor, alternatif yöntem needed.

## Provider/Model Override Komutları

### Cron job override
```
cronjob action=update job_id=XXXXX model='{"model":"upstage/solar-pro4:free","provider":"nous"}'
```

### Config.yaml auxiliary provider'ları (patch reddedilir, python+yaml kullan)
```python
import yaml, os
with open('/home/hermes/.hermes/config.yaml') as f:
    cfg = yaml.safe_load(f)
cfg['auxiliary']['vision']['provider'] = 'nous'
cfg['auxiliary']['vision']['model'] = 'upstage/solar-pro4:free'
# ... diğer auxiliary section'lar
with open('/home/hermes/.hermes/config.yaml.new', 'w') as f:
    yaml.dump(cfg, f)
os.replace('/home/hermes/.hermes/config.yaml.new', '/home/hermes/.hermes/config.yaml')
```

### Kontrol
```
cronjob action=list  # tüm job'ları göster, model/provider sütunu
grep -A4 "auxiliary:" ~/.hermes/config.yaml  # auxiliary provider'ları göster
```

## Provider Seçimi Notları

- `nous` provider + `upstage/solar-pro4:free` model → Portal OAuth üzerinden çalışıyor, JWT minting otomatik
- `openrouter` provider → alternatif, model seçimi OpenRouter catalog'ından
- `opencode-go` provider → `x-opencode-session` header zorunlu, kaçınılmalı cron/auxiliary için
- `mimo-v2.5` model → opencode-go provider ile birlikte kullanıldı, bu combo artık problematic

**Şu anki working combo:** `model: upstage/solar-pro4:free`, `provider: nous` (main + 6 cron). Auxiliary provider'ları hala opencode-go — tehdit devam ediyor.
