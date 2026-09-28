# n8n Production Playbook — API Key Checklist

| # | Service | Where to Get | Free Tier |
|---|---------|-------------|-----------|
| 1 | OpenAI API Key | platform.openai.com | No (pay-as-you-go) |
| 2 | n8n API Key | n8n Dashboard > Settings | Yes |
| 3 | Telegram Bot Token | @BotFather on Telegram | Yes |
| 4 | Tavily Search API | app.tavily.com | 1,000 queries/month |
| 5 | Google Sheets API | console.cloud.google.com | Yes (quota) |
| 6 | Slack Webhook URL | api.slack.com > Incoming Webhooks | Yes |
| 7 | Discord Webhook URL | Discord > Channel Settings > Integrations | Yes |
| 8 | PagerDuty Routing Key | support.pagerduty.com | Limited |
| 9 | Notion API Key | notion.so/my-integrations | Yes |
| 10 | PostgreSQL Connection | Your DB provider | Varies |

## Quick Start: Minimum Required Keys

To get started immediately with all workflows functional:
1. **OpenAI API Key** — powers all AI/LLM nodes
2. **Telegram Bot Token** — for Telegram AI Support Bot
3. **Tavily API Key** — for AI Web Research Agent

The remaining services are optional — each workflow degrades gracefully
if a specific credential is not configured.
