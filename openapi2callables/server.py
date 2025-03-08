"""Main module."""

from importlib.metadata import version
from typing import List, Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="OpenAPI2Callables Test Server",
    description="",
    version=version("openapi2callables"),
    docs_url="/",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.get("/get_pirate")
def pirate_endpoint() -> str:
    """Pirate endpoint. Simplest possible endpoint; no inputs, only string response"""
    return "Arr, matey! Welcome to the pirate endpoint!"


@app.get("/urlparam_pirate/{name}")
def pirate_endpoint_name(name: str) -> str:
    """Pirate endpoint. Simplest possible endpoint; URL input, only string response"""
    return f"Arr, matey! Welcome to the pirate endpoint, {name}!"


class Pirate(BaseModel):
    name: str
    age: Optional[int] = None
    ship: Optional[str] = None


pirates_db = []


@app.post("/post_pirate")
def pirate_endpoint_body(pirate: Pirate) -> str:
    """Pirate endpoint. Simplest possible endpoint; Post Body input, only string response"""
    return f"Arr, matey! Welcome to the pirate endpoint, {pirate.name}!"


@app.put("/update_pirate/{name}")
def update_pirate(name: str, pirate: Pirate) -> str:
    """Update a pirate's information."""
    for p in pirates_db:
        if p.name == name:
            p.age = pirate.age
            p.ship = pirate.ship
            return f"Pirate {name} updated!"
    return f"Pirate {name} not found!"


@app.delete("/delete_pirate/{name}")
def delete_pirate(name: str) -> str:
    """Delete a pirate."""
    global pirates_db
    pirates_db = [p for p in pirates_db if p.name != name]
    return f"Pirate {name} deleted!"


@app.get("/search_pirates")
def search_pirates(ship: str) -> List[Pirate]:
    """Search pirates by ship."""
    return [p for p in pirates_db if p.ship == ship]


@app.get("/get_pirates")
def get_pirates() -> List[Pirate]:
    """Get all pirates."""
    return pirates_db


@app.post("/add_pirate")
def add_pirate(pirate: Pirate) -> str:
    """Add a new pirate."""
    pirates_db.append(pirate)
    return f"Pirate {pirate.name} added!"


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", reload=True, debug=True, port=8000)
