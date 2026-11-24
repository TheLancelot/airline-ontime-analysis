import pyodbc

from app.config import settings


def build_connection_string() -> str:
    return (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={settings.SQL_SERVER_SERVER};"
        f"DATABASE={settings.SQL_SERVER_DATABASE};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )


def get_sql_server_connection():
    return pyodbc.connect(build_connection_string())
