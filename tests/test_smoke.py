import pytest
import requests
from http import HTTPStatus
from models.appStatus import AppStatus


class TestStatusEndpoint:
    """Tests for endpoint /status"""
    def test_status(self, get_url):
        response = requests.get(f"{get_url}/status")
        data = response.json()

        assert response.status_code == HTTPStatus.OK
        assert data["status"] == "ok"

        AppStatus.model_validate(data)

    def test_service_not_running(self, get_url):
        try:
            requests.get(f"{get_url}/status", timeout=5)
            pytest.skip("Server is running port 8002")
        except requests.exceptions.ConnectionError:
            assert False, "Connection error"
