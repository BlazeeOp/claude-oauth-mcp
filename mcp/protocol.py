from fastapi import Request
from mcp.tools import add, subtract, multiply, divide

TOOLS = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
}

async def handle_mcp(request: Request):
    body = await request.json()

    method = body.get("method")
    params = body.get("params", {})
    _id = body.get("id")

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": _id,
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
                    for name in TOOLS
                ]
            }
        }

    if method == "tools/call":
        name = params.get("name")
        args = params.get("arguments", {})
        result = TOOLS[name](**args)
        return {
            "jsonrpc": "2.0",
            "id": _id,
            "result": result
        }

    return {
        "jsonrpc": "2.0",
        "id": _id,
        "error": {"code": -32601, "message": "Method not found"}
    }
