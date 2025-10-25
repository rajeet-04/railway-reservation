from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def search_routes(from_code: str, to_code: str, date: str | None = None):
    """Stub route search returning one itinerary."""
    return {
        "from": from_code,
        "to": to_code,
        "date": date,
        "itineraries": [
            {"segments": [{"train_number": "12345", "from": from_code, "to": to_code, "depart": "09:00", "arrive": "17:30"}], "duration": "8:30"}
        ],
    }
