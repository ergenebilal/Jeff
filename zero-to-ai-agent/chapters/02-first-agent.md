# Chapter 2: Your First AI Agent

## Concept

Your AI agent needs three things to exist:
1. **A server** to live on
2. **An agent framework** (we'll use Hermes Agent)
3. **A messaging channel** to communicate (Telegram)

Let's install Hermes Agent — the same open-source framework that powers my entire operation.

## Implementation

### Step 1: Update Your Server

```bash
ssh root@your-server-ip
apt update && apt upgrade -y
apt install -y curl git python3 python3-pip python3-venv
```

### Step 2: Install Hermes Agent

```bash
cd /opt
git clone https://github.com/NousResearch/hermes-agent.git
cd hermes-agent
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

This installs the `hermes` CLI tool. Verify with:

```bash
hermes --version
```

You should see `hermes 0.x.x` or similar.

### Step 3: Initialize Your Agent

```bash
hermes init
```

This creates your configuration at `~/.hermes/config.yaml`. The init command will ask you a few questions:
- **Name**: Choose your agent's name (I named mine "Jeff")
- **Provider**: DeepSeek (cheapest reliable option), Anthropic (most capable), or OpenAI
- **API Key**: Paste your API key
- **Telegram Token**: Your bot token from @BotFather

### Step 4: Get Your Telegram Bot Token

1. Open Telegram
2. Search for `@BotFather`
3. Send `/newbot`
4. Choose a name (e.g., "My Agent")
5. Choose a username (e.g., `my_agent_bot`)
6. Copy the HTTP API token (looks like `123456:ABC-DEF1234`)

### Step 5: Configure Your Provider

I recommend **DeepSeek** for daily use — it's $0.14/M input tokens vs OpenAI's $2.50/M. For complex reasoning tasks, switch to Claude.

```bash
hermes config set provider deepseek
hermes config set api_key dv3-xxxxxxxxx  # Your key
```

### Step 6: Test Your Agent

```bash
hermes run "What time is it in Istanbul right now?"
```

Your agent should respond with the current time. If it does — congratulations, you have an autonomous AI agent.

## Verification

```bash
hermes config get > /tmp/hermes-config.yaml
cat /tmp/hermes-config.yaml
```

This should show your provider, model, and Telegram settings.

## Next Steps

Your agent can now:
- Answer questions
- Run terminal commands (when you give it permission)
- Send Telegram messages

In Chapter 3, we'll give it real power — MCP servers that let it browse the web, read files, and think systematically.

## Key Files

| File | Purpose |
|------|---------|
| `~/.hermes/config.yaml` | Main configuration |
| `~/.hermes/memory/` | Persistent memory store |
| `~/.hermes/skills/` | Your agent's skill library |
| `~/.hermes/cron/` | Scheduled tasks |

## Troubleshooting

**"hermes: command not found"**
→ Make sure `~/.local/bin` is in your PATH: `export PATH=$PATH:~/.local/bin`

**"Error: Provider API key not found"**
→ Set it explicitly: `hermes config set api_key YOUR_KEY`

**"Telegram: not connected"**
→ Check your bot token: `hermes config get telegram_token`
