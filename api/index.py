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
