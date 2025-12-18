def add(a: int, b: int):
    return {"result": a + b}

def subtract(a: int, b: int):
    return {"result": a - b}

def multiply(a: int, b: int):
    return {"result": a * b}

def divide(a: int, b: int):
    if b == 0:
        return {"error": "Division by zero"}
    return {"result": a / b}

TOOLS = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide
}
