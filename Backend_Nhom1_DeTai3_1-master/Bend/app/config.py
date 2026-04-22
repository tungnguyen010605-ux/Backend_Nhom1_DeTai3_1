from __future__ import annotations

from os import getenv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(getenv("DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(getenv("DB_PATH", str(DATA_DIR / "app.db")))


def _normalize_database_url(raw_database_url: str | None) -> str:
    if not raw_database_url:
        return f"sqlite:///{DB_PATH.as_posix()}"

    sqlite_prefix = "sqlite:///"
    if not raw_database_url.startswith(sqlite_prefix):
        return raw_database_url

    sqlite_path = raw_database_url[len(sqlite_prefix):]
    if sqlite_path.startswith("/"):
        return raw_database_url

    resolved_path = (BASE_DIR.parent / sqlite_path).resolve()
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{resolved_path.as_posix()}"


DATABASE_URL = _normalize_database_url(getenv("DATABASE_URL"))

APP_HOST = getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(getenv("APP_PORT", "8000"))
