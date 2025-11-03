import pytest
import requests
from http import HTTPStatus
from models.users import User
from models.pagination import Pagination


@pytest.fixture
def users(get_url):
    response = requests.get(f"{get_url}/api/users/", proxies={})
    assert response.status_code == HTTPStatus.OK
    return response.json()["items"]


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
    """Tests Users endpoint"""
    @pytest.mark.parametrize("user_id", [1, 6, 12])
    def test_user(self, get_url, user_id):
        response = requests.get(f"{get_url}/api/users/{user_id}", proxies={})
        assert response.status_code == HTTPStatus.OK

        user = response.json()
        User.model_validate(user)

    @pytest.mark.parametrize("user_id", [13])
    def test_user_nonexistent_values(self, get_url, user_id):
        response = requests.get(f"{get_url}/api/users/{user_id}", proxies={})
        assert response.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.parametrize("user_id", [-1, 0, "fafaf"])
    def test_user_invalid_values(self, get_url, user_id):
        response = requests.get(f"{get_url}/api/users/{user_id}", proxies={})
        assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


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