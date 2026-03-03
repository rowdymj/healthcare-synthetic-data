"""
Healthcare Sandbox — MCP Server
================================
Exposes all 18 healthcare agent tools via Model Context Protocol.

Usage (stdio — Claude Desktop / Cursor):
    python3 mcp_server.py

Usage (SSE — Cowork / remote clients):
    python3 mcp_server.py --sse [--port 8080]
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("healthcare-mcp")

sys.path.insert(0, str(Path(__file__).parent))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from api_server import create_api

TOOLS_PATH = Path(__file__).parent / "tools" / "tool_schemas.json"
with open(TOOLS_PATH) as f:
    tool_schemas = json.load(f)

mcp_tools = []
for t in tool_schemas["anthropic_tools"]:
    mcp_tools.append(Tool(
        name=t["name"],
        description=t["description"],
        inputSchema=t["input_schema"],
    ))

api = create_api()

def _log_startup():
    backend = "SQLite" if hasattr(api, "db_path") else "In-memory JSON"
    log.info("=" * 60)
    log.info("Healthcare Sandbox MCP Server")
    log.info("=" * 60)
    log.info(f"Backend: {backend}")
    log.info(f"Tools loaded: {len(mcp_tools)}")
    counts = {}
    for attr in ["members", "medical_claims", "providers", "plans",
                 "pharmacy_claims", "authorizations", "call_logs"]:
        try:
            data = getattr(api, attr, [])
            counts[attr] = len(data) if data else 0
        except Exception:
            counts[attr] = "?"
    for name, count in counts.items():
        log.info(f"  {name}: {count:,}" if isinstance(count, int) else f"  {name}: {count}")
    log.info(f"Tool list: {', '.join(t.name for t in mcp_tools)}")
    log.info("Ready for connections.")

_log_startup()

server = Server("healthcare-sandbox")

@server.list_tools()
async def list_tools():
    return mcp_tools

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    start = time.monotonic()
    log.info(f"CALL {name}({json.dumps(arguments, default=str)})")
    try:
        result = api.execute_tool(name, arguments)
    except Exception as e:
        elapsed = (time.monotonic() - start) * 1000
        log.error(f"FAIL {name} ({elapsed:.0f}ms): {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e), "tool": name}))]
    elapsed = (time.monotonic() - start) * 1000
    has_error = isinstance(result, dict) and "error" in result
    level = logging.WARNING if has_error else logging.INFO
    log.log(level, f"{'WARN' if has_error else 'OK  '} {name} ({elapsed:.0f}ms)")
    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

async def run_stdio():
    log.info("Transport: stdio")
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())

async def run_sse(port: int):
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.responses import Response
    from starlette.routing import Route, Mount
    import uvicorn
    sse = SseServerTransport("/messages/")
    async def handle_sse(request):
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await server.run(streams[0], streams[1], server.create_initialization_options())
        return Response()
    starlette_app = Starlette(routes=[
        Route("/sse", endpoint=handle_sse),
        Mount("/messages/", app=sse.handle_post_message),
    ])
    log.info(f"Transport: SSE on port {port}")
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=port, log_level="warning")
    srv = uvicorn.Server(config)
    await srv.serve()

if __name__ == "__main__":
    import asyncio
    parser = argparse.ArgumentParser(description="Healthcare Sandbox MCP Server")
    parser.add_argument("--sse", action="store_true", help="Use SSE transport instead of stdio")
    parser.add_argument("--port", type=int, default=8080, help="Port for SSE transport (default: 8080)")
    args = parser.parse_args()
    if args.sse:
        asyncio.run(run_sse(args.port))
    else:
        asyncio.run(run_stdio())
