# Chapter 5: n8n Integration — Workflow Automation

## Concept

n8n is **enterprise workflow automation** that runs on your own server. It connects 400+ services without code.

Your AI agent handles **decision-making and intelligence**. n8n handles **scheduled execution and integrations**. Together, they're unstoppable.

## Architecture

```
Agent (Hermes)  ←→  n8n API  ←→  400+ services
    │                        │
    │                        ├── Gmail
    │                        ├── Telegram
    │                        ├── Google Sheets
    │                        ├── OpenAI/Anthropic
    │                        ├── PostgreSQL
    │                        └── 395+ more
    │
    └── Telegram / Web UI (you)
```

## Installation

### Option A: Docker (Recommended)

```bash
# One-liner install
docker run -d \
  --name n8n \
  --restart unless-stopped \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  n8nio/n8n

# Wait 30 seconds, then open:
# http://your-server-ip:5678
```

### Option B: Coolify (Easier Management)

If you run Coolify (I do), deploy n8n as a service:
1. Open Coolify dashboard
2. Add Service → n8n
3. Set domain: `n8n.yourdomain.com`
4. Deploy (takes ~2 minutes)

## Getting Your API Key

1. Open n8n → Settings → API Keys
2. Click "Create API Key"
3. Copy the key (starts with `n8n_api_...`)

## Your First Workflow: Daily Lead Collector

This workflow runs every morning and collects leads from multiple sources.

**Create this in n8n:**

1. **Schedule Trigger**: Every day at 08:00
2. **HTTP Request**: GET Twitter search for "need automation"
3. **HTTP Request**: GET Reddit r/smallbusiness new posts
4. **Code Node**: Merge and deduplicate
5. **AI Node**: Rank by relevance (OpenAI)
6. **Telegram**: Send top 3 leads to your phone

### Export (JSON)

You'll find the complete workflow JSON in the included `workflows/` folder. Import it in n8n:
- Workflows → Add Workflow → Import from JSON

## Agent + n8n Communication

Your agent talks to n8n via the API:

```bash
# From your agent
curl -X POST https://n8n.yourdomain.com/webhook/trigger-workflow \
  -H "Content-Type: application/json" \
  -d '{"action": "scan_opportunities"}'
```

Configure in Hermes:

```bash
hermes config set n8n_url https://n8n.yourdomain.com
hermes config set n8n_api_key n8n_api_your_key_here
```

## Workflow Templates Included

This book includes 3 production workflows you can import immediately:

| Workflow | Purpose | When to Run |
|----------|---------|-------------|
| **Lead Scanner** | Scans Twitter + Reddit for leads | Every morning |
| **Content Reporter** | Summarizes industry news | Weekly |
| **Health Monitor** | Checks server + agent status | Every 30 minutes |

## Verification

```bash
# Test n8n API connection
curl -X GET https://n8n.yourdomain.com/healthz
# Returns: 200 OK

# Trigger a workflow
curl -X POST https://n8n.yourdomain.com/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

## Pro Tips

1. **Rate limiting**: Don't run AI-powered workflows more than once per hour. Costs add up.
2. **Error handling**: Always add an "Error" output on every node. n8n silently fails otherwise.
3. **Credentials**: Store API keys in n8n's credential store, not in workflow parameters.
4. **Version control**: Export workflows to JSON and commit to git.

## Next Steps

With n8n, you have automation superpowers. Chapter 6 shows how to build monitoring systems that watch the world for you.
