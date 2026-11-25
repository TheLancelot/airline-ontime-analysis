import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def resolve_app_path(value: str | None, default: Path) -> Path:
    path = Path(value).expanduser() if value else default
    if not path.is_absolute():
        path = BASE_DIR / path
    return path.resolve()


class Settings:
    APP_NAME = "Airline On-Time Demo"
    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    SQL_SERVER_SERVER = os.getenv("SQL_SERVER_SERVER", r"DESKTOP-LVP84RD\MSSQLSERVER01")
    SQL_SERVER_DATABASE = os.getenv("SQL_SERVER_DATABASE", "AirlinesProject")
    USER_STORE_PATH = resolve_app_path(
        os.getenv("USER_STORE_PATH"), BASE_DIR / "data" / "users.json"
    )
    LOG_FILE_PATH = resolve_app_path(
        os.getenv("LOG_FILE_PATH"), BASE_DIR / "logs" / "app.log"
    )
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    ALLOWED_TABLES = {"airline", "airport", "flightinstance"}
    MAX_ROWS = 250
    MAX_QUERY_SECONDS = 30
    DASHBOARD_CACHE_TTL_SECONDS = int(os.getenv("DASHBOARD_CACHE_TTL_SECONDS", "300"))
    MAX_LOG_LINES = 200


settings = Settings()
