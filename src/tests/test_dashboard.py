import pytest
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes import dashboard as dashboard_routes
from app.main import app


@pytest.fixture(autouse=True)
def clear_dashboard_cache():
    dashboard_routes._dashboard_cache = None
    dashboard_routes._dashboard_cache_expires_at = 0


class FakeCursor:
    def __init__(self):
        self.query_count = 0
        self.queries = []

    def execute(self, query):
        self.query_count += 1
        self.queries.append(query)

    def fetchone(self):
        return (3_400_000, 7, 11, 8.25, 4.5, 72.3)

    def fetchall(self):
        return [("American Airlines", 8.25), ("Delta Air Lines", -1.5)]


class FakeConnection:
    def __init__(self):
        self.fake_cursor = FakeCursor()
        self.closed = False

    def cursor(self):
        return self.fake_cursor

    def close(self):
        self.closed = True


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


def test_dashboard_api_returns_json_compatible_insights(monkeypatch, capsys):
    connection = FakeConnection()
    monkeypatch.setattr(dashboard_routes, "get_sql_server_connection", lambda: connection)
    app.dependency_overrides[get_current_user] = lambda: {
        "username": "demo_user",
        "role": "user",
    }

    try:
        response = TestClient(app).get("/api/dashboard")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json() == {
        "metrics": {
            "total_flights": 3_400_000,
            "total_carriers": 7,
            "total_airports": 11,
            "average_arrival_delay": 8.2,
            "average_departure_delay": 4.5,
            "on_time_arrival_percentage": 72.3,
        },
        "carrier_delays": [
            {"airline_name": "American Airlines", "average_delay": 8.2},
            {"airline_name": "Delta Air Lines", "average_delay": -1.5},
        ],
    }
    metrics_query = connection.fake_cursor.queries[0]
    assert metrics_query.count("dbo.FlightInstance") == 1
    assert "COUNT_BIG(*) AS total_flights" in metrics_query
    assert "AVG(CAST(arrival_delay_minutes AS FLOAT))" in metrics_query
    assert "AVG(CAST(departure_delay_minutes AS FLOAT))" in metrics_query
    assert "on_time_arrival_percentage" in metrics_query
    assert connection.closed
    output = capsys.readouterr().out
    assert "Dashboard: starting metrics query" in output
    assert "Dashboard: starting airline delay chart query" in output


def test_dashboard_failure_prints_the_failing_query_stage(monkeypatch, capsys):
    connection = FakeConnection()
    monkeypatch.setattr(dashboard_routes, "get_sql_server_connection", lambda: connection)

    def fail_query(query):
        assert query
        raise RuntimeError("simulated SQL timeout")

    monkeypatch.setattr(
        connection.fake_cursor,
        "execute",
        fail_query,
    )
    app.dependency_overrides[get_current_user] = lambda: {
        "username": "demo_user",
        "role": "user",
    }

    try:
        response = TestClient(app).get("/api/dashboard")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 503
    output = capsys.readouterr().out
    assert "Dashboard: starting metrics query" in output
    assert "Dashboard: failed during metrics_query" in output
    assert "simulated SQL timeout" in output
    assert connection.closed


def test_dashboard_chart_query_joins_airline_names(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(dashboard_routes, "get_sql_server_connection", lambda: connection)
    app.dependency_overrides[get_current_user] = lambda: {
        "username": "demo_user",
        "role": "user",
    }

    try:
        response = TestClient(app).get("/api/dashboard")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert "INNER JOIN dbo.Airline" in connection.fake_cursor.queries[1]


def test_dashboard_caches_results_and_skips_sql_on_cache_hit(monkeypatch):
    connection = FakeConnection()
    connection_calls = 0

    def get_connection():
        nonlocal connection_calls
        connection_calls += 1
        return connection

    monkeypatch.setattr(dashboard_routes, "get_sql_server_connection", get_connection)
    app.dependency_overrides[get_current_user] = lambda: {
        "username": "demo_user",
        "role": "user",
    }

    try:
        client = TestClient(app)
        first_response = client.get("/api/dashboard")
        second_response = client.get("/api/dashboard")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert first_response.status_code == 200
    assert first_response.headers["x-dashboard-cache"] == "MISS"
    assert second_response.status_code == 200
    assert second_response.headers["x-dashboard-cache"] == "HIT"
    assert first_response.json() == second_response.json()
    assert connection_calls == 1
    assert len(connection.fake_cursor.queries) == 2


def test_dashboard_refreshes_cache_after_ttl(monkeypatch):
    clock = {"now": 100.0}
    connections = []

    def get_connection():
        connection = FakeConnection()
        connections.append(connection)
        return connection

    monkeypatch.setattr(dashboard_routes, "perf_counter", lambda: clock["now"])
    monkeypatch.setattr(dashboard_routes, "get_sql_server_connection", get_connection)
    monkeypatch.setattr(dashboard_routes.settings, "DASHBOARD_CACHE_TTL_SECONDS", 10)
    app.dependency_overrides[get_current_user] = lambda: {
        "username": "demo_user",
        "role": "user",
    }

    try:
        client = TestClient(app)
        first_response = client.get("/api/dashboard")
        clock["now"] += 11
        refreshed_response = client.get("/api/dashboard")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert first_response.headers["x-dashboard-cache"] == "MISS"
    assert refreshed_response.headers["x-dashboard-cache"] == "MISS"
    assert len(connections) == 2
    assert all(connection.closed for connection in connections)


def test_dashboard_chart_uses_airline_names_as_labels():
    response = TestClient(app).get("/dashboard")

    assert response.status_code == 200
    assert "labels: data.carrier_delays.map((item) => item.airline_name)" in response.text


def test_dashboard_api_requires_login():
    app.dependency_overrides.pop(get_current_user, None)

    response = TestClient(app).get("/api/dashboard")

    assert response.status_code == 401
