# Altyapı Tuzakları ve Doğru Usuller (hafızadan taşındı 15.09.2026)

## Coolify
- Sunucuda bir şey bozulduğunda **önce Coolify DB'sini kontrol et**: `docker exec coolify-db psql -U coolify -d coolify`. Çoğu servis Coolify üzerinden deploy edilmiş olabilir; sıfırdan build etmek yerine mevcut konteyner/config'i restart etmek yeterli olabilir.
- **COOLIFY .env DOSYASINA ELLE MÜDAHALE ETME.** Encrypted cast "MAC is invalid" hatası verir, DB çöpe gider. Bu hata bir kez yapıldı, OpenCode düzeltti.

## Zamanlanmış görevler
- Cron `script` alanı **yol** bekler; içine kod gövdesi yazılırsa her koşuda "Script not found" ile düşer. 14.09'da `morning-briefing` ve `nightly-consolidation` bu yüzden bozuktu.
- Script tabanı: `~/.hermes/scripts/`. Kaynak dosyalar `~/scripts/` altında da tutulur; iki kopya eşitlenmezse iş "Script not found" verir (iki dizinde de dosya + `chmod +x` gerekir).
- Görev canlılığı `last_run_at` tarihiyle kontrol edilir; beslemesi ölen bir görev sessizce yalan rapor üretir (14.09'da fırsat radarı 8 gündür ölüydü, günlük brifing "radar çalışıyor" diyordu).
- **Beslemesi ölmüş görev, uydurma kaynak cümlesi kurar:** brifing "tarama sonuçları geldi" yazarken `context_from` boş ve üretici görev listede yoksa çıktı uydurmadır (15.09: iki denetimde de aynı durum). Bir rapor "veri geldi" diyorsa **üretici beslemenin var olduğunu** ayrıca doğrula.

## NotebookLM
- Oturum **kalıcı tarayıcı + CDP** üzerinden alınır (profil: `~/.nlm-browser`, uzak hata ayıklama 127.0.0.1:18800).
- **Cookie enjeksiyonu oturumu iptal eder**; manuel cookie devri bitti.

## Google / yedekleme kimlikleri
- Google OAuth (19.08): Drive/Calendar/Docs/Sheets/Gmail gönderme + refresh çalışıyor; **eksik kapsam: gmail.readonly**.
- Bilal kişisel Google hesabı kullanıyor (Workspace değil) → Shared Drive yok; servis hesabı yalnız Shared Drive'a yazar, kişisel Drive'a OAuth token ile yedek alınır (SA JSON dosyasına dokunulmaz). Hedef klasör: Jeff-Backup (benzer adlı 4 klasör var).
- rclone kendi client_id'siyle çalışır; `gdrive:` uzak adı tanımlı. Her koşuda "bu kimlik 2026 içinde kapanacak" uyarısı basar ama yükleme başarılıdır (15.09: 222 MB, Drive'da doğrulandı) — uyarıyı hata sayma, yüklemeyi kanıtla.

## Heron / hermes CLI
- `hermes serve` = masaüstü uygulaması ve uzak istemcilerin bağlandığı JSON-RPC/WebSocket kapısı (varsayılan 9119). Loopback dışı bind her zaman kimlik doğrulama ister; `--insecure` artık no-op. 127.0.0.1'e bağlayıp tünellemek en doğrusu.
- ACP modu (`hermes acp`) yalnız **stdio** çalışır ve `agent-client-protocol==0.9.0` paketi kurulu değilse açılmaz (`pip install -e '.[acp]'`).
- Bilişsel katman canlı trafikte **gözlemci modda** çalışıyor: karar motoru HOLD, kurul REJECT → her stratejik tur "dry run" ile bitiyor (14.09 ve 15.09 ölçümü: 30/30; talimat metninin kendisi de "önemsiz" sınıflandı).
- `hermes update` 13.09'da ertelendi; yerel bilişsel çalışma `cognitive-core-yerel-20260913` dalında (commit 7e18a04240), yedek `/opt/backups/hermes-local/*.tgz`. Sıra: yedek → dal tazele → update → restart → test.

### Uzak istemci / masaüstü panel (Bilal talebi, 15.09 — seçim YAPILMADI)

Amaç: masaüstünde **tek panel**; yerel OpenClaw (Windows) ile sunucudaki ajanlar aynı arayüzde görünsün.

- **Doğal yol bizim tarafta hazır:** panel `hermes serve` (9119, auth'lu) kapısına bağlanır; uzaktan
  erişim Tailscale üzerinden. 0.0.0.0'a bind edip auth'u kapatmayı deneme (`--insecure` no-op).
- **Panel ACP konuşuyorsa köprü şart:** `hermes acp` stdio-only ve `agent-client-protocol` paketi
  kurulu değil → WebSocket'e çeviren köprü (ör. `coder/agentapi`) gerekir. Köprü kurmadan önce
  native `hermes serve` yolunu dene; gereksiz katman ekleme.
- Değerlendirilen aday: **AionUi** (Tauri masaüstü; uzak ajan protokolleri `openclaw|zeroclaw|acp`
  destekliyor). Kurulum testi YAPILMADI — VERIFIED değil; seçim Bilal'in.
- **Kural:** panel seçiminden önce sunucu tarafında bağlanabilirliği kanıtla (kapı açık mı, kimlik
  istiyor mu, uzak istemciden gerçekten cevap geliyor mu). Test edilmemiş panelle yola çıkma.
