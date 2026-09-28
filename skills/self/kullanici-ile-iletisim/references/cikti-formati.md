# Çıktı Formatı Kuralları

## Ne Zaman Kullanılır

Her yanıt verirken. Bilal'in çıktı kalitesiyle ilgili şikayetleri sonrası oluşturuldu (10.08.2026).

## Kesin Kurallar

### ❌ ASLA YAPMA
- JSON dump gösterme (cron update yanıtları, API response'ları)
- Çince karakter hatası içeren çıktılar gösterme
- Gereksiz uzunlukta çıktı üretme
- Tek bir iş için sayfalarca açıklama yazma
- Cron listesinde ilgisi olmayan job'ları gösterme

### ✅ HER ZAMAN YAP
- Kısa, net Türkçe özet ver
- Tablo formatında bilgi sun (varsa)
- Sadece işine yarayan bilgiyi göster
- "Anlaşıldı" de, uzatma
- JSON gerektiğinde sadece gerekli alanları göster

## Çıktı Uzunluğu Kılavuzu

| Tür | Maks Uzunluk |
|-----|-------------|
| Basit onay | 1 cümle |
| Durum raporu | 5-10 satır |
| Teknik açıklama | 1 paragraf |
| Karmaşık analiz | Tablo + 2-3 cümle özet |

## Sinyaller

Bunları duyduğunda **hemen** çıktıyı kısalt:
- "Çince görmeye gerek yok"
- "Bunu gösterme"
- "Kısa ol"
- "Görmeme gerek olmayan cronları gösterme"
- "Sayfalar dolusu yazı yazmışsın"

## Örnek

❌ Kötü:
```
Cron job başarıyla güncellendi. Eski isim: jeff3-sabah-brifingi, yeni isim: jeff4-sabah-brifingi. Prompt güncellendi. Sonraki çalışma zamanı: 2026-08-12T08:00:00+03:00. Durum: scheduled. Aktif: true. [JSON dump 200 satır]
```

✅ İyi:
```
Güncellendi: jeff4-sabah-brifingi ✅
```
