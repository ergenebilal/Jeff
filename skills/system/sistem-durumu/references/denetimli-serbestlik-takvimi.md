# Bilal — Denetimli Serbestlik Takvimi

**Kaynak:** `~/.hermes/scripts/probation_reminder.py` (cron: "Denetim Hatırlatıcı", ID: c16a3add1f03, her gün 06:00)
**Orijinal Kaynak:** Google Calendar (OAuth bozuldu — `deleted_client`)

## Durum Bilgisi

| Kalem | Detay |
|-------|-------|
| Sebep | Esrar — Ağustos 2025 gözaltı |
| Başlangıç | Kasım 2025 |
| Bitiş | Aralık 2026 |
| Testler | ✅ Temiz |
| Aile | Bilmiyor (saklanması gereken bilgi) |

## Haftalık Program

- **Cuma** 15:30 — Grup Programı (B Blok 1. Kat)
- **Cuma** 16:00 — Bireysel Görüşme (Esra Canlı, B Blok 1. Kat)
- Bireysel görüşme her Cuma değil, belirli tarihlerde (aşağıdaki listeden kontrol et)

## Takvim (Hardcoded)

| Tarih | Gün | Etkinlik | Yer |
|-------|-----|----------|-----|
| ~~2026-06-26~~ | Cuma | ~~Seminer~~ | 15 Temmuz Konferans Salonu |
| ~~2026-07-21~~ | Salı | ~~Seminer~~ | 15 Temmuz Konferans Salonu |
| **2026-08-14** | **Cuma** | **Grup Programı** | **B Blok 1. Kat** |
| 2026-08-28 | Cuma | Grup Programı | B Blok 1. Kat |
| 2026-09-11 | Cuma | Grup Programı | B Blok 1. Kat |
| 2026-09-25 | Cuma | Grup Programı | B Blok 1. Kat |
| **2026-10-09** | **Cuma** | **Grup Programı** | **B Blok 1. Kat** |
| 2026-10-23 | Cuma | Grup Programı | B Blok 1. Kat |
| 2026-11-06 | Cuma | Grup Programı | B Blok 1. Kat |
| 2026-11-20 | Cuma | Grup Programı | B Blok 1. Kat |
| 2026-12-04 | Cuma | Grup Programı | B Blok 1. Kat |
| 2026-12-18 | Cuma | Grup Programı (15:30) | B Blok 1. Kat |
| 2026-12-18 | Cuma | **Bireysel Görüşme (16:00)** | B Blok 1. Kat |

## Notlar

- Takvim güncellemesi gerektiğinde `probation_reminder.py` içindeki `schedule` listesi düzenlenmeli.
- Google Calendar OAuth onarılınca `takvim_etkinlik_ekle()` ile etkinlikler yeniden eklenebilir.
- Cron her gün 06:00'da bir sonraki günü kontrol eder, yarın randevu varsa Bilal'e Telegram bildirimi gider.
