from typing import Literal

from pydantic import BaseModel, Field, model_validator


class PoseKeypointPayload(BaseModel):
    index: int
    name: str = Field(min_length=1, max_length=50)
    x: float
    y: float
    z: float
    pixel_x: int
    pixel_y: int
    visibility: float | None = None


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    gender: Literal["male", "female"] = "male"
    height_cm: float = Field(gt=50, lt=260)
    chest_cm: float = Field(gt=30, lt=200)
    waist_cm: float = Field(gt=30, lt=200)
    hip_cm: float = Field(gt=30, lt=220)
    inseam_cm: float = Field(gt=20, lt=150)


class UserResponse(UserCreate):
    id: int

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    gender: Literal["male", "female"] | None = None
    height_cm: float | None = Field(default=None, gt=50, lt=260)
    chest_cm: float | None = Field(default=None, gt=30, lt=200)
    waist_cm: float | None = Field(default=None, gt=30, lt=200)
    hip_cm: float | None = Field(default=None, gt=30, lt=220)
    inseam_cm: float | None = Field(default=None, gt=20, lt=150)

    @model_validator(mode="after")
    def validate_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update")
        return self


class DeleteUserPreviewResponse(BaseModel):
    user_id: int
    user_name: str
    clothing_item_count: int
    body_measurement_count: int
    warning: str


class DeleteUserResult(BaseModel):
    deleted_user_id: int
    deleted_clothing_item_count: int
    deleted_body_measurement_count: int
    message: str


class BodyMeasurementCreate(BaseModel):
    user_id: int
    height_cm: float = Field(gt=50, lt=260)
    chest_cm: float = Field(gt=30, lt=200)
    waist_cm: float = Field(gt=30, lt=200)
    hip_cm: float = Field(gt=30, lt=220)
    inseam_cm: float = Field(gt=20, lt=150)
    source: str = Field(default="mediapipe", min_length=2, max_length=50)
    keypoints: list[PoseKeypointPayload] | None = None


class BodyMeasurementResponse(BodyMeasurementCreate):
    id: int

    class Config:
        from_attributes = True


class ClothingItemCreate(BaseModel):
    user_id: int
    display_name: str | None = Field(default=None, max_length=120)
    category: str = Field(min_length=2, max_length=50)
    slot: str | None = Field(default=None, max_length=20)
    size_label: str = Field(min_length=1, max_length=20)
    color: str = Field(min_length=1, max_length=30)
    image_path: str | None = None
    preview_image_path: str | None = None
    model_path: str | None = None
    render_mode: Literal["texture", "prefab"] = "texture"
    body_compatibility: list[str] | None = None
    runtime_notes: str | None = None


class ClothingItemResponse(ClothingItemCreate):
    id: int

    class Config:
        from_attributes = True


class ClothingItemUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=120)
    category: str | None = Field(default=None, min_length=2, max_length=50)
    slot: str | None = Field(default=None, max_length=20)
    size_label: str | None = Field(default=None, min_length=1, max_length=20)
    color: str | None = Field(default=None, min_length=1, max_length=30)
    image_path: str | None = None
    preview_image_path: str | None = None
    model_path: str | None = None
    render_mode: Literal["texture", "prefab"] | None = None
    body_compatibility: list[str] | None = None
    runtime_notes: str | None = None

    @model_validator(mode="after")
    def validate_not_empty(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided for update")
        return self


class DeleteClothingItemResult(BaseModel):
    deleted_clothing_item_id: int
    user_id: int
    message: str


class BulkDeleteRequest(BaseModel):
    ids: list[int] = Field(min_length=1)
    confirm: bool = False


class BulkDeleteUsersPreviewResponse(BaseModel):
    requested_ids: list[int]
    found_ids: list[int]
    not_found_ids: list[int]
    total_clothing_item_count: int
    total_body_measurement_count: int
    warning: str


class BulkDeleteUsersResult(BaseModel):
    deleted_user_ids: list[int]
    deleted_clothing_item_count: int
    deleted_body_measurement_count: int
    not_found_ids: list[int]
    message: str


class BulkDeleteClothingResult(BaseModel):
    deleted_clothing_item_ids: list[int]
    not_found_ids: list[int]
    user_id: int | None = None
    message: str


class BodyData(BaseModel):
    user_id: int
    height_cm: float
    chest_cm: float
    waist_cm: float
    hip_cm: float
    inseam_cm: float
    shoulder_cm: float
    arm_length_cm: float


class PoseMeasurementEstimate(BaseModel):
    height_cm: float
    chest_cm: float
    waist_cm: float
    hip_cm: float
    inseam_cm: float
    shoulder_cm: float
    arm_length_cm: float


class PoseEstimateResponse(BaseModel):
    image_width: int
    image_height: int
    keypoints: list[PoseKeypointPayload]
    measurements: PoseMeasurementEstimate


class TaskCreateRequest(BaseModel):
    user_id: int
    clothing_item_id: int


class TaskStatus(BaseModel):
    task_id: str
    status: str
    progress: int = Field(ge=0, le=100)
    message: str
    output_url: str | None = None
