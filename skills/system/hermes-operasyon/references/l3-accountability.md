# L3 Accountability — Sistemin Sağlığı Senin Sorumluluğun

**Bilal'in direktifi (07.09.2026):** "Sen sistemin sağlığından sorumlusun. Çalışmadığını benim tespit etmem değil, senin anında farkedip sorunu otonom çözmen gerekirdi."

Bu bir L3 (Kritik Bilişsel Hata) — kullanıcı söylemeden önce senin fark etmen bekleniyor.

## Olay (07.09.2026)

- Coolify reverse proxy (Traefik) container'ı bir noktada öldü (kullanıcı fark etti, ben fark etmedim)
- Kullanıcı "n8n.aiergene.xyz ve esgrupmetal.com açılmıyor" dedi — **o an benim hatam**
- Oysa 5dk önce watchdog'um olsaydı, kendim otonom geri başlatabilirdim
- OpenCode çözdü (coolify-proxy companion container + APP_KEY yedekten dönüş + esgrup-web redeploy)
- **Sonrasında ben watchdog katmanını ekledim** (5dk cron + alert flag + restart policy)

## Recurring Workflow — Ajan Çözdükten Sonra

**1) Olay tespiti** (kullanıcı veya sen)
**2) Triage** — kendi tool'larınla durumu kontrol et
**3) Karar:**
   - (a) Kendin çözebilirsen → otonom çöz, watchdog kur, audit log
   - (b) Başka ajana delege et (OpenCode, Nanobot) → **"müdahale etmeyelim halletsin kendisi"** moduna geç, gözlemle
   - (c) Kullanıcı onayı gerekli → kısa özet + seçenekler sun, kararı bekle
**4) Çözüm sonrası — KENDİ KATMANINI KUR:**
   - Watchdog script'i güncellendi mi? (Yeni container/site eklendiyse)
   - Container restart policy `unless-stopped` mı?
   - Alert flag mekanizması var mı?
   - Canlı test edildi mi? (ilk koşu + 5dk sonraki tick)
   - SOUL/memory'ye "bir daha olmasın" kuralı yazıldı mı?

**Bu adım atlanırsa aynı olay 2 hafta sonra tekrar eder.** Ajan çözer, sen unutursun, sistem tekrar çöker, kullanıcı yine söyler → güven kaybı.

## L3 Tetikleyiciler (kendine sor)

- [ ] Watchdog cron kurulu mu? (`crontab -l | grep watchdog`)
- [ ] Yeni deploy edilen her public servis watchdog'a eklendi mi?
- [ ] Container restart policy kontrol edildi mi?
- [ ] Eski alert flag dosyası var mı? (varsa kullanıcıya haber gitmemiş → flag'i temizle, manual notification gönder)
- [ ] Son 24 saatte watchdog log'unda FAIL var mı?
- [ ] Açıklanamayan bir çökme oldu mu? → root cause analysis yap, hipotezi terk etme

## Alert Flag Protokolü

```bash
# Flag dosyası: /home/hermes/.hermes/state/reverse-proxy-alert.flag
# İçerik:
TIMESTAMP=2026-09-07T16:30:00+03:00
ACTIONS=coolify-proxy restart
ESGRUP=302
N8N=200

# Yorumlama:
# - Flag varsa → sorun VARDI, otonom restart yapıldı
# - Flag 24 saatten eski → kullanıcıya haber gitmemiş olabilir (Telegram bot bağlıysa zaten gitmiştir)
# - Flag varsa ve sorun tekrar yok → durumu kullanıcıya özetle, flag'i temizle
```

## Pitfalls

- [ ] **Watchdog'u sadece yazma, canlı test et** — script syntax hatası olabilir, ilk koşuda başarısız olur
- [ ] **Alert flag spam yapma** — her tick'te Telegram atma, sadece durum değişimi bildir
- [ ] **Ajan çözdükten sonra "müdahale etmeyelim" modunda kalıp watchdog kurmayı unutma** — sık yapılan hata
- [ ] **Watchdog yaz ama restart çağırma** — log-only modda bırak, restart'ı ayrı kanaldan yap (döngü riski)
- [ ] **Birden fazla watchdog olabilir** — root crontab + hermes crontab + systemd timer → hepsini kontrol et, çakışma olmasın

## İlgili

- `scripts/reverse-proxy-watchdog.sh` — concrete 5dk cron script
- `hermes-operasyon` skill — gateway watchdog pattern'i (port 80 vs 9119 dikkat)
