"""Main module."""
import uvicorn
from fastapi import FastAPI


app = FastAPI()


@app.get("/pirate")
def pirate_endpoint() -> str:
    """Pirate endpoint. Simplest possible endpoint; no inputs, only string response"""
    return "Arr, matey! Welcome to the pirate endpoint!"


@app.get("/pirate/{name}")
def pirate_endpoint(name: str) -> str:
    """Pirate endpoint. Simplest possible endpoint; URL input, only string response"""
    return f"Arr, matey! Welcome to the pirate endpoint, {name}!"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
