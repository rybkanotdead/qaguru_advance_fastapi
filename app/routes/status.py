from fastapi import APIRouter
from app.database.engine import check_availability

router = APIRouter(prefix="/api")

@router.get("/status")
def status():
    return {"database": check_availability()}
