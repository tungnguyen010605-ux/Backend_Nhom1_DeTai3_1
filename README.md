# CPU-Friendly FastAPI Backend

This project implements the requirements from your screenshots using a lightweight stack that runs on CPU-only laptops.

## What is included

- FastAPI + Pydantic validation for strict request/response schemas.
- SQLite + SQLAlchemy for user profiles and clothing items.
- Mock VR body-data endpoint for Unity/backend integration testing.
- Async texture generation with `task_id` and polling endpoint `/status/{task_id}`.
- Completed texture tasks automatically persist `output_url` into `ClothingItem.image_path`.
- WebSocket endpoint for task updates: `/ws/tasks/{task_id}`.
- Static file serving from `/textures/...`.
- Image preprocessing endpoint with resize, normalize, optional augment.

## Project layout

- `Bend/` - backend (FastAPI, DB, tests, static textures).
- `Fend/` - frontend (HTML/CSS/JS UI).

Main backend files:

- `main.py` - local runner from project root.
- `Bend/app/main_api.py` - FastAPI app and endpoints.
- `Bend/app/database.py` - SQLite connection/session.
- `Bend/app/models.py` - SQLAlchemy models.
- `Bend/app/schemas.py` - Pydantic schemas.
- `Bend/app/services/preprocess.py` - CPU-safe image preprocessing.
- `Bend/app/services/mock_vr.py` - mock body measurement generator.
- `Bend/app/services/tasks.py` - async task manager with progress updates.
- `Bend/smoke_test.py` - tiny end-to-end test.

## Quick start

```powershell
python -m pip install -r Bend/requirements.txt
python main.py
```

Open docs:

- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/ui` (web frontend)

## Run smoke test

```powershell
python Bend/smoke_test.py
```

## CP-VTON checkpoint integration

This backend now supports loading a real CP-VTON TOM checkpoint at startup.

1. Place your checkpoint file (example):

```text
Bend/ml_pipeline/checkpoints/cpvton_tom_latest.pth
```

2. Optional environment variables:

```powershell
$env:VTON_CHECKPOINT_PATH="C:\path\to\cpvton_tom_latest.pth"
$env:VTON_MODEL_TYPE="cpvton_tom"
$env:VTON_INPUT_CHANNELS="25"
$env:VTON_OUTPUT_CHANNELS="4"
$env:VTON_USE_FP16="true"
```

3. Upload a person reference image used during fitting:

```powershell
curl -X POST "http://127.0.0.1:8000/users/1/reference-image" -F "file=@person.jpg"
```

Notes:

- `/tasks/generate-texture` now uses person reference image + clothing image when available.
- If either input image or checkpoint is missing, runtime falls back to deterministic texture output.

## Run benchmarks locally

One command to start backend, run latency benchmark, run VRAM benchmark, and stop backend:

```powershell
python Bend/scripts/run_benchmarks_local.py --user-id 1 --clothing-item-id 1 --rounds 10
```

Skip VRAM benchmark:

```powershell
python Bend/scripts/run_benchmarks_local.py --user-id 1 --clothing-item-id 1 --rounds 10 --skip-vram
```

## Notes for your hardware

- Concurrency is limited to 2 background jobs to avoid CPU spikes.
- Image size is capped at 1024x1024 in preprocessing.
- Augmentation is intentionally simple and cheap.

