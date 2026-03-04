# Team Setup Guide

Connect your Claude Desktop (or Cursor) to the shared Healthcare Sandbox deployment.

## Prerequisites

- Python 3.10+ with the MCP SDK installed
- Access to the team's API key (ask the project owner)

Install the MCP SDK if you haven't:

```bash
pip install "mcp[cli]"
```

## Quick Start (2 minutes)

### 1. Clone the repo

```bash
git clone https://github.com/rowdymj/healthcare-synthetic-data.git
cd healthcare-synthetic-data
```

### 2. Configure Claude Desktop

Edit your Claude Desktop config:

- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

Add this MCP server entry:

```json
{
  "mcpServers": {
    "healthcare-sandbox": {
      "command": "python3",
      "args": ["/absolute/path/to/healthcare-synthetic-data/agent-sandbox/mcp_remote.py"],
      "env": {
        "HEALTHCARE_API_URL": "https://your-app.vercel.app",
        "HEALTHCARE_API_KEY": "your-api-key"
      }
    }
  }
}
```

Replace:
- `/absolute/path/to/` with the actual path where you cloned the repo
- `https://your-app.vercel.app` with the deployment URL
- `your-api-key` with the team API key

### 3. Restart Claude Desktop

Quit and reopen Claude Desktop. You should see "healthcare-sandbox" in the MCP tools list.

### 4. Test it

Ask Claude: "Look up member Smith using the healthcare sandbox"

You should see Claude call the `lookup_member` tool and return results.

## Direct REST API Access

You can also hit the API directly:

```bash
# Health check
curl https://your-app.vercel.app/

# Search members (with auth)
curl -H "Authorization: Bearer your-api-key" \
  "https://your-app.vercel.app/api/members?last_name=Smith"

# Execute any tool
curl -X POST -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"tool_name": "lookup_member", "params": {"last_name": "Smith"}}' \
  https://your-app.vercel.app/tool
```

Interactive docs: `https://your-app.vercel.app/docs`

## Troubleshooting

**"HEALTHCARE_API_URL environment variable is required"**
→ Your Claude Desktop config is missing the `env` block. See step 2.

**"Invalid or missing API key" (401)**
→ Check that `HEALTHCARE_API_KEY` matches the deployed API key.

**Tools not showing up in Claude Desktop**
→ Make sure `python3` resolves to Python 3.10+ with the MCP SDK installed. Try `python3 -c "import mcp; print('OK')"`.

**Timeout errors**
→ First request after idle may take 2-5s (cold start). Retry once.

## What's Available

18 healthcare agent tools including:
- `lookup_member` — search members by ID, name, DOB
- `search_claims` — filter medical claims by status, date, provider
- `search_pharmacy_claims` — prescription history and formulary
- `check_benefits` — plan coverage for service categories
- `search_providers` — find providers by specialty, location
- `get_claim_detail` — full claim with line items
- `search_knowledge_base` — plan policies, FAQs, business rules

All data is synthetic. No real PHI/PII.
