from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app


def test_current_user_endpoint_returns_authenticated_identity():
    app.dependency_overrides[get_current_user] = lambda: {
        "username": "demo_user",
        "role": "user",
    }

    try:
        response = TestClient(app).get("/api/me")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json() == {"username": "demo_user", "role": "user"}


def test_logout_clears_the_access_cookie():
    response = TestClient(app).post("/api/logout")

    assert response.status_code == 200
    assert response.json() == {"message": "Logged out"}
    assert "access_token" in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]
