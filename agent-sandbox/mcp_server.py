"""
Healthcare Sandbox — MCP Server
================================
Exposes all 18 healthcare agent tools via Model Context Protocol.

Usage:
    python3 mcp_server.py

Or add to Claude Desktop config (Settings > Developer > Edit Config):

    {
      "mcpServers": {
        "healthcare-sandbox": {
          "command": "python3",
          "args": ["/absolute/path/to/agent-sandbox/mcp_server.py"]
        }
      }
    }

Then restart Claude Desktop. All 18 tools appear automatically.
"""

import json
import sys
from pathlib import Path

# Ensure we can import api_server from the same directory
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from api_server import HealthcareAPI

# ── Load tool schemas ────────────────────────────────────────────────

TOOLS_PATH = Path(__file__).parent / "tools" / "tool_schemas.json"
with open(TOOLS_PATH) as f:
    tool_schemas = json.load(f)

# Build MCP Tool objects from our existing Anthropic-format schemas
mcp_tools = []
for t in tool_schemas["anthropic_tools"]:
    mcp_tools.append(Tool(
        name=t["name"],
        description=t["description"],
        inputSchema=t["input_schema"],
    ))

# ── Initialize API ───────────────────────────────────────────────────

api = HealthcareAPI()

# ── MCP Server ───────────────────────────────────────────────────────

server = Server("healthcare-sandbox")


@server.list_tools()
async def list_tools():
    """Advertise all 18 healthcare tools to any MCP client."""
    return mcp_tools


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Route tool calls to the healthcare API query engine."""
    try:
        result = api.execute_tool(name, arguments)
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]

    # Format result as readable JSON for the model
    return [TextContent(
        type="text",
        text=json.dumps(result, indent=2, default=str),
    )]


# ── Run ──────────────────────────────────────────────────────────────

async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
