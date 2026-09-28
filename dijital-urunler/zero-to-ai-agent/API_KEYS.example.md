# Zero to AI Agent — API Key Checklist
## Kurulum icin ihtiyaciniz olan tum anahtarlar

---

| # | Servis | Nereden Alinir | Ucretsiz? | Nereye Yapistirilir |
|---|--------|---------------|-----------|---------------------|
| 1 | **Telegram Bot Token** | @BotFather (Telegram) → /newbot | ✅ Evet | `hermes config set telegram_token XXX` |
| 2 | **AI Provider Key** | platform.openai.com (OpenAI) veya anthropic.com veya deepseek.com | ❌ Hayir ($2-20) | `hermes config set api_key XXX` |
| 3 | **Tavily API Key** | app.tavily.com → API Keys | ✅ 1000 sorgu/ay | `hermes config set web_search_api_key XXX` |
| 4 | **n8n API Key** | n8n Dashboard → Settings → API Keys | ✅ (kendi sunucun) | `hermes config set n8n_api_key XXX` |
| 5 | **Twitter API Key** | developer.twitter.com → Projects & Apps | ✅ Temel erisim | agent-reach-config.yaml |

---

### Adim Adim:

**1. Telegram Bot Token (2 dk)**
- Telegram'da @BotFather ara
- `/newbot` yaz
- Bot adi ve kullanici adi ver
- `123456:ABC-DEF1234` formatindaki token'i kopyala

**2. AI Provider Key (5 dk)**
- **En ucuz:** deepseek.com → API Keys → $2/token
- **En iyi:** anthropic.com → API Keys
- **Standart:** platform.openai.com → API Keys

**3. Tavily API Key (2 dk)**
- app.tavily.com adresine git
- GitHub ile kaydol
- API Keys sayfasindan kopyala

**4. n8n API Key (1 dk)**
- n8n panelini ac
- Settings → API Keys
- "Create API Key" tikla

**5. Twitter API Key (istege bagli, 10 dk)**
- developer.twitter.com adresine git
- Free plan yeterli
- Consumer Key + Consumer Secret al

---

**Ihtiyaciniz olan minimum:** Telegram Bot Token + AI Provider Key + Tavily API Key
**Hepsi ucretsiz degil:** AI Provider Key icin minimum $2/baslangic
