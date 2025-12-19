def add(a: float, b: float):
    return a + b

def subtract(a: float, b: float):
    return a - b

def multiply(a: float, b: float):
    return a * b

def divide(a: float, b: float):
    if b == 0:
        raise ValueError("Division by zero")
    return a / b
