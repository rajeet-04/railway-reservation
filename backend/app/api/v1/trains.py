from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_trains(from_code: str | None = None, to_code: str | None = None):
    """List trains between two stations (stub)."""
    return {"from": from_code, "to": to_code, "trains": [{"number": "12345", "name": "Sample Express"}]}


@router.get("/{number}")
async def train_detail(number: str):
    return {"number": number, "name": "Sample Express", "distance_km": 500, "duration_h": 8, "duration_m": 30}
