
from fastapi import FastAPI

app = FastAPI(
    title="My First FastAPI App",
    description="A simple application with two endpoints",
    version="1.0.0"
)

# Endpoint 1: Root
@app.get("/")
def home():
    return {
        "message": "Welcome to my FastAPI application!"
    }

# Endpoint 2: Path parameter
@app.get("/greet/{name}")
def greet(name: str):
    return {
        "message": f"Hello, {name}! Welcome to FastAPI."
    }