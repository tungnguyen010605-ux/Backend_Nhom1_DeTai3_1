from __future__ import annotations

from os import getenv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(getenv("DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path(getenv("DB_PATH", str(DATA_DIR / "app.db")))
DATABASE_URL = getenv("DATABASE_URL", f"sqlite:///{DB_PATH.as_posix()}")

APP_HOST = getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(getenv("APP_PORT", "8000"))
