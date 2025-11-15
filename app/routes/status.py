from fastapi import APIRouter
from app.database.engine import check_availability
from app.models.appStatus import AppStatus  # импорт твоей модели

router = APIRouter(prefix="/api")

@router.get("/status", response_model=AppStatus)
def status():
    return AppStatus(database=check_availability())
