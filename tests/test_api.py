import json
import pytest
import requests
from http import HTTPStatus
from sqlmodel import Session as SQLSession
from app.database.engine import engine
from app.models.users import User
from app.models.pagination import Pagination


# ================== Fixtures ==================

@pytest.fixture
def fill_test_data():
    """Заполняем тестовую БД пользователями из JSON."""
    with open("users.json", "r", encoding="utf-8") as f:
        users_data = json.load(f)

    users_objects = [User(**user) for user in users_data]

    with SQLSession(engine) as session:
        session.query(User).delete()
        session.add_all(users_objects)
        session.commit()


@pytest.fixture
def created_users(fill_test_data):
    """Возвращаем реальные id пользователей после вставки."""
    with SQLSession(engine) as session:
        users = session.query(User).all()
        return {i + 1: user.id for i, user in enumerate(users[:12])}


@pytest.fixture
def users(get_url):
    response = requests.get(f"{get_url}/api/users/", proxies={})
    assert response.status_code == HTTPStatus.OK
    return response.json()["items"]


# ================== GET Tests ==================

class TestUsersEndpoint:
    """Tests Users endpoint"""

    def test_users(self, get_url):
        response = requests.get(f"{get_url}/api/users/", proxies={})
        assert response.status_code == HTTPStatus.OK

        users_list = response.json()["items"]
        for user in users_list:
            User.model_validate(user)

    def test_users_no_duplicates(self, users):
        users_ids = [user["id"] for user in users]
        assert len(users_ids) == len(set(users_ids))


class TestUserEndpoint:
    """Tests single User endpoint"""

    @pytest.mark.parametrize("user_index", [1, 6, 12])
    def test_user(self, get_url, user_index, created_users):
        user_id = created_users[user_index]
        response = requests.get(f"{get_url}/api/users/{user_id}", proxies={})
        assert response.status_code == HTTPStatus.OK

        user = response.json()
        User.model_validate(user)

    @pytest.mark.parametrize("user_id", [9999])
    def test_user_nonexistent_values(self, get_url, user_id):
        response = requests.get(f"{get_url}/api/users/{user_id}", proxies={})
        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.parametrize("user_id", [-1, 0, "fafaf"])
    def test_user_invalid_values(self, get_url, user_id):
        response = requests.get(f"{get_url}/api/users/{user_id}", proxies={})
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


# ================== Pagination Tests ==================

class TestPagination:
    """Tests Pagination endpoint"""

    def test_default_pagination(self, get_url):
        response = requests.get(f"{get_url}/api/users/", proxies={})
        users_with_pagination = response.json()

        assert response.status_code == HTTPStatus.OK
        assert len(users_with_pagination["items"]) == 12

        Pagination.model_validate(users_with_pagination)

    @pytest.mark.parametrize("size, expected_pages", [(1, 12), (3, 4), (12, 1)])
    def test_get_users_page_calculation(self, get_url, size, expected_pages):
        response = requests.get(f"{get_url}/api/users/?size={size}", proxies={})
        assert response.status_code == HTTPStatus.OK
        assert response.json()["pages"] == expected_pages

    @pytest.mark.parametrize("page, size, expected_count", [
        (1, 5, 5),
        (2, 5, 5),
        (3, 5, 2),
        (1, 12, 12),
        (2, 12, 0)
    ])
    def test_get_users_different_pages_pagination(self, get_url, page, size, expected_count):
        response = requests.get(f"{get_url}/api/users/?page={page}&size={size}", proxies={})
        assert response.status_code == HTTPStatus.OK
        assert response.json()["page"] == page
        assert response.json()["size"] == size
        assert len(response.json()["items"]) == expected_count

    def test_get_users_different_data_in_pages(self, get_url):
        response_page1 = requests.get(f"{get_url}/api/users/?page=1&size=6", proxies={})
        response_page2 = requests.get(f"{get_url}/api/users/?page=2&size=6", proxies={})

        data_page1 = response_page1.json()
        data_page2 = response_page2.json()

        assert data_page1["items"] != data_page2["items"]
        assert data_page1["page"] == 1
        assert data_page2["page"] == 2


# ================== CRUD Tests ==================

class TestUsersCRUD:
    BASE_PATH = "/api/users"

    @pytest.mark.usefixtures("fill_test_data")
    def test_create_user(self, get_url):
        """POST: создание нового пользователя"""
        new_user = {
            "first_name": "Smoke",
            "last_name": "Test",
            "email": "smoke@test.com",
            "avatar": "https://example.com/avatar.jpg"
        }
        response = requests.post(f"{get_url}{self.BASE_PATH}/", json=new_user, proxies={})
        print(response.text)
        assert response.status_code in (HTTPStatus.CREATED, HTTPStatus.OK)

        with SQLSession(engine) as session:
            user_in_db = session.query(User).filter(User.email == "smoke@test.com").first()
            assert user_in_db is not None
            assert user_in_db.first_name == "Smoke"

    @pytest.mark.usefixtures("fill_test_data")
    def test_update_user(self, get_url, created_users):
        """PATCH/PUT: изменение существующего пользователя"""
        user_id = list(created_users.values())[0]
        update_data = {"first_name": "Updated", "last_name": "UserUpdated"}

        response = requests.patch(f"{get_url}{self.BASE_PATH}/{user_id}", json=update_data, proxies={})
        if response.status_code == 405:
            response = requests.put(f"{get_url}{self.BASE_PATH}/{user_id}", json=update_data, proxies={})

        print(response.text)
        assert response.status_code in (HTTPStatus.OK, HTTPStatus.NO_CONTENT)

        with SQLSession(engine) as session:
            user_in_db = session.query(User).get(user_id)
            assert user_in_db.first_name == "Updated"
            assert user_in_db.last_name == "UserUpdated"

    @pytest.mark.usefixtures("fill_test_data")
    def test_delete_user(self, get_url, created_users):
        """DELETE: удаление существующего пользователя"""
        user_id = list(created_users.values())[0]
        response = requests.delete(f"{get_url}{self.BASE_PATH}/{user_id}", proxies={})
        print(response.text)
        assert response.status_code in (HTTPStatus.NO_CONTENT, HTTPStatus.OK)

        with SQLSession(engine) as session:
            user_in_db = session.query(User).get(user_id)
            assert user_in_db is None
