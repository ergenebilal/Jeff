# Cron Job Hatası Teşhis Prosedürü

## Genel akış

1. `cronjob list` ile tüm job'ları listele — `last_status` ve `last_delivery_error` sütunlarına bak
2. Error olan job'ın output dizinini bul: `~/.hermes/cron/output/{job_id}/`
3. En son `.md` dosyasını oku — Error bölümü hatanın kaynağını verir
4. Hata türüne göre ayrıştır:

## Hata türüne göre ayrıştırma

### Provider hataları (HTTP 400/404/410/429/500)
- **400 `x-opencode-session` eksik:** OpenCode Go provider yeni sürümde session header zorunlu. Etkilenen: cron job'lar + Nanobot (Dewey) + `nanobot agent --message`. Geçici fix: consumer'ları openrouter'a çevir. Nanobot config: `~/.nanobot/config.json`.
- **404 / 410 Gone:** Model silinmiş/ölü. Model adını değiştir.
- **429 Rate limit:** Free tier limiti dolmuş. Provider'ı değiştir veya ücretli plana geç.
- **500 Internal Server Error:** Provider tarafı sorunlu. Key doğruysa model deployment down demektir. Başka model dene.
- **HTTP 000 / timeout:** Provider cevap vermiyor. Provider'ı değiştir.

### Delivery hataları
- **`Telegram send failed: RuntimeError('cannot schedule new futures after interpreter shutdown')`:** Gateway restart sırasında cron pool'u öldü. Sorun cron'da değil — gateway restart kaynağını bul (bkz. gateway-restart-loop-2026-09.md). Cron kendisi sağlıklı.

### Agent hataları
- **Prompt boş/yanıtsız:** Agent model seçimi yanlış veya provider çalışmıyor. Model/provider değiştir.
- **Script not found (`.../scripts/#!...` veya uzun kod satırı):** job'ın `script` alanına dosya YOLU yerine script METNİ yazılmış, ya da mutlak yol verilmiş. Alan `~/.hermes/scripts/` köküne göre **göreli dosya adı** ister. Onarım: dosyayı `~/.hermes/scripts/<ad>.py` olarak yaz + `chmod +x`; repo modüllerini import eden script `sys.path.insert(0, "/home/hermes/.hermes/hermes-agent")` + `os.chdir(...)` yapmalı (cron farklı cwd'den koşar); `hermes cron edit <job> --script <ad>.py`; emin olmak için `cron run` → `cron tick` → `cron runs` çıktısında yeni `completed` satırı.

## Cron output okuma

Her cron job çıktısı `~/.hermes/cron/output/{job_id}/` dizininde `YYYY-MM-DD_HH-MM-SS.md` formatında kaydedilir. Dosya yapısı:
- `## Prompt` bölümü — cron'un gönderdiği prompt
- `## Error` bölümü — hata varsa burada (```
``` ile sarılı)

### Sessiz içerik arızası — `last_status: ok` ama çıktı çöp

**Hata kaydı YOKTUR; tek belirti kullanıcıya giden metnin kendisidir.** Koşu hatasız tamamlanır, `last_status: ok` yazar, ama teslim edilen mesaj konu dışıdır / dili bozuktur.

Belirti deseni: metin başka bir konuya kaymış, Türkçe bozulmuş (yarım/uydurma kelimeler), araya başka dillerin sözcükleri karışmış, son cümle "şimdi çıktıyı üretiyorum" gibi bir vaat. Bozulma günler içinde kademeli büyür — ilk günlerde yalnız harf hataları görünür, sonra tam konu kayması.

Ayırt etme: bu sınıf **kod/script hatası değildir**; iş zayıf/ücretsiz bir modele override edilmiştir (bkz. SKILL.md §12c — override temizleme + konu kilidi).

Teşhis sırası:
1. `sed -n '/## Response/,$p' ~/.hermes/cron/output/<job_id>/<en-yeni>.md` → gerçek teslim metnini oku.
2. Son 3-4 çıktıyı yan yana koy → bozulmanın başladığı koşuyu bul.
3. `jobs.json`'da `model`/`provider` dolu olan işleri çıkar → şüpheliler bunlar.
4. Düzeltme sonrası işi elle tetikle ve **çıktı dosyasından** doğrula; `ok` durumu kanıt sayılmaz.

## Pitfall

- **`last_status: ok` doğru içerik garantisi değildir.** Kullanıcıya mesaj gönderen işlerde periyodik olarak çıktının KENDİSİNİ oku — status yeşilken çöp teslim eden bir iş hiçbir uyarı üretmez.
- Kullanıcıya giden prompt işlerinde konu kilidi (`başka konuya kayarsan tek kelime: [SILENT]`) yoksa modelin konu kayması doğrudan kullanıcıya ulaşır.
- Cron hataları göz ardı edilmemeli: `last_status: error` olan job'ları sessizce geçmişe bırakma — her hata ya provider Sorunu ya da config Sorunu demektir.
- `last_run_at` tarihine bakarak ne zamandan beri çalışmadığını ölç — 10+ gün çalışmayan cron kör demektir.
- `Interpreter shutdown` hataları gateway restart'ın SYMPTOM'u — cron'u düzeltmeye çalışma, gateway restart kaynağını bul.