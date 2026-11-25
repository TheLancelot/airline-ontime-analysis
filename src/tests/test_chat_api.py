from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.api.routes import chat as chat_routes
from app.main import app
from app.services.gemini_client import GeminiServiceError


class FakeRow:
    def __init__(self, values):
        self.values = values

    def __iter__(self):
        return iter(self.values)


class FakeCursor:
    description = [("carrier_code",), ("airline_name",)]

    def execute(self, sql):
        self.sql = sql

    def fetchmany(self, size):
        return [FakeRow(("AA", "American Airlines"))]


class FakeConnection:
    def __init__(self):
        self.fake_cursor = FakeCursor()
        self.closed = False

    def cursor(self):
        return self.fake_cursor

    def close(self):
        self.closed = True


def test_chat_serializes_database_rows_for_json(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(chat_routes, "get_sql_server_connection", lambda: connection)
    monkeypatch.setattr(
        chat_routes.GeminiClient,
        "generate_sql",
        lambda self, question: {
            "sql": "SELECT carrier_code, airline_name FROM dbo.Airline",
            "refusal_reason": None,
            "explanation": "Lists carriers.",
        },
    )
    app.dependency_overrides[get_current_user] = lambda: {
        "username": "demo_user",
        "role": "user",
    }

    try:
        response = TestClient(app).post("/api/chat", json={"question": "List carriers"})
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["rows"] == [["AA", "American Airlines"]]
    assert "sql" not in response.json()
    assert connection.closed


def test_chat_returns_generated_sql_to_admin_only(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(chat_routes, "get_sql_server_connection", lambda: connection)
    monkeypatch.setattr(
        chat_routes.GeminiClient,
        "generate_sql",
        lambda self, question: {
            "sql": "SELECT carrier_code, airline_name FROM dbo.Airline",
            "refusal_reason": None,
            "explanation": "Lists carriers.",
        },
    )
    app.dependency_overrides[get_current_user] = lambda: {
        "username": "demo_admin",
        "role": "admin",
    }

    try:
        response = TestClient(app).post("/api/chat", json={"question": "List carriers"})
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["sql"] == (
        "SELECT TOP 250 carrier_code, airline_name FROM dbo.Airline"
    )


def test_chat_returns_visible_gateway_error_when_gemini_fails(monkeypatch):
    def fail_generation(self, question):
        raise GeminiServiceError("Gemini could not generate a response.")

    monkeypatch.setattr(chat_routes.GeminiClient, "generate_sql", fail_generation)
    app.dependency_overrides[get_current_user] = lambda: {
        "username": "demo_user",
        "role": "user",
    }

    try:
        response = TestClient(app).post("/api/chat", json={"question": "List carriers"})
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 502
    assert response.json()["detail"] == "Gemini could not generate a response."
