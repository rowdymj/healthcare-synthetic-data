# Vercel Deployment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy the Healthcare Sandbox API to Vercel so teammates can access REST endpoints and connect Claude Desktop via a local MCP proxy.

**Architecture:** Single Vercel Python serverless function wrapping the existing FastAPI app. JSON in-memory backend (stateless). API key auth via env var. Teammates run `mcp_remote.py` locally which speaks MCP stdio to Claude Desktop and forwards tool calls as HTTP POSTs to the Vercel `/tool` endpoint.

**Tech Stack:** Vercel Python runtime, FastAPI (existing), urllib (stdlib for remote proxy), MCP SDK (for local proxy only)

---

### Task 1: Patch api_server.py to support DATA_DIR env var

**Files:**
- Modify: `agent-sandbox/api_server.py:21`

**Step 1: Add os import and env var override**

The file already imports `os` (line 15). Change line 21 from:

```python
DATA_DIR = BASE_DIR / "data" / "json"
```

to:

```python
DATA_DIR = Path(os.environ["DATA_DIR"]) if "DATA_DIR" in os.environ else BASE_DIR / "data" / "json"
```

**Step 2: Verify existing behavior unchanged**

Run: `cd /Users/matthewjohnson/healthcare-synthetic-data && python3 agent-sandbox/api_server.py`
Expected: "Loaded: 2000 members, 13841 claims, 300 providers" and "All tools operational."

**Step 3: Verify env var override works**

Run: `DATA_DIR=/Users/matthewjohnson/healthcare-synthetic-data/data/json python3 agent-sandbox/api_server.py`
Expected: Same output — proves the env var path resolution works.

**Step 4: Commit**

```bash
git add agent-sandbox/api_server.py
git commit -m "feat: support DATA_DIR env var for Vercel deployment"
```

---

### Task 2: Create root-level requirements.txt

**Files:**
- Create: `requirements.txt`

**Step 1: Create the file**

```
fastapi>=0.104.0
uvicorn>=0.24.0
```

Note: MCP SDK is NOT needed on Vercel — only the REST API runs there. The MCP proxy runs locally on teammate machines.

**Step 2: Verify no conflict with agent-sandbox/requirements.txt**

Run: `cat agent-sandbox/requirements.txt`
Confirm it has the same deps (plus MCP comment). No conflict.

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat: add root requirements.txt for Vercel Python runtime"
```

---

### Task 3: Create vercel.json

**Files:**
- Create: `vercel.json`

**Step 1: Create the routing config**

```json
{
  "builds": [
    {
      "src": "api/index.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "api/index.py"
    }
  ]
}
```

This sends all traffic to the single Python serverless function.

**Step 2: Validate JSON syntax**

Run: `python3 -c "import json; json.load(open('vercel.json')); print('OK')"`
Expected: "OK"

**Step 3: Commit**

```bash
git add vercel.json
git commit -m "feat: add vercel.json routing config"
```

---

### Task 4: Create api/index.py serverless entry point

**Files:**
- Create: `api/index.py`

**Step 1: Create the directory and file**

```python
"""
Healthcare Sandbox — Vercel Serverless Entry Point
====================================================
Wraps the existing FastAPI app for Vercel's Python runtime.
Adds API key authentication via the API_KEY environment variable.

Set API_KEY in Vercel project settings to enable auth.
"""

import os
import sys
from pathlib import Path

from fastapi import Request
from fastapi.responses import JSONResponse

# Add agent-sandbox to Python path so server.py imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "agent-sandbox"))

from server import app

# ── API Key Middleware ─────────────────────────────────────────────

API_KEY = os.environ.get("API_KEY")

# Public paths that skip auth (health check + docs)
_PUBLIC_PATHS = frozenset({"/", "/docs", "/redoc", "/openapi.json"})


@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    if API_KEY and request.url.path not in _PUBLIC_PATHS:
        token = request.headers.get("Authorization", "")
        if not token.startswith("Bearer ") or token[7:] != API_KEY:
            return JSONResponse(
                status_code=401,
                content={"error": "Invalid or missing API key"},
            )
    return await call_next(request)
```

**Step 2: Verify the import chain works locally**

Run: `cd /Users/matthewjohnson/healthcare-synthetic-data && python3 -c "import sys; sys.path.insert(0, 'agent-sandbox'); from server import app; print(f'Routes: {len(app.routes)}')"`
Expected: "Routes: NN" (some positive number)

**Step 3: Commit**

```bash
git add api/index.py
git commit -m "feat: add Vercel serverless entry point with API key auth"
```

---

### Task 5: Create agent-sandbox/mcp_remote.py

**Files:**
- Create: `agent-sandbox/mcp_remote.py`

**Step 1: Create the remote proxy**

```python
"""
Healthcare Sandbox — Remote MCP Proxy
=======================================
Local stdio MCP server that proxies tool calls to a remote Healthcare API.
Teammates use this to connect Claude Desktop to the shared Vercel deployment.

Required env vars:
    HEALTHCARE_API_URL  — base URL (e.g. https://your-app.vercel.app)
    HEALTHCARE_API_KEY  — API key for the deployment

Usage:
    export HEALTHCARE_API_URL=https://your-app.vercel.app
    export HEALTHCARE_API_KEY=your-key
    python3 mcp_remote.py

Claude Desktop config (~/.claude/claude_desktop_config.json):
    {
        "mcpServers": {
            "healthcare-sandbox": {
                "command": "python3",
                "args": ["/absolute/path/to/agent-sandbox/mcp_remote.py"],
                "env": {
                    "HEALTHCARE_API_URL": "https://your-app.vercel.app",
                    "HEALTHCARE_API_KEY": "your-key"
                }
            }
        }
    }
"""

import asyncio
import json
import logging
import os
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("healthcare-mcp-remote")

sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# ── Configuration ─────────────────────────────────────────────────

API_URL = os.environ.get("HEALTHCARE_API_URL", "").rstrip("/")
API_KEY = os.environ.get("HEALTHCARE_API_KEY", "")

if not API_URL:
    log.error("Set HEALTHCARE_API_URL env var (e.g. https://your-app.vercel.app)")
    sys.exit(1)

# ── Load tool schemas from local repo ─────────────────────────────

TOOLS_PATH = Path(__file__).parent / "tools" / "tool_schemas.json"
with open(TOOLS_PATH) as f:
    tool_schemas = json.load(f)

mcp_tools = []
for t in tool_schemas["anthropic_tools"]:
    mcp_tools.append(
        Tool(
            name=t["name"],
            description=t["description"],
            inputSchema=t["input_schema"],
        )
    )

log.info(f"Remote proxy -> {API_URL}")
log.info(f"Tools loaded: {len(mcp_tools)}")
log.info(f"Auth: {'API key set' if API_KEY else 'no key (public)'}")

# ── MCP Server ────────────────────────────────────────────────────

server = Server("healthcare-sandbox-remote")


@server.list_tools()
async def list_tools():
    return mcp_tools


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    start = time.monotonic()
    log.info(f"CALL {name}({json.dumps(arguments, default=str)})")
    try:
        payload = json.dumps({"tool_name": name, "params": arguments}).encode()
        headers = {"Content-Type": "application/json"}
        if API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"
        req = urllib.request.Request(
            f"{API_URL}/tool", data=payload, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
        elapsed = (time.monotonic() - start) * 1000
        log.info(f"OK   {name} ({elapsed:.0f}ms)")
    except urllib.error.HTTPError as e:
        elapsed = (time.monotonic() - start) * 1000
        body = e.read().decode() if e.fp else str(e)
        log.error(f"FAIL {name}: HTTP {e.code} ({elapsed:.0f}ms)")
        result = {"error": f"Remote API error: HTTP {e.code}", "detail": body}
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        log.error(f"FAIL {name}: {e} ({elapsed:.0f}ms)")
        result = {"error": str(e)}
    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]


# ── Entry point ───────────────────────────────────────────────────


async def main():
    log.info("Transport: stdio (remote proxy)")
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Verify syntax**

Run: `python3 -c "import py_compile; py_compile.compile('agent-sandbox/mcp_remote.py', doraise=True); print('OK')"`
Expected: "OK"

**Step 3: Commit**

```bash
git add agent-sandbox/mcp_remote.py
git commit -m "feat: add MCP remote proxy for team Vercel access"
```

---

### Task 6: Create TEAM-SETUP.md

**Files:**
- Create: `TEAM-SETUP.md`

**Step 1: Write the guide**

```markdown
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
```

**Step 2: Commit**

```bash
git add TEAM-SETUP.md
git commit -m "docs: add team setup guide for Vercel deployment"
```

---

### Task 7: Final verification and combined commit

**Step 1: Check all files exist**

Run: `ls -la vercel.json api/index.py requirements.txt agent-sandbox/mcp_remote.py TEAM-SETUP.md`

**Step 2: Verify Python syntax on all new/modified files**

Run: `python3 -m py_compile api/index.py && python3 -m py_compile agent-sandbox/mcp_remote.py && python3 -m py_compile agent-sandbox/api_server.py && echo "All OK"`

**Step 3: Run existing CI checks**

Run: `python3 scripts/validate_data.py`
Expected: All checks pass (data integrity unchanged).

**Step 4: Verify the FastAPI app loads**

Run: `cd /Users/matthewjohnson/healthcare-synthetic-data && python3 -c "import sys; sys.path.insert(0, 'agent-sandbox'); from server import app; print(f'App OK — {len(app.routes)} routes')"`
