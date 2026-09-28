n8n Production Playbook v2
===========================
by ErgeneAI

WHAT'S INCLUDED:
- n8n-playbook.pdf (8 chapters, production deployment & workflow guide)
- 5 production-ready n8n workflow JSON files:
  1. Content Idea Aggregator (7 nodes) — RSS → AI → Google Sheets
  2. AI Web Research Agent (7 nodes) — Web Search → AI → Notion
  3. Production Error Alerting Pipeline (7 nodes) — Webhook → PagerDuty → Slack
  4. Secure Webhook Proxy (8 nodes) — Auth → Transform → Multi-channel
  5. Telegram AI Support Bot (9 nodes) — TG → AI Reply → Log

INSTALLATION:
1. Read the PDF guide first (includes architecture decisions)
2. Import workflows: n8n Dashboard → Workflows → Add from file
3. Configure credentials (all marked with {{ $credentials.xxx }})
4. Update webhook URLs and environment variables

REQUIREMENTS:
- n8n 1.0+ (Docker or self-hosted)
- Node.js 18+ (if self-hosting)
- PostgreSQL (recommended for production persistence)
- OpenAI API key (for AI-powered nodes)
- Free API keys: Telegram Bot Token (@BotFather), Tavily (app.tavily.com)

PRODUCTION USE:
These workflows power ErgeneAI's live AI agent infrastructure at
n8n.aiergene.xyz — 34 active workflows running since May 2026.

SUPPORT & COMMUNITY:
- Documentation: https://ergene.gumroad.com/l/n8n-playbook
- YouTube: https://youtube.com/@ergeneai
- GitHub: https://github.com/ergenebilal/Jeff
