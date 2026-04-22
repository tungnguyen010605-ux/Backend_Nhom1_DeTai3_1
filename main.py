"""Root-level compatibility wrapper for the FastAPI app.

This module exposes the backend app from `Bend.app.main_api` while also
registering compatibility aliases so imports like `app.database` continue to
work when the project is launched from the workspace root.
"""

from __future__ import annotations

import importlib
import sys

from Bend.app.config import APP_HOST, APP_PORT

_ALIAS_MAP = {
    "app.database": "Bend.app.database",
    "app.models": "Bend.app.models",
    "app.schemas": "Bend.app.schemas",
    "app.services": "Bend.app.services",
    "app.services.mock_vr": "Bend.app.services.mock_vr",
    "app.services.preprocess": "Bend.app.services.preprocess",
    "app.services.tasks": "Bend.app.services.tasks",
}

for alias, target in _ALIAS_MAP.items():
    sys.modules.setdefault(alias, importlib.import_module(target))

from Bend.app.main_api import app

__all__ = ["app"]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=APP_HOST, port=APP_PORT)



