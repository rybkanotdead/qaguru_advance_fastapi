import pytest
import requests
from http import HTTPStatus
from app.models.appStatus import AppStatus


class TestStatusEndpoint:
    """Tests for endpoint /api/status"""

    def test_status_ok(self, get_url):
        """Проверка успешного ответа /status"""
        response = requests.get(f"{get_url}/api/status", timeout=5)

        assert response.status_code == HTTPStatus.OK, f"Expected 200, got {response.status_code}"

        try:
            data = response.json()
        except requests.exceptions.JSONDecodeError:
            pytest.fail("Response is not valid JSON")

        assert "database" in data, "Response missing 'database' field"
        assert isinstance(data["database"], bool), "'database' should be a boolean"

        AppStatus.model_validate(data)

    def test_status_response_time(self, get_url):
        """Проверка времени ответа сервиса"""
        response = requests.get(f"{get_url}/api/status", timeout=5)
        assert response.elapsed.total_seconds() < 2, "Response time too long"

    def test_service_not_running(self, get_url):
        """Проверка недоступности сервиса"""
        try:
            requests.get(f"{get_url}/api/status", timeout=5)
            pytest.skip("Server is running, skipping test")
        except requests.exceptions.ConnectionError:
            assert True
