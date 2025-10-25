from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/")
async def create_booking(payload: dict):
    """Stub booking creation. In real app, this must be atomic and use DB locks."""
    if not payload.get("train_run_id"):
        raise HTTPException(status_code=400, detail="train_run_id required")
    # Return fake booking id
    return {"pnr": "PNR12345", "status": "CONFIRMED"}


@router.get("/{pnr}")
async def get_booking(pnr: str):
    return {"pnr": pnr, "status": "CONFIRMED", "seats": ["S1-1"]}
