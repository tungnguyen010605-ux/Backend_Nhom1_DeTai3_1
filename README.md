# CPU-Friendly FastAPI Backend

This project implements the requirements from your screenshots using a lightweight stack that runs on CPU-only laptops.

## What is included

- FastAPI + Pydantic validation for strict request/response schemas.
- SQLite + SQLAlchemy for user profiles and clothing items.
- Mock VR body-data endpoint for Unity/backend integration testing.
- Async texture generation with `task_id` and polling endpoint `/status/{task_id}`.
- WebSocket endpoint for task updates: `/ws/tasks/{task_id}`.
- Static file serving from `/textures/...`.
- Image preprocessing endpoint with resize, normalize, optional augment.

## Project files

- `main.py` - local runner.
- `app/main_api.py` - FastAPI app and endpoints.
- `app/database.py` - SQLite connection/session.
- `app/models.py` - SQLAlchemy models.
- `app/schemas.py` - Pydantic schemas.
- `app/services/preprocess.py` - CPU-safe image preprocessing.
- `app/services/mock_vr.py` - mock body measurement generator.
- `app/services/tasks.py` - async task manager with progress updates.
- `smoke_test.py` - tiny end-to-end test.

## Quick start

```powershell
python -m pip install -r requirements.txt
python main.py
```

Open docs:

- `http://127.0.0.1:8000/docs`

## Run smoke test

```powershell
python smoke_test.py
```

## Notes for your hardware

- Concurrency is limited to 2 background jobs to avoid CPU spikes.
- Image size is capped at 1024x1024 in preprocessing.
- Augmentation is intentionally simple and cheap.

