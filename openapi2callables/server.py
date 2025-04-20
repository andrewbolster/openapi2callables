"""Main module."""

from datetime import date, datetime
from enum import Enum
from importlib.metadata import version
from typing import Dict, List, Optional, Union

import uvicorn
from fastapi import Body, Cookie, FastAPI, Header, HTTPException, Path, Query, status
from pydantic import BaseModel, EmailStr, Field

app = FastAPI(
    title="OpenAPI2Callables Test Server",
    description="A test server for OpenAPI2Callables with various endpoint types to test parsing capabilities",
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


# Enum for pirate ranks
class PirateRank(str, Enum):
    CAPTAIN = "captain"
    FIRST_MATE = "first_mate"
    QUARTERMASTER = "quartermaster"
    BOATSWAIN = "boatswain"
    GUNNER = "gunner"
    SAILOR = "sailor"


# Nested model for ship details
class Ship(BaseModel):
    name: str
    type: str = Field(..., description="Type of ship (e.g., Galleon, Frigate, Sloop)")
    capacity: int = Field(..., description="Number of crew members the ship can hold")
    cannons: int = Field(0, description="Number of cannons on the ship")
    year_built: Optional[int] = Field(None, description="Year the ship was built")


# Nested model for treasure
class Treasure(BaseModel):
    name: str
    value: float
    location: Optional[str] = None
    is_cursed: bool = False


class Pirate(BaseModel):
    name: str
    age: Optional[int] = None
    ship: Optional[str] = None
    rank: Optional[PirateRank] = None
    joined_date: Optional[date] = None
    skills: List[str] = Field(default_factory=list)
    bounty: Optional[float] = None
    is_active: bool = True


# Extended pirate model with more complex fields
class PirateExtended(Pirate):
    email: Optional[EmailStr] = None
    ship_details: Optional[Ship] = None
    treasures: List[Treasure] = Field(default_factory=list)
    last_seen: Optional[datetime] = None
    metadata: Dict[str, Union[str, int, bool]] = Field(default_factory=dict)


pirates_db = []
treasures_db = []
ships_db = []


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


# New endpoints with more complex features


@app.post("/ships", response_model=Ship, status_code=status.HTTP_201_CREATED)
def create_ship(ship: Ship, x_api_key: str = Header(None, description="API key for authentication")) -> Ship:
    """
    Create a new ship with detailed information.

    This endpoint demonstrates:
    - Custom status code
    - Header parameters
    - Complex response model
    """
    if x_api_key != "test-api-key":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    ships_db.append(ship)
    return ship


@app.get("/ships", response_model=List[Ship])
def get_ships(
    skip: int = Query(0, description="Number of ships to skip", ge=0),
    limit: int = Query(10, description="Maximum number of ships to return", ge=1, le=100),
    sort_by: str = Query("name", description="Field to sort by"),
    order: str = Query("asc", description="Sort order (asc or desc)"),
) -> List[Ship]:
    """
    Get a list of ships with pagination and sorting.

    This endpoint demonstrates:
    - Query parameters with validation
    - Pagination
    - Sorting options
    """
    result = ships_db.copy()

    # Sort the results
    reverse = order.lower() == "desc"
    if sort_by in ["name", "type", "capacity", "cannons", "year_built"]:
        result.sort(key=lambda x: getattr(x, sort_by), reverse=reverse)

    # Apply pagination
    return result[skip : skip + limit]


@app.get("/ships/{ship_id}", response_model=Ship)
def get_ship(
    ship_id: int = Path(..., description="The ID of the ship to get", ge=0),
    include_crew: bool = Query(False, description="Whether to include crew information"),
) -> Ship:
    """
    Get a ship by ID.

    This endpoint demonstrates:
    - Path parameters with validation
    - Optional query parameters affecting response
    """
    if ship_id >= len(ships_db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Ship with ID {ship_id} not found")

    ship = ships_db[ship_id]
    # In a real implementation, we would add crew info here if include_crew is True
    return ship


@app.post("/treasures", response_model=Treasure)
def create_treasure(
    treasure: Treasure, pirate_id: Optional[int] = Query(None, description="ID of the pirate who found the treasure")
) -> Treasure:
    """
    Add a new treasure to the database.

    This endpoint demonstrates:
    - Optional query parameters
    - Complex request body
    """
    treasures_db.append(treasure)
    return treasure


@app.post("/pirates/extended", response_model=PirateExtended)
def create_extended_pirate(
    pirate: PirateExtended = Body(..., description="Extended pirate information with nested objects"),
    session_id: str = Cookie(None, description="Session ID for tracking"),
) -> PirateExtended:
    """
    Create a new pirate with extended information.

    This endpoint demonstrates:
    - Complex nested objects
    - Cookie parameters
    - Detailed request body with annotations
    """
    # In a real implementation, we would validate the session_id
    return pirate


@app.get("/pirates/search", response_model=List[Pirate])
def search_pirates_advanced(
    name: Optional[str] = Query(None, description="Filter by name (case-insensitive, partial match)"),
    min_age: Optional[int] = Query(None, description="Minimum age", ge=0),
    max_age: Optional[int] = Query(None, description="Maximum age", ge=0),
    rank: Optional[PirateRank] = Query(None, description="Filter by rank"),
    skills: Optional[List[str]] = Query(None, description="Filter by skills (must have all listed skills)"),
    active_only: bool = Query(True, description="Only include active pirates"),
) -> List[Pirate]:
    """
    Advanced search for pirates with multiple optional filters.

    This endpoint demonstrates:
    - Multiple optional query parameters
    - Enum parameters
    - Array parameters
    - Boolean flags
    """
    result = pirates_db.copy()

    # Apply filters
    if name:
        result = [p for p in result if name.lower() in p.name.lower()]
    if min_age is not None:
        result = [p for p in result if p.age is not None and p.age >= min_age]
    if max_age is not None:
        result = [p for p in result if p.age is not None and p.age <= max_age]
    if rank:
        result = [p for p in result if p.rank == rank]
    if skills:
        result = [p for p in result if all(skill in p.skills for skill in skills)]
    if active_only:
        result = [p for p in result if p.is_active]

    return result


@app.patch("/pirates/{pirate_id}", response_model=Pirate)
def update_pirate_partial(
    pirate_id: int = Path(..., description="The ID of the pirate to update", ge=0),
    name: Optional[str] = Body(None, description="New name for the pirate"),
    age: Optional[int] = Body(None, description="New age for the pirate"),
    ship: Optional[str] = Body(None, description="New ship for the pirate"),
    rank: Optional[PirateRank] = Body(None, description="New rank for the pirate"),
    skills: Optional[List[str]] = Body(None, description="New skills for the pirate"),
    is_active: Optional[bool] = Body(None, description="Whether the pirate is active"),
) -> Pirate:
    """
    Partially update a pirate's information.

    This endpoint demonstrates:
    - PATCH method for partial updates
    - Multiple optional body parameters
    """
    if pirate_id >= len(pirates_db):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pirate with ID {pirate_id} not found")

    pirate = pirates_db[pirate_id]

    # Update fields if provided
    if name is not None:
        pirate.name = name
    if age is not None:
        pirate.age = age
    if ship is not None:
        pirate.ship = ship
    if rank is not None:
        pirate.rank = rank
    if skills is not None:
        pirate.skills = skills
    if is_active is not None:
        pirate.is_active = is_active

    return pirate


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", reload=True, debug=True, port=8000)
