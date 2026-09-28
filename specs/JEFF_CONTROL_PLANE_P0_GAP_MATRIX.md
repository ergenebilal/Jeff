# JEFF_CONTROL_PLANE v1.0 — mevcut durum ve P0 eksik matrisi

Karşılaştırma tabanı: `37ddabfe9` ve kullanıcı tarafından sağlanan JSON. Aktif Bridge `jeff2/bridge/`, Pablo `pablo/`, operasyon betikleri `scripts/` altındadır. Bu dal yalnız P0 kodunu değiştirir; dağıtım veya `main` birleştirmesi yapmaz.

| Alan | Depoda görülen kanıt | Durum ve bu daldaki işlem |
| --- | --- | --- |
| P0 — Bridge secret / bind | `jeff_bridge_api.py`: startup'ta `BRIDGE_KEY` kontrolü, varsayılan `127.0.0.1`, IP allowlist | Mevcut testlerle kapsanıyor. Public bind ayrıca yapılandırılmalı. |
| P0 — Kalıcı idempotency | `alfred_task_claims`, SHA-256 digest, atomik SQLite claim, `409` testleri | Mevcut. Legacy kayıtlar korunur ve doğrulanmış başarı sayılmaz. |
| P0 — Tek TaskGuard yolu | `alfred_client.py` yalnız heartbeat; Bridge görevleri `execute_request` üzerinden TaskGuard'a gider | Pablo'nun doğrudan Telegram döngüsü artık `main()` tarafından başlatılmaz. Doğrudan HTTP `/execute` yan etkili eylemleri TaskGuard'a ulaşmadan `403 BLOCKED` ile kapatır. Salt-okunur liste `ping`, `window_list`, `gui_coords`, `pilot_status` ile sınırlıdır; tıklayabilen `vision_grounding`, dosya yazabilen `screenshot` ve serbest URL açabilen `browser_read` Bridge üzerinde de onay gerektirir. |
| P0 — Onay | `pablo_task_guard.py`: digest, owner, süre ve tek tüketim | Bridge görevleri için kalıcı `alfred_approvals` kaydı ve Jeff/Pablo karar devri eklendi. Ayrı Jeff onay tüketicisi bildirimi atomik olarak bir kez sahiplenip Telegram callback'ini Bridge'e aktarır. Belirsiz Telegram gönderiminden sonra kör tekrar yapılmaz; manuel reconciliation gerekir. Tüketici henüz canlıya alınmadı. |
| P0 — Sonuç bağlama | Digest, worker ID, attempt ve karantina vardı; fakat kuyruk/sonuç/heartbeat yalnız genel Bridge anahtarını kabul ediyordu | Ayrı `TASK_WORKER_KEY` ve yapılandırılmış `PABLO_WORKER_ID` zorunlu. Sonuç gövdesindeki worker ID de bu kimlikle eşleşir. |
| P1 — Task contract / ledger | `task_contract.py`: durum makinesi, event ledger, claim ve verifier | Kısmen mevcut. JSON'daki `tenant_id` ve `autonomy_level` oluşturma sözleşmesinde görünmüyor. P1 kodu değiştirilmedi. |
| P1 — Kanıt ve doğrulama | `task_contract.py` ve HTTP/SQLite smoke testleri yürütme/sonuç kanıtını ayırıyor | Salt-okunur örnek doğrulanıyor; bütün yan etkili sınıflar için bağımsız sonuç doğrulaması bu dalda kanıtlanmadı. |
| P2 — Brifing ve radar | `executive_briefing.py` yapılandırılmış DB sorguları ve veri yoksa `UNKNOWN`; `proactive_lead_radar.py` kaynaklı adayları işler | Temel akış var. JSON'daki tüm job telemetrisi, dead-man switch, maliyet defteri ve sağlayıcı sağlığı gösterilmedi. P2 kodu değiştirilmedi. |
| P3 — Ajans ve tenant ayrımı | Aktif Bridge/Pablo betiklerinde `tenant_id` araması sonuç vermedi | Tam müşteri yaşam döngüsü ve tenant ayrımı gösterilmedi. P3 kodu değiştirilmedi. |
| Bellek / veri / model yönlendirme | Aktif ledger var; arşivde bellek belgeleri var | Obsidian export, hassas veri için onaylı rota ve bütçe/circuit-breaker kuralları bu incelemede doğrulanmadı. |
| CI / yayın | `.github/workflows/active-contract-gates.yml` PR ve dal testleri çalıştırıyor | GitHub branch protection ve insan yayın onayı repo içinden doğrulanamaz. Bu dal `main`e gönderilmeyecek. |

## P0 yapılandırması

Bridge ortamında `BRIDGE_KEY`, ondan farklı bir `TASK_WORKER_KEY`, her ikisinden farklı bir `JEFF_APPROVAL_KEY`, Pablo'nun `node_id` değeriyle aynı `PABLO_WORKER_ID` ve onay sahibinin kimliği olan `APPROVAL_OWNER_ID` gerekir. Pablo'nun yerel yapılandırmasında `auth_token` Bridge anahtarı, `task_worker_key` worker anahtarı olmalıdır; worker anahtarı `TASK_WORKER_KEY` ortam değişkeninden de alınabilir. `JEFF_APPROVAL_KEY` yalnız Jeff onay tüketicisinde bulunmalı, Pablo'ya verilmemelidir. Yeni `jeff-approval-bot.service` ayrıca `/etc/jeff-approval-bot.env` içinden bu anahtarları, `APPROVAL_OWNER_ID` değerini ve yalnız kendisinin kullandığı `JEFF_APPROVAL_BOT_TOKEN` değerini bekler. Aynı Telegram tokenını başka poller kullanırsa hizmetler çakışır; yayından önce tek polling sahibi doğrulanmalıdır. Secret'ları kaynak dosyaya yazmayın. Eksik veya aynı anahtarlar ilgili uçları kapalı tutar; Pablo'nun Bridge döngüsü yerel anahtarlar eksikse başlamaz.

## Doğrulama ve yayın sınırı

`python scripts/run_active_tests.py --group bridge`, `--group contract`, `python scripts/compile_active.py`, `python scripts/lint_active.py`, `python scripts/ci_secret_scan.py` çalıştırılır. HTTP/SQLite smoke testi yalnız `127.0.0.1`, geçici DB ve sahte TaskGuard eylemi kullanır; yetkisiz isteğin görev claim'i veya sonuç kaydı oluşturmadığını kontrol eder. Yayından önce staging'de yeni worker kimlik bilgileriyle tam handshake doğrulanmalıdır. Bu değişiklik üretim servisine gönderilmedi.

Yerel staging handshake'i, Pablo'nun gerçek `pablo_bridge_auth.py` modülünden başlıkları üretip geçici Bridge HTTP sunucusuna gönderir. Genel anahtarla polling/heartbeat `401`, yanlış worker kimliği `403` döner. Doğru kimlikle heartbeat sağlık kontrolünde `alfred_online=true` olur; görev bir kez claim edilir, sahte TaskGuard eylemi bir kez çalışır, sonuç bir kez kaydedilir ve duplicate karantinaya alınır. Onay devrinde yalnız Jeff anahtarıyla kart okunur ve sahiplenilir; owner eşleşmezse `403`, digest değişirse ve karar tekrar edilirse `409` döner. Pablo kararı TaskGuard üzerinden uygular. Bu kanıt canlı sunucu handshake'inin yerine geçmez.

Smoke testinde gerçek `JeffApprovalBot` modülü geçici localhost Bridge'e bağlanır; Telegram taşıması sahte fonksiyonla değiştirilir. Kart bir kez hazırlanır, callback iki kez verildiğinde Bridge kararı bir kez kaydeder ve TaskGuard eylemi bir kez çalıştırır. Hiçbir gerçek Telegram mesajı veya Windows eylemi yürütülmez.

Pablo, `APPROVAL_REQUIRED` sonucu için Bridge'den `handoff=stored` yanıtı almadan yerel sonuç outbox kaydını silmez. Eski Bridge sürümü böyle bir yanıt vermez; worker sonucu saklar ve onay devri kurulana kadar görevi yürütmez. Bridge ve Pablo sürümleri birlikte doğrulanmalıdır.

Yayın engeli: Pablo'nun doğrudan Telegram döngüsü kodda kalsa da başlangıçtan çıkarıldı. Jeff onay tüketicisi depo içinde hazırdır: sahibin kimliğini Telegram callback'inde denetler, Bridge'e digest/approval ID ile tek kullanımlık karar gönderir; okunamayacak kadar uzun kartları sahiplenmez. Doğrudan `/execute` yan etkili eylemleri gerçek localhost HTTP testiyle `403 BLOCKED` olarak doğrulandı. Ancak Jeff onay servisi canlıda yoktur ve gerçek Telegram callback'i doğrulanmadı; kullanıcıya bildirim gittiği iddia edilemez. Jeff onay tüketicisinin geçerli, ayrı tokenla tek poller olduğu ve gerçek callback staging'de doğrulanmadan yayın yapılamaz.

2026-09-28 staging kontrolü: Sunucudaki Jeff onay botu pasif ve kendisine atanmış env dosyası yok; sunucuda bulunan diğer Telegram tokenı Bot API `getMe` çağrısında `401` döndürdü. Yerel geçerli token, çalışan Pablo sürecinin Telegram tüketicisiyle aynı yapılandırmada. Bu nedenle ikinci bir `getUpdates` tüketicisi başlatılmadı; gerçek Telegram callback'i ve uçtan uca onay devri doğrulanamadı.

Yeni sunucudaki salt-okunur inceleme (2026-09-28 17:18 UTC): `/home/hermes/jeff2`, `/home/hermes/jeff_repo/jeff2` dizinine işaret eder. `jeff-bridge.service` aktiftir; `/home/hermes/jeff_repo` temiz `main` dalında `50e63c837` commit'indedir. Bridge yalnız `127.0.0.1:7700/health` üzerinden HTTP 200 verdi. `:9119`, `:8999`, `:8774` ve `:18791` localhost sağlık sorguları bağlantı kuramadı. `telegram-claude-bot.service` ve `antigravity-telegram-bot.service` pasiftir; unit dosyaları bu sunucuda bulunamadı. `/opt/hermes/telegram_claude_bot.py` dosyası vardır, ancak çalışan Telegram botu gözlenmedi. Bu gözlem, kullanıcı tarafından verilen aktif servis listesiyle uyuşmaz; servisler yeniden kontrol edilmeden yayın varsayımı yapılmamalıdır.

Sunucudaki Jeff botu dosyasının `request_human_approval` akışı kendi görev durumunu değiştirir; Pablo TaskGuard onay kimliğini tüketen callback bulunmadı. Sunucudaki Bridge dosyasında `TASK_WORKER_KEY` kullanımı görünür, fakat bu daldaki `PABLO_WORKER_ID` bağlaması görünmez. İnceleme dalı canlıya alınmadan önce Jeff botu için tek Telegram polling sahibi, TaskGuard onay callback'i ve çalışan servis yolu kurulup ayrıca doğrulanmalıdır.

Eski `jeff2/bridge/contract_tests/` ağacı ayrıca üretim dosyalarının kopyalarını barındırır. Bu daldaki gerçek HTTP/SQLite güvenlik smoke testi aktif `pablo/pablo_bridge_auth.py` ve `pablo/pablo_approval_handoff.py` modüllerini kullanır; eski kopyaların geçmesi canlı Pablo sürümünün doğru olduğunu tek başına kanıtlamaz.

## Geri alma

Dalın P0 commit'leri ters sırada `git revert` ile geri alınabilir. Eklenen `approval_notified` SQLite sütunu ve `alfred_approvals` tablosu geride kalabilir; eski kod bunları yok sayar ve mevcut kayıtlar korunur. Önce eski worker sürümü geri yüklenmeli, ardından yalnız bu değişiklik için eklenen worker ve Jeff onay kimlik ayarları kaldırılmalıdır.
