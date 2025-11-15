import os
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlmodel import create_engine, SQLModel

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_ENGINE", "sqlite:///./test.db")
POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", 10))

engine = create_engine(DATABASE_URL, pool_size=POOL_SIZE, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def check_availability() -> bool:
    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print("DB connection error:", e)
        return False
