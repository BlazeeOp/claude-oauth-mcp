from fastapi import Request
from fastapi.responses import JSONResponse
from auth.firebase import verify_firebase_token
from mcp.tools import TOOLS

async def handle_mcp(request: Request):
    # 1️⃣ AUTH CHECK
    auth_header = request.headers.get("authorization")
    if not auth_header:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    token = auth_header.replace("Bearer ", "")
    verify_firebase_token(token)

    # 2️⃣ READ MCP REQUEST
    payload = await request.json()
    method = payload.get("method")
    rpc_id = payload.get("id")

    # 3️⃣ LIST TOOLS
    if method == "tools/list":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "tools": [
                    {
                        "name": name,
                        "description": f"{name} operation",
                        "input_schema": {
                            "type": "object",
                            "properties": {
                                "a": {"type": "number"},
                                "b": {"type": "number"}
                            },
                            "required": ["a", "b"]
                        }
                    }
                    for name in TOOLS.keys()
                ]
            }
        })

    # 4️⃣ CALL TOOL
    if method == "tools/call":
        name = payload["params"]["name"]
        args = payload["params"]["arguments"]

        result = TOOLS[name](**args)

        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": result
        })

    return JSONResponse({"error": "unknown method"}, status_code=400)
