# Chapter 3: Powering Up — MCP Servers

## Concept

An AI agent without tools is just a fancy autocomplete. **MCP (Model Context Protocol)** is the standard way to give your agent real capabilities.

Think of MCP servers as **plugins** for your agent:

| MCP Server | What It Does | Why You Need It |
|------------|-------------|-----------------|
| `time` | Provides accurate date/time | Your agent needs to know what "now" means |
| `fetch` | Downloads web pages | Research, scraping, monitoring |
| `filesystem` | Reads/writes files | Let your agent work with your data |
| `search` | Web search (Tavily/Google) | Current information retrieval |
| `sequential-thinking` | Complex reasoning | Break down hard problems |

## Implementation

### Step 1: Enable Built-in MCP Servers

Edit `~/.hermes/config.yaml`:

```yaml
mcp_servers:
  time:
    enabled: true
  fetch:
    enabled: true
  filesystem:
    enabled: true
    allowed_directories:
      - /home/your-user
      - /opt
  sequential-thinking:
    enabled: true
```

### Step 2: Install Web Search (Tavily)

Tavily gives you 1,000 free searches/month. Better than Google Search API.

```bash
# Get your API key from https://tavily.com
hermes config set web_backend tavily
hermes config set web_search_api_key tvly-xxxxxxxxxx
```

### Step 3: Add a Custom MCP Server

Let's add a database connection:

```bash
mkdir -p ~/.hermes/mcp-servers
cat > ~/.hermes/mcp-servers/my-db-server.py << 'EOF'
from mcp.server import FastMCP
import sqlite3

mcp = FastMCP("Database Server")

@mcp.tool()
def query_database(sql: str) -> list:
    """Run a SQL query on the local database"""
    conn = sqlite3.connect("/home/user/data.db")
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    mcp.run()
EOF

pip install mcp  # Install the MCP SDK
```

Then register it in `config.yaml`:

```yaml
mcp_servers:
  my-db:
    command: python3
    args:
      - /home/user/.hermes/mcp-servers/my-db-server.py
```

### Step 4: Test Your MCP Servers

```bash
hermes run "Search the web for 'AI agent trends 2026' and save the results to a file"
```

Your agent will:
1. Use Tavily to search the web
2. Read the search results
3. Use the filesystem tool to save them

## Verification

```bash
hermes tools
```

This lists all active MCP servers and their tools. You should see:
- `tavily_search`, `tavily_extract`
- `mcp_filesystem_read_file`, `mcp_filesystem_write_file`
- `mcp_sequential_thinking`

## The MCP Ecosystem

Here are production MCP servers I use daily:

| Server | Use | Cost |
|--------|-----|------|
| **Tavily** | Web search | Free tier: 1,000/mo |
| **NotebookLM** | Document intelligence | Free with Google account |
| **Git** | Code operations | Free |
| **Firecrawl** | Full website crawl | $19/mo (or Tavily crawl) |
| **n8n** | Workflow automation | Self-hosted (free) |

## Next Steps

Your agent now has real tools. In Chapter 4, we'll teach it specialized skills and create reusable workflows.

## Pro Tip

Start with just 3 MCP servers: `time`, `fetch`, and `tavily`. Add more as you need them. Every MCP server adds context overhead — too many and your agent gets slow and expensive.
