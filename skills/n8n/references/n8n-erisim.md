# n8n Erişim Bilgileri (hafızadan taşındı 15.09.2026)

- API anahtarı ve URL: `/home/hermes/.config/n8n-api.json` (URL: https://n8n.aiergene.xyz).
- Yerel API: `http://127.0.0.1:5678/api/v1/...`, başlık `X-N8N-API-KEY`.
- Konteyner içinden liste: `docker exec n8n n8n list:workflow` — 14.09 itibarıyla 7 iş akışı görünüyor (en önemlisi `Lead-CRM-Automation-v1`, aktif).
- Uyarı: 5678 kapısı güvenlik duvarında internete açık. Webhook için gerekli olabilir ama gözden geçirilmeli.
