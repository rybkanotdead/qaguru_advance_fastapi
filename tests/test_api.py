import json
from pathlib import Path
import pytest
from http import HTTPStatus
from sqlmodel import Session as SQLSession
from app.database.engine import engine
from app.models.users import User
from app.models.pagination import Pagination


# ================== Fixtures ==================

@pytest.fixture
def fill_test_data(users_api):
    """Заполняем тестовую БД пользователями через API."""
    users_file = Path(__file__).parent / "users.json"
    if not users_file.exists():
        pytest.fail("users.json file not found in tests folder")

    with users_file.open("r", encoding="utf-8") as f:
        users_data = json.load(f)

    # Очищаем базу — удаляем всех пользователей
    response = users_api.get_users()
    if response.status_code != HTTPStatus.OK:
        pytest.fail(f"get_users failed with status {response.status_code}")

    for user in response.json().get("items", []):
        users_api.delete_user(user["id"])

    created = []
    for user in users_data:
        r = users_api.create_user(user)
        if r.status_code not in (HTTPStatus.CREATED, HTTPStatus.OK):
            pytest.fail(f"create_user failed with status {r.status_code}")
        created.append(r.json()["id"])

    return created


@pytest.fixture
def created_users(fill_test_data, users_api):
    """Возвращаем реальные id пользователей"""
    response = users_api.get_users()
    if response.status_code != HTTPStatus.OK:
        pytest.fail(f"get_users failed with status {response.status_code}")

    users = response.json()["items"]
    return {i + 1: users[i]["id"] for i in range(min(12, len(users)))}


@pytest.fixture
def users(users_api):
    response = users_api.get_users()
    if response.status_code != HTTPStatus.OK:
        pytest.fail(f"get_users failed with status {response.status_code}")
    return response.json()["items"]


# ================== GET Tests ==================

class TestUsersEndpoint:
    """Tests Users endpoint"""

    def test_users(self, users_api):
        response = users_api.get_users()
        if response.status_code != HTTPStatus.OK:
            pytest.fail(f"get_users failed with status {response.status_code}")

        users_list = response.json()["items"]
        for user in users_list:
            User.model_validate(user)

    def test_users_no_duplicates(self, users):
        users_ids = [user["id"] for user in users]
        assert len(users_ids) == len(set(users_ids))


class TestUserEndpoint:
    """Tests single User endpoint"""

    @pytest.mark.parametrize("user_index", [1, 6, 12])
    def test_user(self, users_api, user_index, created_users):
        user_id = created_users[user_index]
        response = users_api.get_user(user_id)
        if response.status_code != HTTPStatus.OK:
            pytest.fail(f"get_user failed with status {response.status_code}")

        user = response.json()
        User.model_validate(user)

    @pytest.mark.parametrize("user_id", [9999])
    def test_user_nonexistent_values(self, users_api, user_id):
        response = users_api.get_user(user_id)
        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.parametrize("user_id", [-1, 0, "fafaf"])
    def test_user_invalid_values(self, users_api, user_id):
        response = users_api.get_user(user_id)
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ================== Pagination Tests ==================

class TestPagination:
    """Tests Pagination endpoint"""

    def test_default_pagination(self, users_api):
        response = users_api.get_users()
        if response.status_code != HTTPStatus.OK:
            pytest.fail(f"get_users failed with status {response.status_code}")

        users_with_pagination = response.json()
        assert len(users_with_pagination["items"]) == 12
        Pagination.model_validate(users_with_pagination)

    @pytest.mark.parametrize("size, expected_pages", [(1, 12), (3, 4), (12, 1)])
    def test_get_users_page_calculation(self, users_api, size, expected_pages):
        response = users_api.get_users(size=size)
        if response.status_code != HTTPStatus.OK:
            pytest.fail(f"get_users failed with status {response.status_code}")

        assert response.json()["pages"] == expected_pages

    @pytest.mark.parametrize("page, size, expected_count", [
        (1, 5, 5),
        (2, 5, 5),
        (3, 5, 2),
        (1, 12, 12),
        (2, 12, 0)
    ])
    def test_get_users_different_pages_pagination(self, users_api, page, size, expected_count):
        response = users_api.get_users(page=page, size=size)
        if response.status_code != HTTPStatus.OK:
            pytest.fail(f"get_users failed with status {response.status_code}")

        body = response.json()
        assert body["page"] == page
        assert body["size"] == size
        assert len(body["items"]) == expected_count

    def test_get_users_different_data_in_pages(self, users_api):
        resp1 = users_api.get_users(page=1, size=6)
        resp2 = users_api.get_users(page=2, size=6)

        try:
            data1 = resp1.json()
            data2 = resp2.json()
        except json.JSONDecodeError:
            pytest.fail("Failed to decode JSON from get_users response")

        assert data1["items"] != data2["items"]
        assert data1["page"] == 1
        assert data2["page"] == 2


# ================== CRUD Tests ==================

class TestUsersCRUD:
    """CRUD tests"""

    @pytest.mark.usefixtures("fill_test_data")
    def test_create_user(self, users_api):
        new_user = {
            "first_name": "Smoke",
            "last_name": "Test",
            "email": "smoke@test.com",
            "avatar": "https://example.com/avatar.jpg"
        }

        response = users_api.create_user(new_user)
        if response.status_code not in (HTTPStatus.CREATED, HTTPStatus.OK):
            pytest.fail(f"create_user failed with status {response.status_code}")

        with SQLSession(engine) as session:
            user_in_db = session.query(User).filter(User.email == "smoke@test.com").first()
            assert user_in_db is not None
            assert user_in_db.first_name == "Smoke"

    @pytest.mark.usefixtures("fill_test_data")
    def test_update_user(self, users_api, created_users):
        user_id = list(created_users.values())[0]
        update_data = {"first_name": "Updated", "last_name": "UserUpdated"}

        response = users_api.update_user(user_id, update_data)
        if response.status_code not in (HTTPStatus.OK, HTTPStatus.NO_CONTENT):
            pytest.fail(f"update_user failed with status {response.status_code}")

        with SQLSession(engine) as session:
            user_in_db = session.query(User).get(user_id)
            assert user_in_db.first_name == "Updated"
            assert user_in_db.last_name == "UserUpdated"

    @pytest.mark.usefixtures("fill_test_data")
    def test_delete_user(self, users_api, created_users):
        user_id = list(created_users.values())[0]

        response = users_api.delete_user(user_id)
        if response.status_code not in (HTTPStatus.NO_CONTENT, HTTPStatus.OK):
            pytest.fail(f"delete_user failed with status {response.status_code}")

        with SQLSession(engine) as session:
            user_in_db = session.query(User).get(user_id)
            assert user_in_db is None
