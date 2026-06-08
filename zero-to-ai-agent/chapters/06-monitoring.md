# Chapter 6: Monitoring — Watch the World While You Sleep

## Concept

The real power of an AI agent isn't what it does when you're watching — it's what it does when you're not.

This chapter builds a **passive income monitoring stack** that:
1. Scans Twitter for "need automation" posts
2. Monitors Reddit for small business problems
3. Tracks GitHub trending repos
4. Watches competitor websites
5. Alerts you on Telegram when something interesting happens

## Cron Jobs — Your Agent's Heartbeat

Hermes has a built-in scheduler. Let's set up our first cron job:

```bash
hermes cron create \
  --name "opportunity-scan" \
  --schedule "0 8 * * *" \
  --prompt "Run opportunity-scan skill and report findings" \
  --deliver telegram
```

Every day at 08:00, your agent will:
1. Scan Twitter for leads
2. Check Reddit for business problems
3. Search GitHub for trending tools
4. Send you a Telegram summary

## Agent Reach — Multi-Platform Monitoring

Install Agent Reach for platform-specific monitoring:

```bash
cd /opt
git clone https://github.com/your-username/Agent-Reach.git
cd Agent-Reach
pip install -r requirements.txt
```

Configure channels in `config.yaml`:

```yaml
channels:
  twitter:
    enabled: true
    search_queries:
      - "need an AI agent"
      - "looking for automation"
      - "chatbot for my business"
    
  reddit:
    enabled: true
    subreddits:
      - entrepreneur
      - smallbusiness
      - automation
    
  github:
    enabled: true
    topics:
      - ai-agent
      - automation
      - n8n
```

## Opportunity Scoring

Not all leads are equal. Add an AI-powered scoring layer:

```bash
cat > ~/.hermes/scripts/score_opportunity.py << 'PYEOF'
import json, sys

def score_opportunity(text):
    """Score a lead from 0-100 based on buying signals"""
    score = 0
    
    # High-value signals
    buying_signals = ["how much", "pricing", "need help", "looking for", "recommend"]
    for signal in buying_signals:
        if signal in text.lower():
            score += 20
    
    # Technical fit signals
    tech_signals = ["n8n", "automation", "chatbot", "workflow", "ai agent"]
    for signal in tech_signals:
        if signal in text.lower():
            score += 15
    
    # Urgency signals
    urgent = ["urgent", "asap", "today", "now", "immediately"]
    for signal in urgent:
        if signal in text.lower():
            score += 10
    
    return min(score, 100)

if __name__ == "__main__":
    data = json.load(sys.stdin)
    for item in data:
        item["score"] = score_opportunity(item.get("text", ""))
    print(json.dumps(data, indent=2))
PYEOF
```

## The Monitoring Dashboard

You now have 3 automated systems working while you sleep:

```
07:00 → Agent health check (self-audit)
08:00 → Opportunity scan (find leads)
09:00 → Competitor monitoring (check websites)
10:00 → Content generation (if you have a content channel)
18:00 → Daily summary report
```

## Alert Thresholds

Configure your agent to escalate:

```yaml
alerts:
  critical:
    - disk_usage > 85%
    - agent_unresponsive > 30min
    - n8n_down
  
  warning:
    - lead_score > 70 (immediate Telegram alert)
    - competitor_launched_product
    - ram_usage > 80%
```

## Verification

```bash
# List active monitoring jobs
hermes cron list

# Test opportunity scan immediately
hermes run "Run opportunity-scan skill right now"

# Check delivery
# Your Telegram should have received a report
```

## Pro Tip

Don't over-alert. If your phone buzzes every time a tweet mentions "AI", you'll mute it within a week. Set thresholds high and batch low-priority alerts into daily digests.

## Next Steps

Your agent now watches the world for you. Chapter 7 turns this into an actual revenue stream.
