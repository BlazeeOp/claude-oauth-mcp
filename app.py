@app.post("/auth/callback", include_in_schema=False)
async def auth_callback(payload: dict):
    token = payload["idToken"]
    verify_firebase_token(token)

    return HTMLResponse(f"""
    <html>
      <body>
        <h2>ACCESS TOKEN (copy this)</h2>
        <pre style="white-space: break-all;">{token}</pre>

        <!-- TEMPORARILY DISABLED FOR TESTING -->
        <!--
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
        -->
      </body>
    </html>
    """)