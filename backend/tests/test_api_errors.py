from fastapi.testclient import TestClient

from app.main import create_app


def test_validation_errors_use_contract_shape() -> None:
    client = TestClient(create_app())
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "weak",
            "displayName": "Alex",
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert body["error"]["message"] == "Request validation failed."
    assert isinstance(body["error"]["details"], list)
    assert len(body["error"]["details"]) >= 1
