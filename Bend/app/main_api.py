from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db
from app.models import ClothingItem, UserProfile
from app.schemas import (
    BodyData,
    ClothingItemCreate,
    ClothingItemResponse,
    TaskCreateRequest,
    TaskStatus,
    UserCreate,
    UserResponse,
)
from app.services.mock_vr import build_mock_body_data
from app.services.preprocess import preprocess_image_bytes
from app.services.tasks import TaskManager

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
TEXTURE_DIR = BASE_DIR / "static" / "textures"
FRONTEND_DIR = BASE_DIR / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = PROJECT_ROOT / "Fend"
TEXTURE_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="CPU-Friendly Data Backend", version="1.0.0")
app.mount("/textures", StaticFiles(directory=TEXTURE_DIR), name="textures")
app.mount("/ui/static", StaticFiles(directory=FRONTEND_DIR), name="ui-static")


def persist_task_output(user_id: int, clothing_item_id: int, output_url: str) -> None:
    db = SessionLocal()
    try:
        cloth = (
            db.query(ClothingItem)
            .filter(ClothingItem.id == clothing_item_id, ClothingItem.user_id == user_id)
            .first()
        )
        if not cloth:
            raise ValueError("Clothing item not found for user")
        cloth.image_path = output_url
        db.commit()
    finally:
        db.close()


task_manager = TaskManager(
    output_dir=TEXTURE_DIR,
    max_concurrent_jobs=2,
    on_task_completed=persist_task_output,
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


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

    return build_mock_body_data(
        user_id=user.id,
        height_cm=user.height_cm,
        chest_cm=user.chest_cm,
        waist_cm=user.waist_cm,
        hip_cm=user.hip_cm,
        inseam_cm=user.inseam_cm,
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

    cloth = (
        db.query(ClothingItem)
        .filter(ClothingItem.id == payload.clothing_item_id, ClothingItem.user_id == payload.user_id)
        .first()
    )
    if not cloth:
        raise HTTPException(status_code=404, detail="Clothing item not found for user")

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
