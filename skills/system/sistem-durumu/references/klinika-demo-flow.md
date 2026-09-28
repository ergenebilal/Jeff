# Klinika Demo Akışı

Mert'in "dijital çalışan" / "AI ajan işi" modelinin AgencyOS'taki karşılığı.

## Akış

```
1. CREATE  → klinika_create_agent({clinicName, websiteUrl, mode:"demo"})
2. TRAIN   → klinika_train_agent({agentId, websiteUrl})
3. TEST    → klinika_test_agent({agentId, message:"hasta sorusu"})
4. DEMO    → klinika_send_demo({leadId})  → demo kodu + pitch mesajı
```

## Pitfall'lar

- **İlk train parse hatası verebilir.** `klinika_train_parse_failed` alınırsa tekrar dene. İkinci deneme genelde başarılı.
- **Train 30-60 sn sürer.** `get_job_status` ile poll et.
- **Demo kodu sabit.** Create sırasında üretilir, değişmez.

## Örnek Çalışan Demo

| Klinik | Devadent Ağız ve Diş Sağlığı Polikliniği |
|--------|-------|
| Agent ID | kag-msn7zc9b-fh48cy |
| Demo Kodu | 959VX |
| Öğrenilen | 8 hizmet + 8 SSS + çalışma saatleri + yeni hasta kampanyası |
| Test 1 | "İmplant fiyatları?" → Kişiye özel, ücretsiz konsültasyona davet ✅ |
| Test 2 | "Pazar açık mısınız?" → 10:00-18:00, randevu teklifi ✅ |

## Demo Kodu Nasıl Çalışır?

Klinik sahibi WhatsApp'ta demo kodunu yazar → KENDİ web sitesinden eğitilmiş AI resepsiyonistle konuşur.
Müşteri token/model/altyapı bilmez — sadece WhatsApp'tan yazar.
