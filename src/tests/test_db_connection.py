from app.config import settings
from app.db.connection import build_connection_string


def test_connection_uses_trusted_authentication():
    connection_string = build_connection_string()

    assert "DRIVER={ODBC Driver 18 for SQL Server};" in connection_string
    assert f"SERVER={settings.SQL_SERVER_SERVER};" in connection_string
    assert f"DATABASE={settings.SQL_SERVER_DATABASE};" in connection_string
    assert "Trusted_Connection=yes;" in connection_string
    assert "TrustServerCertificate=yes;" in connection_string
    assert "UID=" not in connection_string
    assert "PWD=" not in connection_string


def test_default_server_is_named_instance():
    assert settings.SQL_SERVER_SERVER == r"DESKTOP-LVP84RD\MSSQLSERVER01"
