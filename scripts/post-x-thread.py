#!/usr/bin/env python3
"""
X Thread Poster — Zero to AI Agent
Posts a thread to X/Twitter via API using n8n credential or direct v2 API.
"""

import json
import os
import sys
import urllib.request
import urllib.parse

# Read thread JSON
THREAD_FILE = os.path.expanduser("~/.hermes/scripts/x-thread-zero-to-ai.sh")

# X API v2 credentials from env
API_KEY = os.environ.get("X_API_KEY", "")
API_SECRET = os.environ.get("X_API_SECRET", "")
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "")
ACCESS_SECRET = os.environ.get("X_ACCESS_SECRET", "")
BEARER_TOKEN = os.environ.get("X_BEARER_TOKEN", "")

# Check if we have X credentials
if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
    print(json.dumps({
        "status": "error",
        "message": "X API credentials not found in environment. Set X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET"
    }))
    sys.exit(1)

# Use tweepy or requests_oauthlib
try:
    import tweepy
    client = tweepy.Client(
        consumer_key=API_KEY,
        consumer_secret=API_SECRET,
        access_token=ACCESS_TOKEN,
        access_token_secret=ACCESS_SECRET
    )
    
    tweets = [
        "🤖 You don't need $500/month in SaaS to run your own AI agent.\n\nYou need a $7 server and one guide.\n\nHere's the exact playbook I used → https://ergene.gumroad.com/l/zero-to-ai-agent",
        
        "🧵 What Zero to AI Agent covers:\n\n1️⃣ Hermes Agent setup & config\n2️⃣ 3 production n8n workflows\n3️⃣ Telegram bot integration\n4️⃣ 17-platform monitoring (Agent Reach)\n5️⃣ AI Agency business model → turn your stack into revenue\n\nAll in plain English, no jargon.",
        
        "📦 What you get:\n\n• 39-page PDF (10 chapters)\n• 3 production n8n workflow JSONs\n• API Key Checklist (one page)\n• Agent Reach monitoring config\n• One-click install script\n\nBonus: Ch.10 — \"Nobody buys AI agents\" — the honest business model.",
        
        "⚡ Written from production experience.\n\nMy Hermes agent runs 24/7 on a $7 server. No cloud bills. No SaaS.\n\nYours can too.\n\n👇 https://ergene.gumroad.com/l/zero-to-ai-agent"
    ]
    
    previous_id = None
    for i, text in enumerate(tweets):
        if previous_id:
            response = client.create_tweet(text=text, in_reply_to_tweet_id=previous_id)
        else:
            response = client.create_tweet(text=text)
        
        tweet_id = response.data['id']
        print(f"Tweet {i+1}: {tweet_id}")
        previous_id = tweet_id
    
    print(json.dumps({"status": "ok", "thread_length": len(tweets), "first_tweet": tweets[0][:50]}))
    
except ImportError:
    print(json.dumps({"status": "error", "message": "tweepy not installed. Run: pip install tweepy"}))
    sys.exit(1)
except Exception as e:
    print(json.dumps({"status": "error", "message": str(e)}))
    sys.exit(1)
