# Çıktı Kalitesi Kuralları

## Ne Zaman Kullanılır
Bilal'e bir şey sunduğunda — rapor, durum, cron sonucu, sistem kontrolü.

## Kural 0: Temiz ve Sade Çıktı
- JSON dökümü, API yanıtları, ham veri **gösterme**
- Çince karakter, encoding hatası **asla olmamalı**
- Gereksiz detay, uzun liste, tablo karmaşası **yapma**
- Sadece **net, okunabilir Türkçe sonuç** sun

## Kural 1: İlgisiz Bilgiyi Gösterme
- Cron listesi gibi şeyleri sormadan gösterme — sadece **işine yarayanları** göster
- 17 cron varsa hepsini listeleme, sadece önemli olanları
- "Diğerleri sessiz çalışıyor, sana rapor gelmez" de ve geç

## Kural 2: JSON Çıktılarını Temizle
- `cronjob action=update` gibi araçlardan gelen JSON yanıtlarını **olduğu gibi gösterme**
- Sadece sonucu özetle: "Güncellendi ✅" yetiyor
- Kullanıcı JSON görmek istemez — sadece ne olduğunu söyler

## Kural 3: Encoding Kontrolü
- Türkçe karakterler (ı, ş, ç, ğ, ö, ü) doğru görünmeli
- Unicode escape (\uXXXX) görünürse — sorun var, düzelt
- Çince/Japonca karakter çıkarsa — encoding hatası, düzelt

## Kural 4: Uzunluk Sınırı
- Status/health gibi şeyler için 3-5 satır yeterli
- Rapor için başlık + 3 madde + tavsiye = max 15-20 satır
- Detaylı rapor istenirse ancak o zaman uzat

## Örnek İyi Yanıt
```
8/8 agent çalışıyor ✅
RAM: %85, Disk: %50, CPU: %38
Sorun yok.
```

## Örnek Kötü Yanıt
```
╔══════════════════════════╗
║ JEFF 4.0 — STATUS       ║
╚══════════════════════════╝
📋 AGENTS
────────────────────────
  gelisim      ✅ running PID: 1496256
  kreatif      ✅ running PID: 1498419
  ... (8 satır daha)
🏥 HEALTH
────────────────────────
  RAM: %84.9 (4849MB free)
  ... (5 satır daha)
📊 METRICS (24h)
────────────────────────
  Total events: 0
📦 TASK QUEUE
────────────────────────
  Total: 0
```
İlk kısım yeterli, geri gereksiz.
