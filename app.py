from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from mcp.protocol import handle_mcp
from auth.firebase import verify_firebase_token

app = FastAPI()

# 1️⃣ MCP METADATA (CLAUDE READS THIS FIRST)
@app.get("/.well-known/mcp.json")
def mcp_metadata():
    return JSONResponse({
        "name": "Math MCP",
        "version": "1.0.0",
        "auth": {
            "type": "oauth",
            "authorization_url": "/auth/start"
        },
        "mcp": {
            "transport": "streamable-http",
            "endpoint": "/mcp"
        }
    })

# 2️⃣ AUTH FLOW
@app.get("/auth/start")
def auth_start():
    return RedirectResponse("/auth/login")

@app.get("/auth/login")
def auth_login():
    with open("frontend/login.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())

@app.post("/auth/callback")
async def auth_callback(payload: dict):
    token = payload["idToken"]
    verify_firebase_token(token)

    return {
        "access_token": token,
        "token_type": "bearer"
    }

# 3️⃣ MCP ENDPOINT
@app.post("/mcp")
async def mcp_endpoint(request: Request):
    return await handle_mcp(request)
