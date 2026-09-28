# Cron Optimizasyonu — 10 Ağustos 2026

## Yapılan Değişiklikler

17 cron → 16 cron. 5 agent-bazlı cron, no_agent script'e dönüştürüldü.

### Kaldırılan
| Cron | ID | Neden |
|------|-----|-------|
| `jeff-sabah-brifingi` | 42c3ab51bb51 | Jeff 3.0 sabah brifingiyle duplicate. Legacy v2. |

### Script'e Dönüştürülen (Agent → no_agent)
| Cron | ID | Yeni Script |
|------|-----|-------------|
| `kart-hatirlatma-denizbank` | 00a544d157bf | `kart-denizbank.sh` |
| `kart-hatirlatma-yk-hepsiburada` | 61619946928b | `kart-yk-hepsiburada.sh` |
| `kart-hatirlatma-yk-word-eko` | c108c1fb204a | `kart-yk-word-eko.sh` |
| `jeff3-sabah-brifingi` | f9b167b548d8 | `jeff3-sabah-brifingi.sh` |
| `jeff3-aksam-raporu` | cc01072ea451 | `jeff3-aksam-raporu.sh` |

### Schedule Değişikliği
| Cron | Önce | Sonra | Neden |
|------|------|-------|-------|
| `rakip-monitoring` | Pzt 10:00 | Pzt **10:05** | `hermes-watchdog` ile çakışma |

## Sonuç

| Metrik | Önce | Sonra |
|--------|:----:|:-----:|
| Toplam cron | 17 | 16 |
| Agent-bazlı | 8 | **3** |
| Script-bazlı | 9 | **13** |
| Günlük LLM call tasarrufu | — | ~4-5 |

## Kalan Agent-Bazlı Cron'lar (3)

Bunlar script'e çevrilemez — gerçekten LLM reasoning gerektiriyor:
- `haftalik-dis-dunya-briefi` — Web araması + AI sentezi
- `rakip-monitoring` — Rekabet analizi + web kazıma
- `dental-lead-gen` — X/web kazıma + lead keşfi

## Agent-to-Script Dönüşüm Pattern'i

1. Script `/home/hermes/.hermes/scripts/<name>.sh` olarak yaz
2. `chmod +x`
3. `cronjob(action="update", job_id="...", no_agent=true, script="<name>.sh")`
4. `bash ~/.hermes/scripts/<name>.sh` ile test et
5. stdout = kullanıcıya teslim edilecek mesaj

### Basit Hatırlatma Script Template
```bash
#!/bin/bash
echo "💳 BAŞLIK"
echo ""
echo "🔔 Mesaj içeriği"
echo ""
echo "⏰ $(date '+%d.%m.%Y %H:%M')"
```

### Sistem Durum Script Template
```bash
#!/bin/bash
echo "## ⚙️ Süreçler"
/path/to/status_command 2>&1
echo ""
echo "## 💻 Sistem"
echo "Disk: $(df -h / | awk 'NR==2{print $3 "/" $2 " (" $5 ")"}')"
echo "RAM:  $(free -h | awk '/^Mem:/{print $3 "/" $2}')"
echo "⏰ $(date '+%d.%m.%Y %H:%M')"
```

## Oluşturulan Script Dosyaları

- `/home/hermes/.hermes/scripts/kart-denizbank.sh`
- `/home/hermes/.hermes/scripts/kart-yk-hepsiburada.sh`
- `/home/hermes/.hermes/scripts/kart-yk-word-eko.sh`
- `/home/hermes/.hermes/scripts/jeff3-sabah-brifingi.sh`
- `/home/hermes/.hermes/scripts/jeff3-aksam-raporu.sh`

## Hermes Güncelleme — 10 Ağustos 2026

Hermes v0.20.0 zaten yüklü (git install, `/home/hermes/.hermes/hermes-agent`).
1 commit geride.

**Güncelleme yöntemleri:**
- ✅ `hermes update` — çalışır ama gateway restart agent'ı kestiği için **60sn timeout** olur. Güncelleme arka planda başarılıdır, `hermes version` ile kontrol et
- ✅ `cd ~/.hermes/hermes-agent && git pull` — timeout alternatifi
- ❌ `pip install git+https://...` — Hermes wheel oluşturmayı reddeder (`Building wheels for hermes-agent is not supported`)
- ❌ `python3.12 -m pip install --upgrade hermes-agent` — aynı sebepten başarısız

**⚠️ `hermes update` Timeout Tuzağı:** Gateway restart yapıp kendi agent process'ini keser → komut timeout olur. `hermes version` ile gerçekten güncellendi mi kontrol et. Güncellenmediyse `git pull` yap.

v0.20.0 highlights: streaming voice + barge-in, wake words, grounded citations, outbound webhooks, A2A protocol, desktop artifacts + plugin SDK, CLI `!command` `/init` `/diff`, 10x faster project loading.
