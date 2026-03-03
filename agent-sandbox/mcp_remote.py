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
