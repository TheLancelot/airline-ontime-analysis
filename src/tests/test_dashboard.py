from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes.dashboard import DASHBOARD_SNAPSHOT
from app.main import app


def test_dashboard_page_and_auth_navigation_are_available():
    client = TestClient(app)
    landing = client.get("/")
    login = client.get("/login")
    register = client.get("/register")

    assert landing.status_code == 200
    assert 'href="/login?next=admin"' in landing.text
    assert login.status_code == 200
    assert 'class="password-toggle"' in login.text
    assert "window.location.assign(data.role === 'admin' ? '/admin' : '/dashboard')" in login.text
    assert register.status_code == 200
    assert 'class="password-toggle"' in register.text
    assert "window.location.assign(`/login?registered=1&username=" in register.text


def test_landing_page_references_the_served_stylesheet():
    client = TestClient(app)

    landing = client.get("/")
    stylesheet = client.get("/static/styles.css?v=3")

    assert 'href="/static/styles.css?v=3"' in landing.text
    assert stylesheet.status_code == 200
    assert "text/css" in stylesheet.headers["content-type"]
    assert ".site-header" in stylesheet.text


def test_dashboard_api_returns_exact_precomputed_snapshot():
    app.dependency_overrides[get_current_user] = lambda: {
        "username": "demo_user",
        "role": "user",
    }

    try:
        response = TestClient(app).get("/api/dashboard")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json() == DASHBOARD_SNAPSHOT
    assert response.json()["metrics"] == {
        "total_flights": 3_401_526,
        "total_carriers": 14,
        "total_airports": 180,
        "average_arrival_delay": 7.08507916740898,
        "average_departure_delay": 15.293786671041174,
        "on_time_arrival_percentage": 76.8957,
    }
    assert len(response.json()["carrier_delays"]) == 7


def test_dashboard_page_uses_airline_names_and_explains_snapshot():
    response = TestClient(app).get("/dashboard")

    assert response.status_code == 200
    assert "labels: data.carrier_delays.map((item) => item.airline_name)" in response.text
    assert "Exact precomputed values from the current static dataset" in response.text
    assert "repeatable 10%" not in response.text


def test_dashboard_api_requires_login():
    app.dependency_overrides.pop(get_current_user, None)

    response = TestClient(app).get("/api/dashboard")

    assert response.status_code == 401
