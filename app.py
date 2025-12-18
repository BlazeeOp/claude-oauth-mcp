from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from mcp.protocol import handle_mcp
from auth.firebase import verify_firebase_token

# 🔹 APP MUST BE DEFINED FIRST
app = FastAPI()

# =========================================================
# 1️⃣ MCP METADATA (CLAUDE READS THIS FIRST)
# =========================================================
@app.get("/.well-known/mcp.json", include_in_schema=False)
@app.get("/well-known/mcp.json", include_in_schema=False)  # fallback
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
# 3️⃣ AUTH CALLBACK (CLAUDE + DEBUG FRIENDLY)
# =========================================================
@app.post("/auth/callback", include_in_schema=False)
async def auth_callback(payload: dict):
    token = payload.get("idToken")
    if not token:
        return HTMLResponse("<h3>Missing idToken</h3>", status_code=400)

    # Verify Firebase token
    verify_firebase_token(token)

    # IMPORTANT:
    # - Shows token for manual testing
    # - Sends postMessage Claude expects
    # - Does NOT auto-close so you can copy token
    return HTMLResponse(f"""
    <html>
      <body>
        <h2>ACCESS TOKEN (copy this for testing)</h2>
        <pre style="white-space: break-all;">{token}</pre>

        <script>
          window.opener?.postMessage(
            {{
              type: "mcp-auth-success",
              access_token: "{token}",
              token_type: "bearer"
            }},
            "*"
          );
        </script>

        <p>You may close this window after copying the token.</p>
      </body>
    </html>
    """)



@app.get("/auth/debug", include_in_schema=False)
def auth_debug():
    return HTMLResponse("""
    <html>
      <body>
        <h2>Finalizing login…</h2>
        <script>
          const token = sessionStorage.getItem("idToken");
          fetch("/auth/callback", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ idToken: token })
          })
          .then(res => res.text())
          .then(html => {
            document.open();
            document.write(html);
            document.close();
          });
        </script>
      </body>
    </html>
    """)






# =========================================================
# 4️⃣ MCP ENDPOINT
# =========================================================
@app.post("/mcp", include_in_schema=False)
async def mcp_endpoint(request: Request):
    return await handle_mcp(request)
