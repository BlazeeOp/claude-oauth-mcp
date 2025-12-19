from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
import os, logging
from mcp.protocol import handle_mcp
from auth.github import (
    get_github_auth_url,
    exchange_code_for_token,
    get_github_user
)

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# =====================================================
# MCP METADATA
# =====================================================
@app.get("/.well-known/mcp.json", include_in_schema=False)
def mcp_metadata():
    return {
        "name": "Claude Math MCP",
        "version": "1.0.0",
        "auth": {
            "type": "oauth",
            "authorization_url": f"{BASE_URL}/auth/github/start"
        },
        "mcp": {
            "transport": "streamable-http",
            "endpoint": "/mcp"
        }
    }

# =====================================================
# OAUTH DISCOVERY (Claude probes these)
# =====================================================
@app.get("/.well-known/oauth-authorization-server", include_in_schema=False)
def oauth_authorization_server():
    return {
        "issuer": BASE_URL,
        "authorization_endpoint": f"{BASE_URL}/auth/github/start",
        "token_endpoint": f"{BASE_URL}/auth/token",
        "response_types_supported": ["token"],
        "grant_types_supported": ["implicit"],
        "token_endpoint_auth_methods_supported": ["none"]
    }

@app.get("/.well-known/oauth-protected-resource", include_in_schema=False)
def oauth_protected_resource():
    return {
        "resource": f"{BASE_URL}/mcp",
        "authorization_servers": [BASE_URL]
    }

@app.post("/auth/token", include_in_schema=False)
async def token_stub():
    return JSONResponse({"error": "unsupported_grant_type"}, status_code=400)

# =====================================================
# GITHUB OAUTH FLOW
# =====================================================
@app.get("/auth/github/start", include_in_schema=False)
def github_start():
    return RedirectResponse(get_github_auth_url())

@app.get("/auth/github/callback", include_in_schema=False)
async def github_callback(code: str):
    token = await exchange_code_for_token(code)
    user = await get_github_user(token)

    return JSONResponse({
        "access_token": token,
        "token_type": "bearer",
        "user": user
    })

# =====================================================
# MCP ENDPOINT
# =====================================================
@app.post("/mcp", include_in_schema=False)
async def mcp_endpoint(request: Request):
    return await handle_mcp(request)

@app.get("/", include_in_schema=False)
def health():
    return {"status": "ok"}
