import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app
from app.db.models import TelemetryResponse

client = TestClient(app)

MOCK_TELEMETRY = [
    TelemetryResponse(ts=1715000000, solar_v=18.5, solar_a=4.1, bat_v=12.6, bat_a=-1.5),
    TelemetryResponse(ts=1715000010, solar_v=18.6, solar_a=4.2, bat_v=12.5, bat_a=-1.4),
]

# ТЕСТ 1: Перевірка кореневого шляху (Base Root)
def test_root_endpoint():
    """Перевірка ініціалізації та працездатності головного екземпляра FastAPI."""
    response = client.get("/")
    assert response.status_code == 200
    assert "Smart Energy Backend is running" in response.json()["message"]


# ТЕСТ 2: Перевірка здоров'я API маршрутів (Healthcheck)
def test_healthcheck_status():
    """Перевірка доступності базового маршруту API (v1)."""
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Backend is running"}


# ТЕСТ 3: Успішне отримання телеметрії (Positive Case)
@patch("app.api.routes.get_recent_telemetry")
def test_get_telemetry_success(mock_get_telemetry):
    """Перевірка коректного парсингу та віддачі списку телеметрії."""
    mock_get_telemetry.return_value = MOCK_TELEMETRY
    
    response = client.get("/api/v1/telemetry/latest?limit=2")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["solar_v"] == 18.5
    assert data[1]["bat_a"] == -1.4


# ТЕСТ 4: Захист від від'ємного ліміту (Lower Bound Validation)
def test_get_telemetry_validation_error_min():
    """Перевірка захисту API від некоректних Query-параметрів (менше мінімуму)."""
    response = client.get("/api/v1/telemetry/latest?limit=0")
    
    # Статус 422: Unprocessable Entity
    assert response.status_code == 422
    assert "greater than or equal to 1" in response.text


# ТЕСТ 5: Захист від надмірного навантаження (Upper Bound Validation)
def test_get_telemetry_validation_error_max():
    """Перевірка захисту від запитів, що перевищують ліміт БД."""
    # Згідно з нашою моделлю, максимум - 500 записів
    response = client.get("/api/v1/telemetry/latest?limit=1000")
    
    assert response.status_code == 422
    assert "less than or equal to 500" in response.text


# ТЕСТ 6: Обробка порожньої бази даних (Empty State)
@patch("app.api.routes.get_recent_telemetry")
def test_get_telemetry_empty_db(mock_get_telemetry):
    """Перевірка поведінки API, якщо в InfluxDB ще немає даних."""
    mock_get_telemetry.return_value = []
    
    response = client.get("/api/v1/telemetry/latest")
    
    assert response.status_code == 200
    assert response.json() == []