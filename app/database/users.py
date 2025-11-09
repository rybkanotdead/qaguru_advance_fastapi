from .engine import engine
from sqlmodel import Session, select
from ..models.users import User, UserCreate, UserUpdate
from typing import Iterable

def get_user(user_id: int) -> User | None:
    with Session(engine) as session:
        return session.get(User, user_id)

def get_users() -> Iterable[User]:
    with Session(engine) as session:
        statement = select(User)
        return session.exec(statement).all()

def create_user(user: UserCreate) -> User:
    db_user = User(**user.dict())  # <-- создаем User из UserCreate
    with Session(engine) as session:
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

def update_user(user_id: int, user: UserUpdate) -> User | None:
    with Session(engine) as session:
        db_user = session.get(User, user_id)
        if not db_user:
            return None
        user_data = user.dict(exclude_unset=True)  # <-- корректно для PATCH
        for key, value in user_data.items():
            setattr(db_user, key, value)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

def delete_user(user_id: int):
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user:
            session.delete(user)
            session.commit()
