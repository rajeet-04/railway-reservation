from fastapi import APIRouter

router = APIRouter()


@router.get("/stats")
async def stats():
    """Admin stats stub."""
    return {"trains": 5208, "stations": 8990}
