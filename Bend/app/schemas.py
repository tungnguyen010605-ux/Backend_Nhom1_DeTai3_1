from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    height_cm: float = Field(gt=50, lt=260)
    chest_cm: float = Field(gt=30, lt=200)
    waist_cm: float = Field(gt=30, lt=200)
    hip_cm: float = Field(gt=30, lt=220)
    inseam_cm: float = Field(gt=20, lt=150)


class UserResponse(UserCreate):
    id: int

    class Config:
        from_attributes = True


class BodyMeasurementCreate(BaseModel):
    user_id: int
    height_cm: float = Field(gt=50, lt=260)
    chest_cm: float = Field(gt=30, lt=200)
    waist_cm: float = Field(gt=30, lt=200)
    hip_cm: float = Field(gt=30, lt=220)
    inseam_cm: float = Field(gt=20, lt=150)
    source: str = Field(default="mediapipe", min_length=2, max_length=50)


class BodyMeasurementResponse(BodyMeasurementCreate):
    id: int

    class Config:
        from_attributes = True


class ClothingItemCreate(BaseModel):
    user_id: int
    category: str = Field(min_length=2, max_length=50)
    size_label: str = Field(min_length=1, max_length=20)
    color: str = Field(min_length=1, max_length=30)
    image_path: str | None = None


class ClothingItemResponse(ClothingItemCreate):
    id: int

    class Config:
        from_attributes = True


class BodyData(BaseModel):
    user_id: int
    height_cm: float
    chest_cm: float
    waist_cm: float
    hip_cm: float
    inseam_cm: float
    shoulder_cm: float
    arm_length_cm: float


class TaskCreateRequest(BaseModel):
    user_id: int
    clothing_item_id: int


class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    message: str
    output_url: str | None = None

