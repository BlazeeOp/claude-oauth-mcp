from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from mcp.protocol import handle_mcp
from auth.firebase import verify_firebase_token
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================================
# APP INITIALIZATION
# =========================================================
app = FastAPI()

# Add CORS middleware
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
            "authorization_url": "https://claude-oauth-mcp-production.up.railway.app/auth/start"
        },
        "mcp": {
            "transport": "streamable-http",
            "endpoint": "https://claude-oauth-mcp-production.up.railway.app/mcp"
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
        logger.error("No token in callback")
        return HTMLResponse("Missing token", status_code=400)

    try:
        verify_firebase_token(token)
        logger.info("Token verified successfully")
    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return HTMLResponse(f"Token verification failed: {str(e)}", status_code=401)

    return HTMLResponse(f"""
    <html>
      <body>
        <script>
          // 🔐 Send token back to Claude
          window.opener?.postMessage(
            {{
              type: "mcp-auth-success",
              access_token: "{token}",
              token_type: "bearer"
            }},
            "*"
          );

          // 🔴 CLOSE THE WINDOW (THIS IS CRITICAL)
          setTimeout(() => window.close(), 1000);
        </script>

        <p>Authentication successful. This window will close automatically.</p>
      </body>
    </html>
    """)


# =========================================================
# 4️⃣ MCP ENDPOINT
# =========================================================
@app.post("/mcp", include_in_schema=False)
async def mcp_endpoint(request: Request):
    logger.info(f"MCP request received: {request.headers.get('authorization', 'No auth')[:20]}...")
    try:
        body = await request.json()
        logger.info(f"MCP method: {body.get('method')}")
        response = await handle_mcp(request)
        return response
    except Exception as e:
        logger.error(f"MCP error: {e}")
        raise


# =========================================================
# 5️⃣ HEALTH CHECK
# =========================================================
@app.get("/", include_in_schema=False)
def health_check():
    return {"status": "ok", "service": "Math MCP Server"}


# =========================================================
# 6️⃣ DEBUG ENDPOINT (Remove in production)
# =========================================================
@app.get("/debug/test-auth", include_in_schema=False)
async def test_auth(token: str):
    """Test endpoint to verify Firebase token"""
    try:
        result = verify_firebase_token(token)
        return {"status": "valid", "user": result}
    except Exception as e:
        return {"status": "invalid", "error": str(e)}