"""Main module."""

import uvicorn
from importlib.metadata import version
from fastapi import FastAPI


app = FastAPI(
    title="OpenAPI2Callables Test Server",
    description="",
    version=version("openapi2callables"),
    docs_url="/",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.get("/pirate")
def pirate_endpoint() -> str:
    """Pirate endpoint. Simplest possible endpoint; no inputs, only string response"""
    return "Arr, matey! Welcome to the pirate endpoint!"


@app.get("/pirate/{name}")
def pirate_endpoint_name(name: str) -> str:
    """Pirate endpoint. Simplest possible endpoint; URL input, only string response"""
    return f"Arr, matey! Welcome to the pirate endpoint, {name}!"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", reload=True, debug=True, port=8000)
