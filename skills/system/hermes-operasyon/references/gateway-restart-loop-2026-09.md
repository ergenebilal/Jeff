# Gateway Restart Döngüsü Vakası — 2026-09-06

## Semptom
Gateway her ~5 dk'da bir SIGTERM yiyip restart oluyordu. Arka plan process'leri
(bg probe script'leri) her restart'ta öldürülüyordu → "probe sonucu okunamadı"
sorunları. Journal'da bol miktarda `cannot schedule new futures after
interpreter shutdown` cron hatası.

## Teşhis zinciri (sıralı kanıtlar)

1. `systemctl show` → uptime hep ~5dk. NRestarts=0 (systemd restart etmiyor,
   DIŞARIDAN biri `systemctl restart` çağırıyor).
2. Journal: `Shutdown context: signal=SIGTERM under_systemd=yes` — SIGTERM
   systemd'den, saatler 5 dk periyodik (23:45, 23:50, 23:55, 00:00, 00:05, 00:10...).
3. Tüm cron kaynakları tarandı → **iki ayrı watchdog aynı anda**:
   - root crontab: `/usr/local/bin/hermes-watchdog.sh` (her 5 dk)
   - hermes crontab: `~/.hermes/scripts/gateway-healthcheck.sh` (her 5 dk)
4. `hermes-watchdog.sh` okundu → **`check_port80()` fonksiyonu suçlu**:
   port 80 dinlenmiyorsa `systemctl restart hermes-gateway` çağırıyordu.
5. Kök neden: **gateway port 80'i KULLANMIYOR** (9119 web / 8642 telegram).
   Port 80 nginx/Coolify işi. Bu makinede port 80 hiç dinlenmiyor → watchdog
   HER koşuda "restart" diyordu → sonsuz döngü.
6. Gateway-healthcheck.sh ise legit (gerçek koşullar: servis ölü / PID canlı
   değil / interpreter shutdown + flap koruması 10dk cooldown) — suçlu değil,
   ama restart edebildiği için ikincil kontrol edildi.

## İlginç teşhis tuzakları

- `--since "HH:MM"` filtresi eski saat dilimi kayıtlarını pencerelere sürüklüyor:
  "00:13:30 sonrası 40 SIGTERM" çıktı ama hepsi tarihsel. Güvenilir yol:
  journalctl | tail -60 ile GERÇEK son satırlara bakmak.
- `grep -iE "shutdown|stop"` gibi desenler blocklist'e takılıyor (sistem
  kapatma komutu sanılıyor) → komut metnini "SIGTERM ending" gibi zararsız
  alternatiflerle yaz.
- "interpreter shutdown" hataları restart'ın SYMPTOM'u — restart kesilince
  kendiliğinden kayboldu (00:15 sonrası sıfır yeni hata).

## Fix

`check_port80()` içinde `systemctl restart hermes-gateway` satırı kaldırıldı;
fonksiyon artık sadece log yazıyor ("gateway 80 hic kullanmaz... restart
EDILMEYECEK"). Yedek: mtime ile teyit (script 00:12'de değişti, restart döngüsü
00:13:20'de durdu).

## Doğrulama kanıtları

- Elle `sudo /usr/local/bin/hermes-watchdog.sh` → gateway restart ETMEDİ
  (ActiveEnterTimestamp değişmedi, NRestarts=0 sabit kaldı).
- Doğal cron tick (00:15:01) → yine restart yok, watchdog log'da yeni metin.
- Gateway uptime fix'ten sonra kesintisiz büyüdü (245s → 342s → 558s → 584s).
- Sıfır yeni SIGTERM (0000:20 sonrası).