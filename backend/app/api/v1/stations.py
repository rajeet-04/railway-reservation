from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_stations(q: str = "", limit: int = 10):
    """Return a small list of station suggestions (stub)."""
    # Real implementation: query DB with LIKE / trigrams
    sample = [
        {"code": "NDLS", "name": "New Delhi"},
        {"code": "BCT", "name": "Mumbai Central"},
    ]
    return {"query": q, "results": sample[:limit]}


@router.get("/{code}")
async def station_detail(code: str):
    return {"code": code.upper(), "name": "Sample Station", "latitude": 0.0, "longitude": 0.0}
