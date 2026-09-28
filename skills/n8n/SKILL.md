---
name: n8n
description: n8n Otomasyon Motoru ve Süper-Ajan Entegrasyon Protokolü (Beyin-Kas Mimarisi)
---

# n8n & Jeff Süper-Ajan Operasyonel Kılavuzu

n8n, Jeff'in deterministik "kas ve sinir sistemi"dir. 
Jeff (LLM) **Beyin**'dir (muhakeme, karar, dinamik strateji); n8n ise **Kas**'tır (entegrasyon, veri boru hatları, webhooks, 400+ servis bağlantısı).

---

## 1. Altın Kural: Ne Zaman Jeff, Ne Zaman n8n?

| Senaryo | YANLIŞ YAKLAŞIM (Anti-Pattern) | DOĞRU YAKLAŞIM (n8n Pattern) |
|---|---|---|
| **Çok Servisli Dağıtım** | Jeff'in 200 satır Python yazıp Gmail, Notion ve Slack API'lerine tek tek bağlanması. | Jeff'in n8n'deki tek bir webhook'a JSON atması. n8n'in işi deterministik olarak dağıtması. |
| **Zamanlanmış Veri Çekme** | Jeff'in her 10 dakikada bir uyanıp API scrape etmesi (token israfı). | n8n cron düğümünün veriyi çekip yerel bir SQLite/JSON dosyasına bırakması; Jeff'in sadece analiz etmesi. |
| **Kullanıcı Bildirimleri** | Jeff'in her bildirim için ayrı script çalıştırması. | n8n bildirim hattının (Telegram, WhatsApp/Waha, E-posta) tetiklenmesi. |
| **Hata Toleransı (Retry)** | Network kesintisinde Jeff'in döngüye girip token tüketmesi. | n8n'in dahili Retry & Error Trigger mekanizmasının devrede olması. |

---

## 2. Sunucu Altyapısı ve Uç Noktalar

- **Yerel n8n URL:** `http://127.0.0.1:5678` (Host network üzerinde doğrudan erişilebilir)
- **Harici / Webhook URL:** `https://n8n.aiergene.xyz`
- **Docker Konteyneri:** `n8n` (Docker altında 7/24 çalışır vaziyette)
- **Veritabanı Yedeği:** Her gece 02:00'de otomatik yedeklenir.

---

## 3. Temel Entegrasyon Desenleri

### Desen A: Webhook Tetikleme (Trigger & Forget)
Bir analiz veya karar bittiğinde harici dünyayı harekete geçirmek için:
```bash
# Örnek: Analiz bitti, n8n üzerinden bildirim ve veri akışını tetikle
curl -s -X POST http://127.0.0.1:5678/webhook/hermes-lead-alert \
  -H "Content-Type: application/json" \
  -d '{"status": "success", "summary": "Günün kritik sinyalleri", "data": [...]}'
```

### Desen B: Ajan Girdi Kuyruğu (Queue Ingestion)
n8n dış dünyadan (CRM, formlar, webhook'lar) gelen veriyi toplar. Jeff sabah veya proaktif turda bu veriyi okur:
- n8n veriyi `/home/hermes/data/inbox/` veya SQLite tablosuna yazar.
- Jeff: `goals.db` içine hedef açar ve işler.

### Desen C: n8n MCP Kullanımı
`n8n-mcp` araçları:
- `n8n_list_workflows`: Mevcut aktif iş akışlarını listeler.
- `n8n_execute_workflow`: Belirli bir ID'ye sahip akışı parametrelerle çalıştırır.
- `n8n_get_execution`: Akışın başarı durumunu ve loglarını kontrol eder.

---

## 4. Güvenlik ve Dayanıklılık İlkeleri
1. **API Key Yenileme:** n8n API anahtarı `401 Unauthorized` verirse, n8n arayüzünden (Settings -> API) yeni bir key üretilip `~/.hermes/config.yaml` içindeki `n8n-mcp.env.N8N_API_KEY` alanına yazılmalıdır.
2. **Gizlilik:** Webhook yüklerine asla düz metin şifreler, SSH private key'ler veya hassas sistem ortam değişkenleri basılmaz.
