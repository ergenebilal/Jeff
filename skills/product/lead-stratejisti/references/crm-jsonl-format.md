# CRM JSONL Formatı — lead_pipeline_1.jsonl

## Lead Alanları

```json
{
  "company": "İşletme Adı",
  "phone": "+90 XXX XXX XX XX",
  "email": "ornek@email.com",
  "source": "Google Maps / Yerel Haber / Instagram / Web",
  "priority": "CRITICAL / HIGH / MEDIUM / LOW",
  "website": "https://ornek.com",
  "instagram": "@kullanici_adi",
  "notes": "Öncelik sebebi, dijital eksikler, potansiyel"
}
```

## Enrichment Workflow (10.07.2026)

CRITICAL lead'ler için web'den email enrichment:

1. `web_search` ile lead adı + "email" + "iletişim" sorgula
2. Bulunan web sitesini `web_extract` ile tara, iletişim bölümünü kontrol et
3. Başarılı: `info@site.com` → CRM'e kaydet
4. Başarısız: telefon numarası varsa onunla yetin, "enrichment_required" notu ekle

## Priorite Sistemi

| Seviye | Anlamı | Aksiyon |
|--------|--------|---------|
| CRITICAL | Sıfır dijital varlık veya kritik eksik | Haftalık öncelik |
| HIGH | Kısmi varlık, geliştirilebilir | Sıradaki |
| MEDIUM | Dijital varlığı var ama potansiyel var | Zamanla |
| LOW | Kurumsal/kendi ekibi var | Düşük öncelik |

## Dosya Yolu

`/home/hermes/jeff2/hq/lead_pipeline_1.jsonl`

## İlgili Script'ler

| Script | İşlev |
|--------|-------|
| `hq/lead_merge.py` | Eski lead dosyalarını birleştirip JSONL'ye yazar |
| `hq/lead_enrich.py` | Email enrichment yapar, CRM'i günceller |
| `hq/hizmet_motoru_cron.py` | Haftalık pipeline durum raporu hazırlar |

## Hizmet Motoru Cron

- **Zaman:** Her Pazartesi 11:00
- **Job ID:** e0061433a6fa
- **Adı:** hizmet-motoru-durum
