import json
from io import BytesIO
from pathlib import Path
import sys
from uuid import uuid4

from sqlalchemy import text
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from PIL import Image
from sqlalchemy.orm import Session

try:
    from .database import Base, SessionLocal, engine, get_db
    from .models import BodyMeasurement, ClothingItem, UserProfile
    from .schemas import (
        BodyData,
        BodyMeasurementCreate,
        BodyMeasurementResponse,
        ClothingItemCreate,
        ClothingItemResponse,
        PoseEstimateResponse,
        TaskCreateRequest,
        TaskStatus,
        UserCreate,
        UserResponse,
    )
    from .services.mock_vr import build_mock_body_data
    from .services.preprocess import preprocess_image_bytes
    from .services.tasks import TaskManager
except ImportError:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from Bend.app.database import Base, SessionLocal, engine, get_db
    from Bend.app.models import BodyMeasurement, ClothingItem, UserProfile
    from Bend.app.schemas import (
        BodyData,
        BodyMeasurementCreate,
        BodyMeasurementResponse,
        ClothingItemCreate,
        ClothingItemResponse,
        PoseEstimateResponse,
        TaskCreateRequest,
        TaskStatus,
        UserCreate,
        UserResponse,
    )
    from Bend.app.services.mock_vr import build_mock_body_data
    from Bend.app.services.preprocess import preprocess_image_bytes
    from Bend.app.services.tasks import TaskManager

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
TEXTURE_DIR = BASE_DIR / "static" / "textures"
CLOTHING_IMAGE_DIR = BASE_DIR / "static" / "clothing_images"
FRONTEND_DIR = BASE_DIR / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = PROJECT_ROOT / "Fend"
TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
CLOTHING_IMAGE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="CPU-Friendly Data Backend", version="1.0.0")
app.mount("/textures", StaticFiles(directory=TEXTURE_DIR), name="textures")
app.mount("/clothing-images", StaticFiles(directory=CLOTHING_IMAGE_DIR), name="clothing-images")
app.mount("/ui/static", StaticFiles(directory=FRONTEND_DIR), name="ui-static")

_pose_import_error: Exception | None = None
estimate_pose_from_image_bytes = None

try:
    from .services.pose_estimation import estimate_pose_from_image_bytes
except ImportError:
    try:
        from Bend.app.services.pose_estimation import estimate_pose_from_image_bytes
    except ImportError as exc:
        _pose_import_error = exc


def _require_pose_estimator():
    if estimate_pose_from_image_bytes is None:
        detail = (
            "Pose estimation dependencies are not available. "
            "Install Bend/requirements.txt to enable /pose/estimate."
        )
        if _pose_import_error is not None:
            detail = f"{detail} Missing dependency: {_pose_import_error}"
        raise HTTPException(status_code=503, detail=detail)
    return estimate_pose_from_image_bytes


@app.middleware("http")
async def add_no_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith(("/ui", "/textures", "/clothing-images")):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


def _save_uploaded_clothing_image(content: bytes) -> str:
    try:
        image = Image.open(BytesIO(content))
        image.load()
    except Exception as exc:  # pragma: no cover - Pillow validation path
        raise HTTPException(status_code=400, detail="Invalid clothing image file") from exc

    out_path = CLOTHING_IMAGE_DIR / f"clothing_{uuid4().hex}.png"
    image.convert("RGB").save(out_path, format="PNG", optimize=True)
    return f"/clothing-images/{out_path.name}"


def _latest_body_measurement(db: Session, user_id: int) -> BodyMeasurement | None:
    return (
        db.query(BodyMeasurement)
        .filter(BodyMeasurement.user_id == user_id)
        .order_by(BodyMeasurement.created_at.desc(), BodyMeasurement.id.desc())
        .first()
    )


def persist_task_output(user_id: int, clothing_item_id: int, output_url: str) -> None:
    db = SessionLocal()
    try:
        cloth = (
            db.query(ClothingItem)
            .filter(ClothingItem.id == clothing_item_id)
            .first()
        )
        if not cloth:
            raise ValueError("Clothing item not found")
        cloth.image_path = output_url
        db.commit()
    finally:
        db.close()


def _ensure_sqlite_column(table_name: str, column_name: str, column_sql: str) -> None:
    with engine.begin() as connection:
        if connection.dialect.name != "sqlite":
            return
        existing_columns = {
            row[1]
            for row in connection.execute(text(f"PRAGMA table_info({table_name})"))
        }
        if column_name not in existing_columns:
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))


task_manager = TaskManager(
    output_dir=TEXTURE_DIR,
    max_concurrent_jobs=2,
    on_task_completed=persist_task_output,
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_sqlite_column("body_measurements", "keypoints_json", "TEXT")


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok", "mode": "cpu-friendly"}


@app.get("/", include_in_schema=False)
def root() -> RedirectResponse:
    return RedirectResponse(url="/ui")


@app.get("/ui", include_in_schema=False)
def frontend() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.post("/users", response_model=UserResponse)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserProfile:
    user = UserProfile(**payload.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)

    measurement = BodyMeasurement(
        user_id=user.id,
        height_cm=user.height_cm,
        chest_cm=user.chest_cm,
        waist_cm=user.waist_cm,
        hip_cm=user.hip_cm,
        inseam_cm=user.inseam_cm,
        source="user_create",
        keypoints_json=None,
    )
    db.add(measurement)
    db.commit()
    return user


@app.get("/users", response_model=list[UserResponse])
def get_all_users(limit: int = 100, db: Session = Depends(get_db)) -> list[UserProfile]:
    safe_limit = max(1, min(limit, 500))
    return db.query(UserProfile).order_by(UserProfile.id.asc()).limit(safe_limit).all()


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)) -> UserProfile:
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/body-measurements", response_model=BodyMeasurementResponse)
def create_body_measurement(
    payload: BodyMeasurementCreate,
    db: Session = Depends(get_db),
) -> BodyMeasurement:
    user = db.query(UserProfile).filter(UserProfile.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    measurement = BodyMeasurement(**payload.model_dump(exclude={"keypoints"}))
    measurement.keypoints_json = (
        json.dumps([point.model_dump() for point in payload.keypoints], ensure_ascii=True)
        if payload.keypoints
        else None
    )
    db.add(measurement)

    user.height_cm = payload.height_cm
    user.chest_cm = payload.chest_cm
    user.waist_cm = payload.waist_cm
    user.hip_cm = payload.hip_cm
    user.inseam_cm = payload.inseam_cm

    db.commit()
    db.refresh(measurement)
    return measurement


@app.get("/body-measurements", response_model=list[BodyMeasurementResponse])
def get_body_measurements(
    user_id: int | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> list[BodyMeasurement]:
    safe_limit = max(1, min(limit, 500))
    query = db.query(BodyMeasurement)
    if user_id is not None:
        query = query.filter(BodyMeasurement.user_id == user_id)
    return query.order_by(BodyMeasurement.created_at.desc(), BodyMeasurement.id.desc()).limit(safe_limit).all()


@app.get("/body-measurements/latest/{user_id}", response_model=BodyMeasurementResponse)
def get_latest_body_measurement(user_id: int, db: Session = Depends(get_db)) -> BodyMeasurement:
    measurement = _latest_body_measurement(db, user_id)
    if not measurement:
        raise HTTPException(status_code=404, detail="Body measurement not found")
    return measurement


@app.post("/clothing-items", response_model=ClothingItemResponse)
def create_clothing_item(payload: ClothingItemCreate, db: Session = Depends(get_db)) -> ClothingItem:
    user = db.query(UserProfile).filter(UserProfile.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    item = ClothingItem(**payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.post("/clothing-items/upload", response_model=ClothingItemResponse)
async def create_clothing_item_with_image(
    user_id: int = Form(...),
    category: str = Form(...),
    size_label: str = Form(...),
    color: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ClothingItem:
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_bytes = await file.read()
    image_path = _save_uploaded_clothing_image(file_bytes)

    item = ClothingItem(
        user_id=user_id,
        category=category,
        size_label=size_label,
        color=color,
        image_path=image_path,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/clothing-items", response_model=list[ClothingItemResponse])
def get_clothing_items(user_id: int | None = None, limit: int = 100, db: Session = Depends(get_db)) -> list[ClothingItem]:
    safe_limit = max(1, min(limit, 500))
    query = db.query(ClothingItem)
    if user_id is not None:
        query = query.filter(ClothingItem.user_id == user_id)
    return query.order_by(ClothingItem.id.asc()).limit(safe_limit).all()


@app.get("/mock/vr/body/{user_id}", response_model=BodyData)
def mock_vr_body_data(user_id: int, db: Session = Depends(get_db)) -> BodyData:
    user = db.query(UserProfile).filter(UserProfile.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    measurement = _latest_body_measurement(db, user_id)
    source = measurement or user

    return build_mock_body_data(
        user_id=user.id,
        height_cm=source.height_cm,
        chest_cm=source.chest_cm,
        waist_cm=source.waist_cm,
        hip_cm=source.hip_cm,
        inseam_cm=source.inseam_cm,
    )


@app.post("/pose/estimate", response_model=PoseEstimateResponse)
async def estimate_pose(
    file: UploadFile = File(...),
    reference_height_cm: float = Form(...),
) -> PoseEstimateResponse:
    estimate_pose_impl = _require_pose_estimator()
    content = await file.read()
    try:
        frame_result, measurement_estimate = estimate_pose_impl(
            file_bytes=content,
            reference_height_cm=reference_height_cm,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PoseEstimateResponse(
        image_width=frame_result.image_width,
        image_height=frame_result.image_height,
        keypoints=[point.to_dict() for point in frame_result.keypoints],
        measurements=measurement_estimate.to_dict(),
    )


@app.post("/preprocess")
async def preprocess_image(
    file: UploadFile = File(...),
    width: int = 512,
    height: int = 512,
    normalize: bool = True,
    augment: bool = False,
) -> dict:
    content = await file.read()
    out_path, metadata = preprocess_image_bytes(
        file_bytes=content,
        output_dir=TEXTURE_DIR,
        width=width,
        height=height,
        normalize=normalize,
        augment=augment,
    )
    return {
        "file_url": f"/textures/{out_path.name}",
        "metadata": metadata,
    }


@app.post("/tasks/generate-texture", response_model=TaskStatus)
async def generate_texture(payload: TaskCreateRequest, db: Session = Depends(get_db)) -> TaskStatus:
    user = db.query(UserProfile).filter(UserProfile.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    cloth = db.query(ClothingItem).filter(ClothingItem.id == payload.clothing_item_id).first()
    if not cloth:
        raise HTTPException(status_code=404, detail="Clothing item not found")

    return task_manager.create_task(payload.user_id, payload.clothing_item_id)


@app.get("/status/{task_id}", response_model=TaskStatus)
def get_status(task_id: str) -> TaskStatus:
    task = task_manager.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.websocket("/ws/tasks/{task_id}")
async def ws_task_status(websocket: WebSocket, task_id: str) -> None:
    await websocket.accept()

    existing = task_manager.get_task(task_id)
    if not existing:
        await websocket.send_json({"error": "Task not found"})
        await websocket.close(code=1008)
        return

    queue = await task_manager.subscribe(task_id)
    await websocket.send_json(existing.model_dump())

    try:
        while True:
            update = await queue.get()
            await websocket.send_json(update)
            if update["status"] in {"completed", "failed"}:
                break
    except WebSocketDisconnect:
        pass
    finally:
        task_manager.unsubscribe(task_id, queue)
