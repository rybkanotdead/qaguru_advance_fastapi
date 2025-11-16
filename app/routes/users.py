from http import HTTPStatus
from fastapi import APIRouter, HTTPException
from fastapi_pagination import Page, paginate
from app.database import users
from app.models.users import User, UserCreate, UserUpdate

router = APIRouter(prefix="/api/users")



@router.get("/{user_id}", status_code=HTTPStatus.OK, response_model=User)
def get_user_endpoint(user_id: int) -> User:
    if user_id < 1:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                            detail="User ID must be 1 or greater")
    user = users.get_user(user_id)
    if not user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail=f"User with ID {user_id} not found.")
    return user


@router.get("/", status_code=HTTPStatus.OK, response_model=Page[User])
def get_users_endpoint() -> Page[User]:
    user_list = users.get_users()
    return paginate(user_list)


@router.post("/", status_code=HTTPStatus.CREATED, response_model=User)
def create_user_endpoint(user: UserCreate) -> User:
    return users.create_user(user)


@router.patch("/{user_id}", status_code=HTTPStatus.OK, response_model=User)
def patch_user_endpoint(user_id: int, user: UserUpdate) -> User:
    if user_id < 1:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                            detail="Invalid user ID")
    updated_user = users.update_user(user_id, user)
    if not updated_user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="User not found")
    return updated_user


@router.put("/{user_id}", status_code=HTTPStatus.OK, response_model=User)
def put_user_endpoint(user_id: int, user: UserUpdate) -> User:
    if user_id < 1:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                            detail="Invalid user ID")
    updated_user = users.update_user(user_id, user)
    if not updated_user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="User not found")
    return updated_user


@router.delete("/{user_id}", status_code=HTTPStatus.NO_CONTENT)
def delete_user_endpoint(user_id: int):
    if user_id < 1:
        raise HTTPException(status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
                            detail="Invalid user ID")
    user = users.get_user(user_id)
    if not user:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND,
                            detail="User not found")
    users.delete_user(user_id)
