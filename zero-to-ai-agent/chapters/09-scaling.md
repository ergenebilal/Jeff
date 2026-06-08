# Chapter 9: Scaling — From Solo to Agency

## Concept

One agent is powerful. Ten agents serving ten clients changes your life.

This chapter covers the **agency model** — running multiple agent instances for different clients. Each client gets their own AI agent customized to their business.

## Multi-Client Architecture

```
┌──────────────┐     ┌──────────────────┐
│   Your       │     │  n8n (Shared)    │
│   Server     │     │  - 34 workflows  │
│              │     │  - 400 services  │
│   Hermes     │     └──────────────────┘
│   (You)      │            │
│              │     ┌──────────────────┐
│   Client 1   │     │  Client 1        │
│   Client 2   │     │  - Lead scanner  │
│   Client 3   │     │  - DM responder  │
└──────────────┘     └──────────────────┘
```

## Client Onboarding Pipeline

I built an **Instagram DM automation** pipeline that handles initial client contact:

1. DM comes in → Instagram webhook triggers n8n
2. AI agent responds (qualifies the lead)
3. Lead scores > 70 → my Telegram gets an alert
4. I personally handle the call
5. Client is onboarded → their agent configured

**I only touch calls that score above 70.** Everything else is autonomous.

## Pricing Model

From my actual pricing (in USD, Turkish market adjusted):

| Service | Price | What They Get |
|---------|-------|---------------|
| AI DM Responder | $29-49/mo | Instagram/WhatsApp auto-reply |
| Lead Scanner | $49-99/mo | Daily lead reports + CRM integration |
| Full Agent Setup | $199-499 one-time | Custom agent + n8n workflows |
| White-label Agency | $499-999/mo | Your own Hermes stack to resell |

## The Economics

**Your costs:**
- Server: $20/mo (DigitalOcean, Hetzner, etc.)
- API costs: $5-15/mo (DeepSeek is cheap)
- Total: ~$30/mo

**Your revenue (example):**
- 10 clients × $49/mo = $490/mo (Lead Scanner)
- 2 one-time setups × $299 = $598
- **Monthly recurring: $490** (with $30 cost = $460 margin)

This is **solo, passive, and automated**.

## Client Agent Customization

Each client gets a skill file:

```yaml
# ~/.hermes/clients/restaurant-xyz/SKILL.md
---
name: restaurant-xyz
client: ABC Restaurant
---

## Client Context
- Business: Fine dining, Istanbul
- Pain point: Lost reservations on Instagram DM
- Solution: AI reservation responder

## Communication Style
- Warm, professional
- Turkish language
- Always offer reservation link

## Restrictions
- Never discuss pricing
- Never modify existing reservations
- Escalate complaints to manager
```

## White-Labeling

Your clients don't need to know about Hermes or n8n. They see:

```
Your Brand Name
├── Dashboard (you build)
├── Telegram bot (your logo)
├── Reports (your template)
└── Invoices (your company)
```

Everything under the hood is the same stack. They just see your brand.

## Scaling to 10+ Clients

At 10+ clients, you need:

1. **Separate databases** — One PostgreSQL instance, different schemas
2. **Separate n8n instances** — Or shared n8n with tagged workflows
3. **Client dashboard** — Simple web UI showing status per client
4. **Automated billing** — Stripe/Paddle subscription

## Pro Tips

1. **Start with one client for free** — Build a case study, then charge
2. **Fire bad clients** — Some clients create more work than revenue. Drop them.
3. **Standardize** — Don't custom-build everything. 80% template, 20% customization.
4. **Over-deliver in month 1** — They see value, they stay for months 2-12.
