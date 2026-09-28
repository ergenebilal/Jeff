# System Report Methodology

## Ne Zaman Üretilir
- Kullanıcı "sistem raporu", "kapsamlı rapor", "durum raporu", "özet geç", "neredeyiz" dediğinde
- Kullanıcı "sistem kodları dahil" / "kodlar da olsun" dediğinde → dosya yapısı ve process listesi ekle
- Haftalık bakım rutininin parçası olarak
- Büyük bir değişiklikten sonra (stack temizliği, yeni kurulum, upgrade)

## Veri Toplama Planı (Batch — 5 paralel grup)

**Batch 1 — Sistem + Docker + Jeff:**
```bash
echo "=== DISK ===" && df -h / /home 2>/dev/null | tail -2
echo "=== RAM ===" && free -h | head -2
echo "=== LOAD ===" && uptime
echo "=== DOCKER ===" && docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null | head -15
echo "=== JEFF3 ===" && /opt/hermes/jeff_v2/jeff3_start.sh status 2>/dev/null || echo "N/A"
```

**Batch 2 — AgencyOS CRM Pipeline (MCP):**
- `mcp_agencyos_get_sales_pipeline()`
- `mcp_agencyos_get_agency_state()`

**Batch 3 — Token + Audit:**
```bash
cat /opt/hermes/jeff_v2/reports/token-dashboard.md 2>/dev/null || echo "No token dashboard"
tail -30 /opt/hermes/audit/audit.log 2>/dev/null | head -30 || echo "No audit log"
```

**Batch 4 — API Health + Email + Sequences (MCP):**
- `mcp_agencyos_check_apify_balance()`
- `mcp_agencyos_get_email_stats()`
- `mcp_agencyos_list_sequences()`
- `mcp_agencyos_health_check_apis()`

**Batch 5 — Detaylar (sistem kodları — kullanıcı istediğinde zorunlu):**
```bash
echo "=== HERMES VERSION ===" && hermes --version 2>/dev/null
echo "=== SKILL COUNT ===" && ls ~/.hermes/skills/ 2>/dev/null | wc -l
echo "=== JEFF_V2 STRUCTURE ===" && find /opt/hermes/jeff_v2 -maxdepth 2 -type f \( -name "*.py" -o -name "*.json" -o -name "*.md" -o -name "*.sh" \) 2>/dev/null | head -20
echo "=== INSTAGRAM ===" && find /opt/hermes/instagram-pipeline -type f 2>/dev/null | head -10
echo "=== N8N WFs ===" && sqlite3 /var/lib/docker/volumes/y10hlm1fr9avvxt3asz5p0bk_n8n-data/_data/database.sqlite "SELECT name, active FROM workflow_entity WHERE active=1;" 2>/dev/null
```

## JSON Şeması (v3.0 — CRM/API/Jeff dahil)

```json
{
  "meta": {
    "report": "Hermes Sistem Durum Raporu",
    "tarih": "YYYY-MM-DD",
    "saat_utc": "HH:MM",
    "saat_local": "HH:MM UTC+3",
    "format_version": "3.0"
  },
  "system": {
    "sunucu": { "hostname", "ip", "uptime_gun", "cpu_load": [], "ram": {}, "disk": {}, "acik_portlar": [] },
    "hermes_agent": { "versiyon", "python", "install_dir", "model", "provider", "skill_sayisi" },
    "docker_konteynerler": [{"name", "status", "port"}]
  },
  "jeff_3_0": {
    "durum": "calisiyor|durmus",
    "process_sayisi": "number",
    "processler": [{"pid", "tip", "domain"}],
    "dosyalar": { "core": [], "config": [], "scripts": [], "governance": [] },
    "output_durumu": "string",
    "sorun": "string|null"
  },
  "cron_jobs": {
    "toplam": "number",
    "aktif_joblar": [{"id", "name", "schedule", "last", "script"}]
  },
  "crm_pipeline": {
    "toplam_lead": "number",
    "stage_dagilimi": {"New": 0, "Contacted": 0, "Replied": 0, "Booked": 0, "Won": 0, "Lost": 0},
    "email_durumu": {"email_var": 0, "email_yok": 0, "email_orani_yuzde": 0},
    "outreach": {"toplam_email_gonderilen": 0, "toplam_acilan": 0, "toplam_cevap": 0},
    "sequence_ler": [{"id", "name", "steps"}],
    "lead_kategorileri": {},
    "sorun": "string"
  },
  "apis_and_keys": {
    "genel_durum": "string",
    "providerlar": [{"provider", "status", "etki"}],
    "acil_gerekenler": []
  },
  "ai_cost": {
    "son_7_gun": {"toplam_call", "toplam_hata", "toplam_maliyet_usd"},
    "deepseek_bakiye": {"son_bilinen_usd", "son_log_tarihi", "sorun"}
  },
  "instagram_pipeline": {
    "durum": "aktif|pasif",
    "dosyalar": [],
    "approved_posts": 0
  },
  "agency_identity": {
    "mevcut": {"agency_name", "primary_niche"},
    "olmasi_gereken": {},
    "sorun": "string"
  },
  "gelir_durumu": {
    "mevcut_mrr": 0,
    "toplam_won": 0,
    "aktif_musteri": 0
  },
  "kritik_sorunlar_oncelik_sirali": [
    {"oncelik": 1, "baslik": "string", "cozum": "string"}
  ],
  "aksiyon_plani": {
    "bugun": [],
    "yarin": [],
    "bu_hafta": []
  }
}
```

## Teslimat

1. JSON'u `/opt/hermes/reports/sistem-raporu-YYYY-MM-DD.json` dosyasına yaz
2. `python3 -m json.tool` ile validasyon yap
3. `/home/hermes/sistem-raporu-YYYY-MM-DD.json` yoluna kopyala
4. **MEDIA:/home/hermes/sistem-raporu-YYYY-MM-DD.json** ile Telegram'a gönder
5. Dosyayı kullanıcı telefonuna indirebilir
6. Özet bulguları konuşma içinde markdown tablo olarak da paylaş

## JSON Tuzakları

| Tuzak | Çözüm |
|-------|-------|
| Port aralığı (`6001-6002`) | String olarak yaz: `"6001-6002"` |
| Docker isimleri çok uzun | Kesme, olduğu gibi kullan |
| Türkçe karakter | JSON'da sorunsuz, endişelenme |
| `hermes journey --json` yoksa | JSON'a `"NO_JOURNEY_DATA"` yaz, hata verme |
| `du -sh` timeout | `head -20` ile sınırla, timeout'ta boş dizi yaz |
| API key'ler | `api_keys_configured`'e sadece isim yaz ("Tavily"), değeri asla yazma |

## Örnek

07.07.2026 tarihli kapsamlı rapor: `/home/hermes/system-report-2026-07-07.json` (11.3 KB, 288 satır)
