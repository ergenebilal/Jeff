---
name: sistem-durumu
version: 3.0.0
author: Jeff
description: Jeff'in (Hermes Agent) güncel sistem durumunu içeren referans skill. Şef "sistem ne durumda", "kendini sorgula", "neredeyiz" dediğinde yüklenir. v3.0: CRM pipeline, API key durumu, gelir metrikleri, aksiyon planı dahil.
---

## Sistem Durumu Referansı

Bu skill, Jeff'in sisteminin güncel dökümünü içerir. **Her önemli değişiklikten sonra güncellenmelidir.**

## Rapor Üretimi (v3.0 — 07.08.2026)

Kullanıcı "sistem raporu", "kapsamlı rapor", "durum raporu", "bana bir sistem özeti çıkar" dediğinde:

### JSON Formatında Kapsamlı Rapor (v3.0 — CRM + API + Jeff + Aksiyon Planı)

1. **Veri toplama (5 paralel batch):** Sistem+Docker+Jeff, AgencyOS CRM pipeline (MCP), Token+Audit, API Health+Email+Sequences, Detaylar (dosya yapısı, skill sayısı, IG pipeline)
2. **JSON yapısı (17 bölüm):** `meta` → `system` → `jeff_3_0` → `cron_jobs` → `crm_pipeline` → `apis_and_keys` → `ai_cost` → `instagram_pipeline` → `agency_identity` → `gelir_durumu` → `kritik_sorunlar_oncelik_sirali` → `aksiyon_plani`
3. **Validasyon:** `python3 -m json.tool` ile geçerliliği doğrula
4. **Teslim:** Dosyayı `/opt/hermes/reports/sistem-raporu-YYYY-MM-DD.json` olarak kaydet, `/home/hermes/` yoluna kopyala, **MEDIA:** ile Telegram'a gönder
5. **Özet:** Kritik bulguları konuşma içinde markdown tablo olarak da paylaş

**Yeni (v3.0):** CRM pipeline, API key durumu, gelir metrikleri, AgencyOS kimlik uyumsuzluğu, aksiyon planı otomatik üretilir.

**Kullanıcı "sistem kodları dahil" derse:** Jeff 3.0 dosya yapısı, IG pipeline dosyaları, skill listesi, n8n workflow'ları zorunlu olarak eklenir.

Detaylı metodoloji ve JSON şeması için: `references/system-report-methodology.md`

## Kullanım

Şef şu soruları sorduğunda bu skill'i yükle:
- "Sistem ne durumda?"
- "Kendini sorgula"
- "Şuan nasıl bir yapıdasın?"
- "Neredeyiz?"
- "Özet geç"
- "Sağlık kontrolü"

## Aktif Model & Provider Durumu (01.08.2026)

- **Aktif provider:** opencode-go (ücretsiz DeepSeek) — birincil
- **Fallback provider:** DeepSeek API (paid) — sadece opencode-go offline olunca
- **Model:** deepseek-v4-flash
- **GLM-5.2 (HuggingFace):** ❌ Kaldırıldı
- **Vision:** deepseek-v4-flash ile `vision_analyze` çalışıyor
- **Gemini API:** ❌ Key Generative Language API'ye erişmiyor
- **Groq API:** ❌ Tüm key'ler geçersiz
- **Token maliyeti:** $0/gün (opencode-go ücretsiz)
- **Bakiye:** DeepSeek API balance bilinmiyor, opencode-go kullanıldığı için önemsiz

## Python Sürüm Durumu (04.08.2026)

- **Hermes binary:** Python 3.12 (`/usr/bin/python3.12`, shebang: `#!/usr/bin/python3.12`)
- **Install dir:** `/home/hermes/.local/lib/python3.12/site-packages`
- **Sistem apt:** Python 3.10 (Ubuntu 22.04, dokunulmaz)
- **`hermes update`:** ❌ KULLANMA. Sistem Python 3.10.12'ye bakıp `Python>=3.11` hatası veriyor, `uv` bağımlılık çözümlemesi başarısız. Doğru komut: `python3.12 -m pip install --upgrade hermes-agent`
- **uv:** ❌ Silindi

### Hermes Güncelleme Prosedürü

```bash
# DOĞRU:
python3.12 -m pip install --upgrade hermes-agent

# YANLIŞ (Python 3.10/3.12 çakışması):
hermes update  # ❌ "No solution found when resolving dependencies"
```

**PyPI Gecikme Tuzağı:** Duyuru tweet'leri paket yayınlanmadan atılabilir. v0.20.0 3 Ağustos'ta @IBuzovskyi tarafından duyuruldu, 4 Ağustos'ta PyPI'da hâlâ 0.19.0. `python3.12 -m pip index versions hermes-agent` ile kontrol et, yoksa bekle. GitHub releases (`https://github.com/NousResearch/hermes-agent/releases`) PyPI'dan önce güncellenebilir.

|Gateway RAM: ~2.4 GB (MemoryMax=5G)

## HQ API Durumu (01.08.2026)

- **status:** degraded ⚠️ (embedding daemon kapalı olduğu için — normal, port 8767 kalıcı kaldırıldı)
- **/api/status:** degraded dönüyor (hermes-embedding-daemon: false)
- **/api/v2/status:** çalışıyor
- **Port:** 8889
- **Bilinen sorunlar:** "Degraded" embedding daemon yokluğundan — gerçek sorun değil

## Açık Port Haritası (01.08.2026)

| Port | Servis | Durum |
|------|--------|:-----:|
| 22 | SSH | ✅ |
| 80/443 | Traefik (Coolify proxy) | ✅ |
| 3000 | Next.js (build container) | ✅ |
| 5432 | PostgreSQL (Coolify) | ✅ |
| 5678 | n8n (Docker) | ✅ |
| 6001-6002 | Coolify Realtime | ✅ |
| 6379 | Redis (Coolify) | ✅ |
| 8000 | Coolify (Docker) | ✅ |
| 8090 | Beszel (Docker) | ✅ |
| 8642 | Hermes Gateway API | ✅ |
| 8765 | Hermes Webhook | ✅ |
| 8766 | ~~AgentMemory MCP~~ | ❌ KAPALI (01.08) |
| 8768 | Token Muhasebe | ✅ |
| 8770 | Token Worker | ✅ |
| 8773 | HF-API | ⚠️ Port dinliyor ama yanıt yok |
| 8774 | **Task Intake API** | ✅ Faz 2 — onay paneli |
| 8877 | Browser Worker | ✅ |
| 8889 | HQ (Kanban) | ✅ degraded |
| 8892 | Dograh AI | ✅ |
| 9000-9001 | MinIO (Docker) | ✅ |
| 11235 | Crawl4AI (Docker) | ✅ |
| 34524 | Tailscale | ✅ |
| 49134 | AgentMemory (iii) | ✅ (8766 kapalıyken bu çalışır) |
| 50051 | Coolify gRPC | ✅ |

## Test Durumu (26.06.2026)

- **ToolPolicy tests:** 4/4 passed ✅
- **Total test suite:** ~1500 dosya (upstream Hermes + custom)
- **--collect-only timeout:** Normal — 1500+ dosya 30sn'de toplanamaz
- **Bilinen kırık test:** Yok (test_tool_policy.py tamamen düzeldi)
Terminal segfault: Çözüldü — **2 bağımsız kök sebep var**, aynı semptomu verir. Alttaki "Terminal + Filesystem İkili Çökmesi" bölümünde detay var.

**Arkaplan (16.06.2026) — 2 farklı sebep, aynı semptom:**

**Sebep 1 — Python 3.12 migration (eski):**
1. `hermes update` çalıştı → uv Python 3.12.13 kurdu → venv yenilendi
2. Modüller 3.11 dist-packages'inde kaldı → ModuleNotFoundError
3. Shebang 3.11'e çekilince binary yoktu → bad interpreter
4. Shebang 3.10'a çekilince pydantic ABI uyuşmazlığı → segfault
5. İkincil: venv yenilenirken config.yaml/.env root ownership'a döndü → gateway crash loop
6. **Fix:** `apt install python3.11` + get-pip + hardening script + permission fix

**Sebep 2 — --replace + drop_pending_updates crash loop (16.06 — Kullanıcı düzeltmesi):**
1. `systemctl start` ile `--replace` flag'i yeni process eskiye SIGTERM gönderir
2. Eski process exit code 1 → systemd Restart=always tetiklenir
3. Yeni process Telegram polling'inde "409 Conflict: terminated by other getUpdates request" alır
4. `drop_pending_updates=True` → restart anındaki mesajlar SİLİNİR
5. Tekrar SIGTERM → sonsuz loop
6. **Fix:** systemd service'den `--replace` kaldırıldı + Telegram kodunda `drop_pending_updates=True` → `False` (2 yerde — webhook + polling başlatma)

**Kalıcı önlemler:**
- `hermes-hardening.service` — boot'ta Python shebang + permission kontrolü
- `gateway-child-sentinel.sh` — 5dk'da bir permission ve child process temizliği
- Config: `persistent_shell: false`, `backend: local`

## Güncelleme Kuralı

Bu skill'deki `references/sistem-dokumu.md` dosyası, aşağıdaki durumlarda güncellenmelidir:

1. Yeni bir MCP server kurulduğunda
2. Skill ekleme/çıkarma olduğunda
3. Provider değiştiğinde
4. Cron job eklenip/silinince
5. Sistem mesaj politikasi degistiginde (kronlarin Bilal'e gidip gitmeme karari)
6. Yeni bir entegrasyon (Google, Canva, vb.) kurulduğunda
7. **Her önemli sistem onarımı veya servis değişikliğinde**
8. **MASTER_INDEX.md güncellendiğinde** (ayrıca bu skill'deki ilgili bölümü de güncelle)

## System Check Prosedürü (Aktif)

"System check" istendiğinde veya kendiliğinden sağlık taraması yaparken:

### 1. Temel Metrikler
- Disk, RAM, CPU, uptime, load average
- Swap kullanımı
- Zombie process sayısı

### 2. Kritik Servis Doğrulama (EN ONEMLI)
- **DeepSeek Bakiye:** Balance API sorgula → $2 alti kritik, $5 alti uyari
- **Token Watchdog Cron:** token-watchdog enabled + last_status ok olmali
- **Mem0/Qdrant:** Qdrant client yanit veriyor mu? Lock dosyasi var mi?
- **Hermes API:** 8642 portu acik, 200 donuyor mu?
- **AgentMemory:** 49134 portu acik mi? (8766 kapali — 49134 kullaniliyor)
- **Task Intake API:** 8774 portu acik mi? `curl -s http://localhost:8774/health` → "ok" dönmeli
- **Kanban HQ:** 8889 portu acik mi?
- **Jeff Web API:** 8892 portu acik mi?
- **Webhook:** 8765 portu acik mi?
- **Embedding Daemon:** Calisiyor mu, RAM'i normal mi?
- **n8n:** Docker container'i Up durumda mi?
- **OpenCode:** `/home/hermes/.hermes/node/bin/opencode --version` (standart `which opencode` bulamaz — `opencode` npm global'de değil, PATH dışında)
- **Google OAuth (Calendar/Gmail/Drive):** `takvim_etkinlik_listele()` veya `gmail_oku()` ile test et. `deleted_client` hatasi = Google Cloud Console'dan OAuth client silinmis → yeni credentials.json gerek. `invalid_grant` = token.pickle refresh tokeni dogru degil → yeni auth akisi gerek. Bu hatalar sessizce olusur, Bilal fark etmez — system check'te tespit etmek kritik.
- **Denetim Hatırlatıcı Cron:** `cronjob(action="list")` ile "Denetim Hatırlatıcı" job'ini kontrol et (ID: c16a3add1f03). Her gun 06:00'da Bilal'e Telegram mesaji gonderir (no_agent: true). Script: `~/.hermes/scripts/probation_reminder.py` — hardcoded takvimle calisir, Google Calendar'a bagli degildir. Takvim degisikliklerinde script duzenlenmeli.

### 2.5 Cron Job Denetimi (HER SEFERINDE)
- cronjob(action="list") ile tum cron'lari tara
- last_status: error olanlari tespit et:
  - Agent iceriyorsa (prompt dolu) → hemen sil (token yakiyor!)
  - no_agent: true ise → script bozuk → sil veya duzelt
- Duplicate isimleri kontrol et
- Detayli prosedur: token-budget-guard skill'inde Cron Job Audit bolumu

### 3. Ic Denetim
- Kritik MCP'ler yanit veriyor mu?
- Yakin zamanda reset olmus mu?

### 4. Rapor Formati
- Her bileşen: ✅ / ⚠️ / ❌
- Sorun varsa → sessizce çöz → çözüldükten sonra ✅ olarak raporla
- "X düzeltildi, Y sorunu vardı" GİBİ ifadeler KULLANMA. Sadece çalışan hali göster.
- Sadece çözülemeyen sorunları Bilal'e bildir

**Kural:** Her system check'te en az bir derinlemesine servis doğrulaması yap. Yüzeysel bakıp "her şey iyi" deme.

### 5. Bilinen Tuzaklar

#### Qdrant Lock (Reset Sonrası)
Server resetlenince Qdrant'ın `.lock` dosyaları kalır. Mem0 başlamaz. Çözüm:
```bash
find /home/hermes/.mem0 -name ".lock" -delete
```
Her reset sonrası system check'te öncelikle kontrol et.

#### mem0ai Paket Kaybı
mem0ai `pip3.11 install mem0ai fastembed` ile kurulur. Eksikse import hatası alınır. Sistem reset'lerinden sonra her zaman doğrula.

#### Cron Script Path Resolution (16.06.2026)
Cron runner script base: `/home/hermes/.hermes/scripts/`. The `script` field in jobs.json appends directly to this base path. **The `workdir` field is NOT used for script resolution** — it only sets the working directory for the LLM prompt context.

When `script:` has a `scripts/` prefix (e.g. `scripts/sinir_tanima.py`), the resolved path becomes `/home/hermes/.hermes/scripts/scripts/sinir_tanima.py` (double `scripts/`). This causes "Script not found" errors even when the file exists in the workdir's `scripts/` subdirectory.

**Fix (symlink pattern):**
```bash
mkdir -p /home/hermes/.hermes/scripts/scripts
ln -sf /home/hermes/.hermes/skills/<skill>/scripts/<file>.py \
      /home/hermes/.hermes/scripts/scripts/<file>.py
```

**Affected (fixed 16.06):** Faz26-Otonom-Karar, Faz27-Proaktif-Deger, Faz29-Ogrenme-Dongusu, Faz30-Meta-Degerlendirme, Jeff-API-Watchdog.

#### Terminal + Filesystem İkili Çökmesi (Gateway Process Spawn)
**Semptom:** Tüm shell komutları `exit_code: -11` (SIGSEGV) ile çöker. Aynı anda filesystem MCP de yanıtsızdır — `read_file` var olan dosyalar için bile "File not found" döner, `write_file` başarısız olur.

**Teşhis:** İki bağımsız alt sistem (shell spawn, filesystem MCP spawn) aynı anda aynı şekilde çöküyorsa, ortak bağımlılıkları olan **gateway'in subprocess spawning mekanizması** bozulmuştur. Bu bir MCP veya shell sorunu değil, gateway-level process yönetim sorunudur.

**Kurtarma adımları (sırayla dene):**
1. Önce gateway restart: `pkill -9 -f "hermes gateway"` veya `sudo systemctl restart hermes-gateway` — 10sn içinde düzelir
2. Self-kill riskine dikkat et (gateway-maintenance.md'deki kural): restart'ı terminal'den yap, Telegram session'ından yapma
3. **Terminal de filesystem de çökmüşse** — kısır döngüdesin demektir. Kendi başına çıkamazsın. **Bilal'den SSH ile girmesini iste.** .bat dosyası (`hermes-baglan.bat`) Masaüstünde, çift tıkla bağlanır (SSH key tanımlı, şifresiz). Şu komutlar yeter:
   ```bash
   sudo sed -i 's/--replace//g' /etc/systemd/system/hermes-gateway.service
   TELEGRAM_PY=$(python3.11 -c "import gateway.platforms.telegram; print(gateway.platforms.telegram.__file__)")
   sudo sed -i 's/drop_pending_updates=True/drop_pending_updates=False/g' "$TELEGRAM_PY"
   sudo systemctl daemon-reload && sudo systemctl restart hermes-gateway
   ```
   Bunlar kalıcı fix'tir, bir daha aynı sorun olmaz.
4. Gece 04:00 önleyici restart varsa bekle — çoğu zaman kendiliğinden düzelir
5. Eğer nüksediyorsa: Python sürüm karışıklığı (geçmişte 3 farklı sürüm vardı) veya proces limit (ulimit -u) kontrol et

**⚠️ İKİNCİ KÖK SEBEP (16.06.2026 — Kullanıcı düzeltmesi):** Aynı semptomun ikinci ve bağımsız bir sebebi daha vardır: **`--replace + drop_pending_updates=True` crash loop'u.**

**Semptom:** Terminal her komutta segfault atar, aynı anda filesystem MCP ölür. Gateway crash loop'a girer.

**Mekanizma:**
1. `systemctl start hermes-gateway` ile `--replace` flag'i yeni process eskiye SIGTERM gönderir
2. Eski process exit code 1 → systemd Restart=always tetiklenir
3. Yeni process başlarken Telegram eski polling bağlantısını hâlâ açık tutar
4. Telegram API "409 Conflict: terminated by other getUpdates request" döner
5. `drop_pending_updates=True` → o anki mesajlar silinir
6. Tekrar SIGTERM → sonsuz loop

**Teşhis (hangisi olduğunu anlamak için):** İkisi de aynı semptomu verir.
- `systemctl status hermes-gateway` ile restart sayısını kontrol et
- `journalctl -u hermes-gateway --since "1 hour ago" | grep -c "Conflict\|SIGTERM"` — çok sayıda varsa 2. sebep
- `python3 --version` ile sürüm karışıklığı yoksa 2. sebep

**Kalıcı çözüm (16.06.2026 — 22.06.2026 güncellendi):**\n1. systemd service'den `--replace` kaldırıldı — systemd tek instance yönetir, crash loop biter. **Dikkat:** `hermes gateway service install --replace` bu flagi geri ekler.\n2. `drop_pending_updates=True` → `False` (Telegram platform kodunda 2 yerde: webhook ~satır 2181 + polling ~satır 2214) — restartta mesaj kaybı önlenir.\n3. Doğru path: `/home/hermes/.local/lib/python3.11/site-packages/gateway/platforms/telegram.py` (`import gateway.platforms.telegram` ile bulunur, `hermes.gateway.platforms.telegram` değil.)

**Kontrol sırası:** Nüksedince önce Python sürümünü, sonra systemd config'de --replace + drop_pending_updates durumunu kontrol et.

#### Python Script — `logs[-50]` IndexError Pattern
`log()` fonksiyonunda `logs = logs[-50]` yazılırsa (eksik colon: dilimleme değil index) list boşken `IndexError: list index out of range` patlar. **Doğrusu:** `logs = logs[-50:]` (slice). Bu hata script'in ortasında crash'e yol açar, hata mesajı kafa karıştırıcı olabilir. Yeni bir cron script'i yazarken veya mevcutunda `log()` pattern'i görürsen kontrol et.

#### HF-API Zombie Process (01.08.2026)
**Semptom:** Port 8773 `ss -tlnp` çıktısında LISTEN görünür ama `nc -z localhost 8773` ❌ ve `curl localhost:8773/health` ❌ döner.

**Kök sebep:** `/opt/hermes/scripts/hf_tools/hf_api_server.py` birden fazla PID ile çalışıyor. Eski PID (örn. 1470153, 26 Haziran'dan kalma) sleeping durumda kalır, yeni PID (örn. 252473) portu dinler ama HTTP yanıt vermez. İki process çakışır.

**Fix:**
```bash
# Tüm eski HF process'lerini temizle
pkill -f hf_api_server.py
sleep 1
# Taze başlat (background)
cd /opt/hermes/scripts/hf_tools && python3 hf_api_server.py &
sleep 2
nc -z localhost 8773 && echo "8773 OK"
```
Process'lerin temizlendiğini doğrula: `pgrep -f hf_api_server` → tek PID dönmeli.

**Ne zaman kontrol edilir:** System check'te port 8773 ❌ ise önce bu pitfall'ı kontrol et.

#### caddy.service Mask (01.08.2026)
caddy.service failed durumundaydı. Coolify zaten kendi Traefik proxy'sini kullandığı için caddy'ye gerek yok. Maskelendi:
```bash
sudo systemctl mask caddy.service
```
System check'te `systemctl --failed` çıktısında caddy görürsen mask'la, restart etme.

## Ek Metodoloji & Referans

- `references/sistem-dokumu.md` — Tam sistem dökümü (config, skill'ler, MCP'ler, cron'lar, memory). **01.08.2026'da güncellendi.**
- `references/gateway-maintenance.md` — Gateway graceful restart, cron bakımı, disk temizliği operasyonları
- `references/memory-management.md` — Memory limit yükseltme, temizlik patterni, skill'e taşıma prensipleri
- `references/denetimli-serbestlik-takvimi.md` — Bilal'in denetimli serbestlik görüşme takvimi
- `references/dijital-ayak-izi-temizleme.md` — **Dijital ayak izi tarama ve temizleme (02.08.2026):** site durdurma, WHOIS kontrolü, Google cache taraması, PII temizliği. Şantaj/tehdit durumunda 5 adımlı prosedür.
- `references/once-mimari-pipeline.md` — Architecture First geliştirme pipeline'ı (9 adım)
- `/home/hermes/hermes-system-blueprint-2026-08-01.md` — **Tam sistem blueprint'i (01.08.2026)**. 13 bölüm: donanım, mimari, provider, skill kataloğu, MCP, cron, Docker, port haritası, Jeff 2.0, dosya yapısı, pitfall'lar, roadmap. Harici analiz (ChatGPT) için optimize edildi.
- `~/.hermes/optimization/` — **Optimizasyon kontrol düzlemi (01.08.2026)**. Inventory, health_check.py, task_guard.py, policy, runbook'lar. `python3 ~/.hermes/optimization/scripts/health_check.py` ile anlık sağlık taraması.

## Referans Dosyaları (02.08.2026 güncel)

- `references/sistem-dokumu.md` — Tam sistem dökümü (config, skill, cron, port, provider, Docker — 01.08.2026)
- `references/task-intake-control-plane.md` — Task Intake API v2 + Optimization Control Plane (Faz 1-3)
- `references/gateway-maintenance.md` — Gateway graceful restart, cron bakımı, disk temizliği
- `references/memory-management.md` — Memory limit yükseltme, temizlik patterni
- `references/dijital-ayak-izi-temizleme.md` — Dijital ayak izi tarama ve temizleme (site durdurma, WHOIS, Google cache, PII taraması)
- `references/denetimli-serbestlik-takvimi.md` — Bilal'in denetimli serbestlik görüşme takvimi
- `references/system-report-methodology.md` — JSON formatında kapsamlı sistem raporu metodolojisi
- `references/once-mimari-pipeline.md` — Architecture First geliştirme pipeline'ı (9 adım)
- `/home/hermes/hermes-system-blueprint-2026-08-01.md` — Tam sistem blueprint'i (ChatGPT analizi için)

## MASTER_INDEX & Wiki Sistemi

Sistemin tam haritası `~/.hermes/MASTER_INDEX.md`'dedir. 148 satırlık tek dosya:
- Hiyerarşi, config, 10 işçi, 52 skill, 17 cron, projeler, bağımlılıklar, iletişim kuralları

Context compaction sonrası MASTER_INDEX.md'yi oku, her şey net olur.

Wiki'ler `~/.hermes/wikis/` altında kategorilere ayrılmıştır:
- `tool/`, `provider/`, `workflow/`, `insight/`, `architecture/`
- Yeni keşifler `scripts/wiki.py` ile kaydedilir
- Memory sadece özet referans tutar, detay wiki'de

## Yeni Araçlar (17.06.2026)

| Araç | Versiyon | Ne İşe Yarar |
|------|---------|-------------|
| **scrapling** | v0.4.8 | Anti-bot adaptif web scraping — Lead Stratejisti için |
| **markitdown** | v0.1.6 | PDF/DOCX/PPT → Markdown — İçerik Fabrikası için |
| **supermemory** SDK | v3.46.0 | Cloud memory API client (self-host gerekli, şu an pasif) |
| **webwright** | v0.1.0 | LLM kontrollü Playwright agent (OpenAI key gerek, test edilmedi) |

Kurulu: `pip install` ile Python 3.11 site-packages'ine. `python3.11` ile import edilir.

## Cron Frekans Optimizasyonu (17.06.2026)

| Cron | Önce | Sonra | Gerekçe |
|------|------|-------|---------|
| token-watchdog | 15 dk | **30 dk** | Bakiye 15 dk'da değişmez |
| jeff-watchdog | 5 dk | **15 dk** | RAM/Disk 5 dk'da değişmez |
| jeff-guardian (Gemini) | 1 saat | **6 saat** | Gemini token tüketimi azaltıldı |
| chat-mesaj-watchdog | — | **5 dk** | ergeneai.com chat asistanına gelen mesajları Telegram'a bildirir. Script: chat_watchdog.py (no_agent). Log: ~/.hermes/chat_messages.jsonl |
