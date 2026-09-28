# JEFF_CONTROL_PLANE v1.0 — mevcut durum ve P0 eksik matrisi

Karşılaştırma tabanı: `37ddabfe9` ve kullanıcı tarafından sağlanan JSON. Aktif Bridge `jeff2/bridge/`, Pablo `pablo/`, operasyon betikleri `scripts/` altındadır. Bu dal yalnız P0 kodunu değiştirir; dağıtım veya `main` birleştirmesi yapmaz.

| Alan | Depoda görülen kanıt | Durum ve bu daldaki işlem |
| --- | --- | --- |
| P0 — Bridge secret / bind | `jeff_bridge_api.py`: startup'ta `BRIDGE_KEY` kontrolü, varsayılan `127.0.0.1`, IP allowlist | Mevcut testlerle kapsanıyor. Public bind ayrıca yapılandırılmalı. |
| P0 — Kalıcı idempotency | `alfred_task_claims`, SHA-256 digest, atomik SQLite claim, `409` testleri | Mevcut. Legacy kayıtlar korunur ve doğrulanmış başarı sayılmaz. |
| P0 — Tek TaskGuard yolu | `alfred_client.py` yalnız heartbeat; `hermes_node.py` görevleri `execute_request` üzerinden TaskGuard'a yollar | Windows/browser görevleri için mevcut. Pablo'nun doğrudan Telegram mesajları, JSON'daki tek dış konuşmacı kuralına hâlâ aykırı; ayrı mimari değişiklik gerekir. |
| P0 — Onay | `pablo_task_guard.py`: digest, owner, süre ve tek tüketim | Tekrarlanan isteğin onay bildirimini tekrar göndermemesi için atomik `approval_notified` claim'i eklendi. Gönderim başarısızsa kör tekrar yapılmaz; manuel reconciliation gerekir. |
| P0 — Sonuç bağlama | Digest, worker ID, attempt ve karantina vardı; fakat kuyruk/sonuç/heartbeat yalnız genel Bridge anahtarını kabul ediyordu | Ayrı `TASK_WORKER_KEY` ve yapılandırılmış `PABLO_WORKER_ID` zorunlu. Sonuç gövdesindeki worker ID de bu kimlikle eşleşir. |
| P1 — Task contract / ledger | `task_contract.py`: durum makinesi, event ledger, claim ve verifier | Kısmen mevcut. JSON'daki `tenant_id` ve `autonomy_level` oluşturma sözleşmesinde görünmüyor. P1 kodu değiştirilmedi. |
| P1 — Kanıt ve doğrulama | `task_contract.py` ve HTTP/SQLite smoke testleri yürütme/sonuç kanıtını ayırıyor | Salt-okunur örnek doğrulanıyor; bütün yan etkili sınıflar için bağımsız sonuç doğrulaması bu dalda kanıtlanmadı. |
| P2 — Brifing ve radar | `executive_briefing.py` yapılandırılmış DB sorguları ve veri yoksa `UNKNOWN`; `proactive_lead_radar.py` kaynaklı adayları işler | Temel akış var. JSON'daki tüm job telemetrisi, dead-man switch, maliyet defteri ve sağlayıcı sağlığı gösterilmedi. P2 kodu değiştirilmedi. |
| P3 — Ajans ve tenant ayrımı | Aktif Bridge/Pablo betiklerinde `tenant_id` araması sonuç vermedi | Tam müşteri yaşam döngüsü ve tenant ayrımı gösterilmedi. P3 kodu değiştirilmedi. |
| Bellek / veri / model yönlendirme | Aktif ledger var; arşivde bellek belgeleri var | Obsidian export, hassas veri için onaylı rota ve bütçe/circuit-breaker kuralları bu incelemede doğrulanmadı. |
| CI / yayın | `.github/workflows/active-contract-gates.yml` PR ve dal testleri çalıştırıyor | GitHub branch protection ve insan yayın onayı repo içinden doğrulanamaz. Bu dal `main`e gönderilmeyecek. |

## P0 yapılandırması

Bridge ortamında `BRIDGE_KEY`, ondan farklı bir `TASK_WORKER_KEY` ve Pablo'nun `node_id` değeriyle aynı `PABLO_WORKER_ID` gerekir. Pablo'nun yerel yapılandırmasında `auth_token` Bridge anahtarı, `task_worker_key` worker anahtarı olmalıdır; worker anahtarı `TASK_WORKER_KEY` ortam değişkeninden de alınabilir. Secret'ları kaynak dosyaya yazmayın. Eksik veya aynı anahtarlar worker uçlarını kapalı tutar; Pablo'nun Bridge döngüsü yerel anahtarlar eksikse başlamaz.

## Doğrulama ve yayın sınırı

`python scripts/run_active_tests.py --group bridge`, `--group contract`, `python scripts/compile_active.py`, `python scripts/lint_active.py`, `python scripts/ci_secret_scan.py` çalıştırılır. HTTP/SQLite smoke testi yalnız `127.0.0.1`, geçici DB ve sahte TaskGuard eylemi kullanır; yetkisiz isteğin görev claim'i veya sonuç kaydı oluşturmadığını kontrol eder. Yayından önce staging'de yeni worker kimlik bilgileriyle tam handshake doğrulanmalıdır. Bu değişiklik üretim servisine gönderilmedi.

Yerel staging handshake'i, Pablo'nun gerçek `pablo_bridge_auth.py` modülünden başlıkları üretip geçici Bridge HTTP sunucusuna gönderir. Genel anahtarla polling/heartbeat `401`, yanlış worker kimliği `403` döner. Doğru kimlikle heartbeat sağlık kontrolünde `alfred_online=true` olur; görev bir kez claim edilir, sahte TaskGuard eylemi bir kez çalışır, sonuç bir kez kaydedilir ve duplicate karantinaya alınır. Bu kanıt canlı sunucu handshake'inin yerine geçmez.

Yayın engeli: Pablo'nun doğrudan Telegram botu hem onay düğmelerini işler hem insana mesaj gönderir. Bu, JSON'daki "Pablo hiçbir insana doğrudan mesaj göndermez" sahiplik kuralını henüz sağlamaz. Etkin Jeff onay tüketicisi doğrulanmadan bu yol kaldırılırsa onaylar işlenemez. Jeff tarafındaki sahip ve callback sözleşmesi belirlenip ayrı testle doğrulanmalıdır.

Depodaki eski dağıtım kayıtları `telegram-claude-bot.service` ve `/opt/hermes/telegram_claude_bot.py` dosyasını aday gösterir. Söz konusu botun repo kopyasındaki `request_human_approval` akışı kendi görev durumunu değiştirir; Pablo TaskGuard onay kimliğini tüketmez. Ayrıca kayıtların Bridge yolu `/home/hermes/jeff2/bridge/` iken güncel sunucu bilgisi aktif repoyu `/home/hermes/jeff_repo` olarak tanımlar. Bu kayıtlar yeni sunucunun canlı botunu kanıtlamaz. `hermes@13.140.183.88` için salt-okunur SSH denemesi kimlik doğrulamada reddedildiğinden çalışan servis ve kod yolu doğrulanamadı. İnceleme dalı canlıya alınmadan önce sunucuda çalışan Jeff botu, TaskGuard onay callback'i ve tek Telegram polling sahibi salt-okunur biçimde tespit edilmelidir.

Eski `jeff2/bridge/contract_tests/` ağacı ayrıca üretim dosyalarının kopyalarını barındırır. Bu daldaki gerçek HTTP/SQLite güvenlik smoke testi aktif `pablo/pablo_bridge_auth.py` modülünü kullanır; eski kopyaların geçmesi canlı Pablo sürümünün doğru olduğunu tek başına kanıtlamaz.

## Geri alma

Dalın P0 commit'i `git revert <p0-commit>` ile geri alınabilir. Eklenen `approval_notified` SQLite sütunu geride kalabilir; eski kod sütunu yok sayar ve mevcut kayıtlar korunur. Önce eski worker sürümü geri yüklenmeli, ardından yalnız bu değişiklik için eklenen worker kimlik ayarları kaldırılmalıdır.
