#!/bin/bash
# X thread: Zero to AI Agent — $7.99
# Usage: ./x-thread-zero-to-ai.sh [fal_image_url]
# If first arg is provided, uses it as the tweet image

IMAGE_URL="${1:-}"

# Thread tweets as JSON array (one per line)
# We'll use the n8n Twitter credential or direct API
cat << 'EOF'
{
  "thread": [
    {
      "text": "🤖 You don't need $500/month in SaaS to run your own AI agent.\n\nYou need a $7 server and one guide.\n\nHere's the exact playbook I used →"
    },
    {
      "text": "🧵 What Zero to AI Agent covers:\n\n1️⃣ Hermes Agent kurulumu ve konfigürasyonu\n2️⃣ n8n ile 3 production workflow\n3️⃣ Telegram bot entegrasyonu\n4️⃣ 17 platformda monitoring (Agent Reach)\n5️⃣ AI Agency business model — stack'ini gelire çevir\n\nAll in plain English, no jargon."
    },
    {
      "text": "📦 What you get:\n\n• 39-page PDF (10 chapters)\n• 3 production n8n workflow JSONs\n• API Key Checklist (all in one page)\n• Agent Reach monitoring config\n• One-click install script\n\nBonus: Chapter 10 — \"Nobody buys AI agents\" — the honest business model."
    },
    {
      "text": "⚡ This guide is written from production experience.\n\nMy Hermes agent runs 24/7 on a $7 server. No cloud bills. No SaaS subscriptions.\n\nYours can too.\n\n👇 Get it here:\nhttps://ergene.gumroad.com/l/zero-to-ai-agent"
    }
  ]
}
EOF
