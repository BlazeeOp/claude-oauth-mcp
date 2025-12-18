from fastapi import Request
from fastapi.responses import JSONResponse
from auth.firebase import verify_firebase_token
from mcp.tools import TOOLS

async def handle_mcp(request: Request):
    try:
        # 1️⃣ AUTH CHECK
        auth_header = request.headers.get("authorization")
        if not auth_header:
            return JSONResponse({"error": "unauthorized"}, status_code=401)

        token = auth_header.replace("Bearer ", "")
        try:
            verify_firebase_token(token)
        except Exception as e:
            return JSONResponse({"error": f"Invalid token: {str(e)}"}, status_code=401)

        # 2️⃣ READ MCP REQUEST
        payload = await request.json()
        method = payload.get("method")
        rpc_id = payload.get("id")

        # 3️⃣ INITIALIZE (Required by MCP)
        if method == "initialize":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": "Math MCP",
                        "version": "1.0.0"
                    }
                }
            })

        # 4️⃣ LIST TOOLS
        if method == "tools/list":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "tools": [
                        {
                            "name": name,
                            "description": f"Performs {name} operation on two numbers",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "a": {"type": "number", "description": "First number"},
                                    "b": {"type": "number", "description": "Second number"}
                                },
                                "required": ["a", "b"]
                            }
                        }
                        for name in TOOLS.keys()
                    ]
                }
            })

        # 5️⃣ CALL TOOL
        if method == "tools/call":
            tool_name = payload["params"]["name"]
            args = payload["params"]["arguments"]

            if tool_name not in TOOLS:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {
                        "code": -32601,
                        "message": f"Tool '{tool_name}' not found"
                    }
                })

            result = TOOLS[tool_name](**args)

            # Check if there's an error
            if "error" in result:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result["error"]
                            }
                        ],
                        "isError": True
                    }
                })

            # Success response with proper content structure
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": str(result["result"])
                        }
                    ]
                }
            })

        # Unknown method
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": rpc_id,
            "error": {
                "code": -32601,
                "message": f"Method '{method}' not found"
            }
        }, status_code=400)

    except Exception as e:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": payload.get("id") if "payload" in locals() else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }, status_code=500)