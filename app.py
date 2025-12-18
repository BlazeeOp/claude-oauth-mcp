from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from mcp.protocol import handle_mcp
from auth.firebase import verify_firebase_token

# =========================================================
# APP INITIALIZATION
# =========================================================
app = FastAPI()


# =========================================================
# 1️⃣ MCP METADATA (CLAUDE READS THIS FIRST)
# =========================================================
@app.get("/.well-known/mcp.json", include_in_schema=False)
@app.get("/well-known/mcp.json", include_in_schema=False)  # infra fallback
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


# =========================================================
# 2️⃣ AUTH FLOW
# =========================================================
@app.get("/auth/start", include_in_schema=False)
def auth_start():
    return RedirectResponse("/auth/login")


@app.get("/auth/login", include_in_schema=False)
def auth_login():
    with open("frontend/login.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


# =========================================================
# 3️⃣ AUTH CALLBACK (CLAUDE PRODUCTION MODE)
# =========================================================
@app.post("/auth/callback", include_in_schema=False)
async def auth_callback(payload: dict):
    token = payload.get("idToken")
    if not token:
        return HTMLResponse("<h3>Missing idToken</h3>", status_code=400)

    # Verify Firebase ID token
    verify_firebase_token(token)

    # REQUIRED: send token to Claude via postMessage and close popup
    return HTMLResponse(f"""
    <html>
      <body>
        <script>
          window.opener?.postMessage(
            {{
              type: "mcp-auth-success",
              access_token: "{token}",
              token_type: "bearer"
            }},
            "*"
          );
          window.close();
        </script>
        <p>Authentication successful. You may close this window.</p>
      </body>
    </html>
    """)


# =========================================================
# 4️⃣ MCP ENDPOINT
# =========================================================
@app.post("/mcp", include_in_schema=False)
async def mcp_endpoint(request: Request):
    return await handle_mcp(request)
