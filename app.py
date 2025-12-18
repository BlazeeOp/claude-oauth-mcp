from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.protocol import handle_mcp
from auth.firebase import verify_firebase_token
import logging

# =========================================================
# CONFIG
# =========================================================
BASE_URL = "https://claude-oauth-mcp-production.up.railway.app"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
# APP INITIALIZATION
# =========================================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================
# 1️⃣ MCP METADATA (CLAUDE READS THIS FIRST)
# =========================================================
@app.get("/.well-known/mcp.json", include_in_schema=False)
@app.get("/well-known/mcp.json", include_in_schema=False)
def mcp_metadata():
    logger.info("MCP metadata requested")
    return JSONResponse({
        "name": "Math MCP",
        "version": "1.0.0",
        "auth": {
            "type": "oauth",
            "authorization_url": f"{BASE_URL}/auth/start"
        },
        "mcp": {
            "transport": "streamable-http",
            "endpoint": f"{BASE_URL}/mcp"
        }
    })


# =========================================================
# 2️⃣ AUTH FLOW
# =========================================================
@app.get("/auth/start", include_in_schema=False)
def auth_start():
    logger.info("Auth start requested")
    return RedirectResponse("/auth/login")


@app.get("/auth/login", include_in_schema=False)
def auth_login():
    logger.info("Login page requested")
    with open("frontend/login.html", encoding="utf-8") as f:
        return HTMLResponse(f.read())


# =========================================================
# 3️⃣ AUTH CALLBACK (CLAUDE PRODUCTION MODE)
# =========================================================
@app.post("/auth/callback", include_in_schema=False)
async def auth_callback(payload: dict):
    logger.info("Auth callback received")

    token = payload.get("idToken")
    if not token:
        logger.error("Missing idToken")
        return HTMLResponse("Missing idToken", status_code=400)

    try:
        verify_firebase_token(token)
        logger.info("Token verified successfully")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return HTMLResponse("Invalid token", status_code=401)

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
# 3️⃣.5 OAUTH DISCOVERY (REQUIRED BY CLAUDE)
# =========================================================
@app.get("/.well-known/oauth-authorization-server", include_in_schema=False)
def oauth_authorization_server():
    return JSONResponse({
        "issuer": BASE_URL,
        "authorization_endpoint": f"{BASE_URL}/auth/start",
        "token_endpoint": f"{BASE_URL}/auth/token",
        "response_types_supported": ["token"],
        "grant_types_supported": ["implicit"],
        "token_endpoint_auth_methods_supported": ["none"]
    })


@app.get("/.well-known/oauth-protected-resource", include_in_schema=False)
def oauth_protected_resource():
    return JSONResponse({
        "resource": BASE_URL,
        "authorization_servers": [BASE_URL]
    })


@app.post("/auth/token", include_in_schema=False)
async def oauth_token_stub():
    # Claude probes this endpoint — it must exist
    return JSONResponse(
        {"error": "unsupported_grant_type"},
        status_code=400
    )


# =========================================================
# 4️⃣ MCP ENDPOINT
# =========================================================
@app.post("/mcp", include_in_schema=False)
async def mcp_endpoint(request: Request):
    logger.info(
        f"MCP request received, auth={request.headers.get('authorization', 'none')[:20]}..."
    )
    return await handle_mcp(request)


# =========================================================
# 5️⃣ HEALTH CHECK
# =========================================================
@app.get("/", include_in_schema=False)
def health_check():
    return {"status": "ok", "service": "Math MCP Server"}
