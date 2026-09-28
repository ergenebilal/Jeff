# Gateway Bakım & Sistem Operasyonları

## Gateway Graceful Restart

**🚨 KRİTİK UYARI — Self-Kill Tehlikesi**

Gateway'i restart etmek, O ANDA gateway üzerinden konuşan AKTİF session'ı öldürür. Telegram'daki Jeff restart atarsa **kendi fişini çeker** — konuşma anında kopar, yazılmamış cevap kaybolur.

**Kullanıcı bu hataya ikinci kez tepki verdi (13.06.2026):** \"Yine kendi fişini çektin.\" Bu bir daha yaşanmamalı.

### Doğru Yöntem

```bash
# Graceful restart — mevcut session'ların bitmesini bekler (180sn)
hermes gateway restart --system
```

### Yanlış Yöntem

```bash
sudo systemctl restart hermes-gateway  # ❌ ANINDA ÖLDÜRÜR, session kaybı
```

Config'de `restart_drain_timeout: 180` zaten var. `hermes gateway restart --system` bu süre boyunca session'ların bitmesini bekler.

### Kural

- Gateway restart gerekiyorsa: **Telegram'daki Jeff talimat verir, terminal'deki Jeff veya kullanıcı çalıştırır**
- Acil değilse: gece 03:00 gibi boş zamana planla
- Kritikse: kullanıcıya "şimdi restart et" de, o yapsın

## Cron Bakımı

### İki Ayrı Cron Sistemi

1. **Hermes Cron** — Gateway üzerinden çalışır. `cronjob` tool ile yönetilir. SCRIPT'leri `~/.hermes/scripts/` altında yaşar.
2. **Sistem Crontab** — Eski legacy. `crontab -l` ile görülür. Genelde `/opt/hermes/venv/` gibi eski path'ler kullanır.

### Legacy Cron Temizliği

```bash
# Yedekle
crontab -l > ~/backups/crontab-legacy-yedek.txt
# Sil
crontab -r
```

Kural: tüm cron işleri Hermes cron üzerinden yürütülür. Sistem crontab'ı legacy'dir, temizlenir.

### Hermes Cron Jobs.json Yapısı

`~/.hermes/cron/jobs.json` — `{"jobs": [...]}` formatında. Her job'ın:
- `id`: Benzersiz ID
- `script`: Script yolu. Runner `~/.hermes/scripts/` base'ine eklenir. `script: scripts/x.py` → `~/.hermes/scripts/scripts/x.py` olur (double scripts!). Workdir path'i etkilemez — sadece LLM context içindir.
- `no_agent`: True (0 token harcar) / False (LLM çağırır)
- `schedule`: Cron expression
- `deliver`: `local` (sessiz), `origin` (kullanıcıya), `telegram:chat_id`

### Script Konumları

| Cron Job | Script Yolu |
|----------|-------------|
| no_agent script'leri | `~/.hermes/scripts/<script>` |
| agent job'ları | Prompt ile çalışır, skills + model override kullanır |
| workdir job'ları | Belirtilen workdir altında çalışır |

## Browser Yönetimi

Hermes'te browser iki şekilde çalışır: local Playwright veya cloud Browserbase.

### Playwright (Local)

```bash
# Kurulum
npx playwright install chromium

# MCP olarak kullan
@playwright/mcp
```

Artı: ücretsiz, offline
Eksi: RAM tüketir (~300MB+), bot detection'a takılır

### Browserbase (Cloud)

```bash
# .env'e key
BROWSERBASE_API_KEY=bb_live_xxxx

# Config'de backend
browser:
  backend: browserbase
  engine: auto
```

Artı: sıfır RAM, anti-detection, stabil
Eksi: ücretli (free tier var), internet gerekli

### Geçiş Prosedürü

```yaml
# config.yaml
browser:
  backend: browserbase   # Playwright → Browserbase
  engine: auto
  allow_private_urls: false
```

Playwright MCP npm paketini kaldır:
```bash
npm uninstall -g @playwright/mcp
```

Gateway restart gerekir:
```bash
hermes gateway restart --system
```

### Test

```bash
# Browserbase aktif mi?
hermes browser navigate https://example.com
# Stealth warning: "Running WITHOUT residential proxies" = free tier normal
```

## Disk Bakımı

### Hızlı Kazançlar

| Ne | Nerede | Tipik Boyut |
|----|--------|-------------|
| Docker dangling image'ler | `docker image prune -f` | ~0-500MB |
| HuggingFace cache | `~/.cache/huggingface/hub/` (rm -rf) | 3-4GB |
| npm npx cache | `~/.npm/_npx/` (rm -rf), `npm cache clean --force` | 2-3GB |
| pip cache | `pip3 cache purge` | 100-200MB |
| Docker builder cache | `docker builder prune -af` | ~0-500MB |
| Docker unused volumes | `docker volume prune -f` | ~0-100MB |

### Docker Image Envanteri

Büyük image'leri kontrol ederken hangileri container'ı olan (kullanılan) hangileri atıl:

```bash
docker ps --format "{{.Image}}" | sort -u  # Kullanılan image'ler
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | sort -k3 -h -r
```

Container'ı olmayan image'ler güvenle silinebilir:
```bash
docker rmi <image_id>
```

### Snapshot Alma

Disk temizliği öncesi:
```bash
df -h /  # Kullanımı kaydet
```
Sonra:
```bash
df -h /  # Kazancı hesapla
```

## Gateway Crash Loop Prevention

### Root Cause: --replace + drop_pending_updates=True Crash Loop

systemctl start (--replace ile) → yeni process eskiye SIGTERM gönderir → eski exit code 1 → systemd Restart=always tetiklenir → yeni process başlarken Telegram eski polling bağlantısını hâlâ açık tutar → "409 Conflict: terminated by other getUpdatesRequest" → drop_pending_updates=True mesajları SİLER → tekrar SIGTERM → loop.

Belirtiler: Gateway saniyede bir restart, Telegram mesajları kaybolur, log'da "409 Conflict".

### Kalıcı Çözüm
1. `--replace` kaldır → `/etc/systemd/system/hermes-gateway.service` (systemd tek instance yönetsin)
2. `drop_pending_updates=True` → `False` → `/home/hermes/.local/lib/python3.11/site-packages/gateway/platforms/telegram.py`
   (Eski doküm: `/opt/hermes/gateway/platforms/telegram.py` veya `hermes.gateway.platforms.telegram` import'u ÇALIŞMAZ — doğru yol yukarıdaki gibidir. `import gateway.platforms.telegram` ile bulunur.)
3. **Replace sayısı:** Mevcut kodda 2 yerde `drop_pending_updates=True` kalır (webhook başlatma satırı ~2181 + polling başlatma satırı ~2214). Eski doküm "4 yerde" demişti — versiyon değişti, güncel kodda 2 kaldı. `grep -n "drop_pending_updates"` ile kontrol et.

### Pitfall: `hermes gateway service install` --replace'i Geri Ekler
`hermes gateway service install --replace` komutu systemd unit'ini yeniden oluşturur ve **`--replace` flagini tekrar ekler**. Şu durumlar tetikler:
- Stale unit warning: `TimeoutStopSec=90s but drain_timeout=180s` uyarısına yanıt olarak `hermes gateway service install` koşulması
- `hermes doctor` fix önerisi
- Manuel `hermes gateway service install` çalıştırma

**Kontrol:** `grep ExecStart /etc/systemd/system/hermes-gateway.service` — `--replace` hâlâ duruyorsa sed ile temizle.

### Pitfall: 20-restart-hardening.conf TimeoutStopSec Override
`/etc/systemd/system/hermes-gateway.service.d/20-restart-hardening.conf`:
```
[Service]
KillMode=control-group
TimeoutStopSec=60
SendSIGKILL=yes
```
Bu override, main service'in `TimeoutStopSec=210` değerini **ezerek** 60sn'ye düşürür. Gateway'in drain_timeout=180sn'den kısa olduğu için stale unit uyarısı alınır. Bu uyarı `hermes gateway service install` komutunu tetikleyebilir → `--replace` geri gelir → crash loop döner.

### Pitfall: Memory Provider Setup Cron'u Gateway'i Beklenmedik Anda Restart Eder
`restart-gateway-for-hindsight` gibi cron job'lar gateway'i restart eder. Eğer `--replace` hâlâ aktifse crash loop tetiklenir. **Kural:** Gateway restart eden herhangi bir cron job'u oluşturmadan ÖNCE `--replace`'in kaldırıldığını doğrula.

### Diagnostik Sırası (22.06.2026 doğrulanmış)
Telegram yanıt vermiyorsa şu sırayı izle:
1. `systemctl status hermes-gateway` — PID, uptime, restart sayısı
2. `grep ExecStart /etc/systemd/system/hermes-gateway.service` — `--replace` var mı?
3. `grep -n "drop_pending_updates" /home/hermes/.local/lib/python3.11/site-packages/gateway/platforms/telegram.py` — hâlâ True olan var mı?
4. `journalctl -u hermes-gateway --since "1 hour ago" | grep -c "409 Conflict\|SIGTERM"` — crash loop var mı?

### Kalıcı Çözüm Komutları (22.06.2026 doğrulanmış)
```bash
# 1. --replace kaldır
sudo sed -i 's/ --replace//g' /etc/systemd/system/hermes-gateway.service

# 2. drop_pending_updates fix (dogru path)
TELEGRAM_PY=$(python3.11 -c "import gateway.platforms.telegram; print(gateway.platforms.telegram.__file__)")
sudo sed -i 's/drop_pending_updates=True/drop_pending_updates=False/g' "$TELEGRAM_PY"

# 3. systemd yenile + restart
sudo systemctl daemon-reload && sudo systemctl restart hermes-gateway
```

### İki Farklı Terminal/Gateway Çökme Sebebi
1. Python 3.12 shebang/modül çakışması → segfault
2. --replace + drop_pending_updates crash loop → restart döngüsü

## Self-Kill Test

Gateway restart'ının self-kill yapıp yapmadığını anlamak için:
- Terminal'den restart at → Telegram session'ı koparsa = self-kill
- Yeni PID kontrolü: `pgrep -f "gateway run" | head -1` eski PID'den farklı olmalı
