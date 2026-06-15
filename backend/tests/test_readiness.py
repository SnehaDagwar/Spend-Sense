import logging
from unittest.mock import MagicMock, patch
from fastapi import status
from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.db.session import get_db
from app.core.middleware import RequestLoggingMiddleware


def test_health_endpoint() -> None:
    """Verifies the root-level liveness health check returns 200 and 'ok' status."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "environment" in body


def test_readiness_endpoint_success() -> None:
    """Verifies that the readiness probe returns 200 when the database is reachable."""
    mock_session = MagicMock()
    mock_session.execute.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_session
    try:
        client = TestClient(app)
        response = client.get("/readiness")
        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["status"] == "ok"
        assert body["db"] == "ok"
        mock_session.execute.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_readiness_endpoint_failure() -> None:
    """Verifies that the readiness probe returns 503 when the database is unreachable."""
    mock_session = MagicMock()
    mock_session.execute.side_effect = Exception("DB connection timeout")

    app.dependency_overrides[get_db] = lambda: mock_session
    try:
        client = TestClient(app)
        response = client.get("/readiness")
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        body = response.json()
        assert body["status"] == "unready"
        assert body["db"] == "error"
    finally:
        app.dependency_overrides.clear()


def test_request_logging_middleware_success(caplog: pytest.LogCaptureFixture) -> None:
    """Verifies request logging middleware captures request details successfully."""
    caplog.set_level(logging.INFO, logger="app.request")
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 200

    # Verify log messages from app.request logger
    request_logs = [r for r in caplog.records if r.name == "app.request"]
    assert len(request_logs) >= 1
    log_record = request_logs[0]
    assert "GET /health finished with 200" in log_record.message
    assert log_record.method == "GET"
    assert log_record.path == "/health"
    assert log_record.status_code == 200
    assert hasattr(log_record, "duration_ms")
    assert hasattr(log_record, "ip")
    assert hasattr(log_record, "user_agent")


@patch("app.core.middleware.decode_token")
def test_request_logging_middleware_authenticated(mock_decode: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
    """Verifies middleware extracts user_id from authorization header and logs it."""
    caplog.set_level(logging.INFO, logger="app.request")
    mock_decode.return_value = {"sub": "user-uuid-12345"}
    client = TestClient(app)

    headers = {"Authorization": "Bearer fake-token-string"}
    response = client.get("/health", headers=headers)
    assert response.status_code == 200

    mock_decode.assert_called_once_with("fake-token-string", expected_type="access")

    request_logs = [r for r in caplog.records if r.name == "app.request"]
    assert len(request_logs) >= 1
    log_record = request_logs[0]
    assert log_record.user_id == "user-uuid-12345"


@patch("app.core.middleware.decode_token")
def test_request_logging_middleware_invalid_token(mock_decode: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
    """Verifies middleware gracefully continues logging if the token is invalid/expired."""
    caplog.set_level(logging.INFO, logger="app.request")
    mock_decode.side_effect = Exception("Token expired")
    client = TestClient(app)

    headers = {"Authorization": "Bearer expired-token-string"}
    response = client.get("/health", headers=headers)
    assert response.status_code == 200

    request_logs = [r for r in caplog.records if r.name == "app.request"]
    assert len(request_logs) >= 1
    log_record = request_logs[0]
    # user_id should not be set since decoding failed
    assert not hasattr(log_record, "user_id")
