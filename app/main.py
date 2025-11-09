import dotenv

from app.models.appStatus import AppStatus

dotenv.load_dotenv()

import uvicorn
from fastapi import FastAPI
from fastapi_pagination import add_pagination
from app.routes import status, users
from app.database.engine import create_db_and_tables


app = FastAPI()
add_pagination(app)
app.include_router(status.router)
app.include_router(users.router)


@app.get("/status", response_model=AppStatus)
def get_status():
    """Возвращает статус сервиса"""
    return {"status": "ok"}

if __name__ == "__main__":
    create_db_and_tables()

    uvicorn.run(app, host="localhost", port=8002)