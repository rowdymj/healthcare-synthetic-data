# Vercel Deployment Design

**Date**: 2026-03-03
**Status**: Approved

## Goal

Deploy the healthcare synthetic data platform to Vercel so teammates can:
1. Hit the REST API over HTTPS
2. Connect Claude Desktop / Cursor to a shared MCP SSE endpoint via a local proxy

## Architecture

```
Teammate's machine                         Vercel
+---------------------+           +----------------------+
| Claude Desktop      |           |  api/index.py        |
|   <-> stdio         |           |  (FastAPI via ASGI)  |
| mcp_remote.py ------+-- HTTPS --+> /sse    (MCP SSE)  |
| (local proxy)       |           |  /tool   (REST)      |
+---------------------+           |  /members (REST)     |
                                  |  ...23 endpoints     |
                                  |                      |
                                  |  Loads data/json/*   |
                                  |  on cold start       |
                                  +----------------------+
```

## Decisions

- **Backend**: JSON in-memory (stateless, fits serverless model)
- **Auth**: API key via `API_KEY` env var, checked in `Authorization: Bearer` header
- **MCP access**: Teammates run `mcp_remote.py` locally (stdio proxy -> Vercel SSE)
- **Approach**: Single Vercel Python serverless function wrapping existing FastAPI app

## Files

| File | Purpose |
|------|---------|
| `vercel.json` | Route all requests to Python serverless function |
| `api/index.py` | ASGI entry point with API key middleware |
| `requirements.txt` (root) | Python deps for Vercel runtime |
| `agent-sandbox/mcp_remote.py` | Local stdio-to-SSE proxy for teammates |
| `agent-sandbox/api_server.py` | Patch: read DATA_DIR from env var |
| `TEAM-SETUP.md` | Teammate onboarding guide |

## Constraints

- Cold starts ~2-5s (loading 33MB JSON)
- SSE has ~30s timeout on Vercel serverless (fine for tool calls)
- Write tools (create_case_note, etc.) don't persist across invocations
- All data is synthetic, so public-ish access is acceptable with API key
