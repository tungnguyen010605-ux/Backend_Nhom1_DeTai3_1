import json

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

try:
    from .database import Base
except ImportError:  # Allows direct execution of this file in IDE run mode.
    from database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    gender = Column(String(10), nullable=False, default="male")
    height_cm = Column(Float, nullable=False)
    chest_cm = Column(Float, nullable=False)
    waist_cm = Column(Float, nullable=False)
    hip_cm = Column(Float, nullable=False)
    inseam_cm = Column(Float, nullable=False)

    clothing_items = relationship("ClothingItem", back_populates="owner", cascade="all, delete-orphan")
    body_measurements = relationship("BodyMeasurement", back_populates="user", cascade="all, delete-orphan")


class BodyMeasurement(Base):
    __tablename__ = "body_measurements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False, index=True)
    height_cm = Column(Float, nullable=False)
    chest_cm = Column(Float, nullable=False)
    waist_cm = Column(Float, nullable=False)
    hip_cm = Column(Float, nullable=False)
    inseam_cm = Column(Float, nullable=False)
    source = Column(String(50), nullable=False, default="mediapipe")
    keypoints_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("UserProfile", back_populates="body_measurements")

    @property
    def keypoints(self):
        if not self.keypoints_json:
            return None
        try:
            return json.loads(self.keypoints_json)
        except json.JSONDecodeError:
            return None


class ClothingItem(Base):
    __tablename__ = "clothing_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False, index=True)
    display_name = Column(String(120), nullable=True)
    category = Column(String(50), nullable=False)
    slot = Column(String(20), nullable=True)
    size_label = Column(String(20), nullable=False)
    color = Column(String(30), nullable=False)
    image_path = Column(String(300), nullable=True)
    preview_image_path = Column(String(300), nullable=True)
    model_path = Column(String(300), nullable=True)
    render_mode = Column(String(20), nullable=False, default="texture")
    body_compatibility_json = Column(Text, nullable=True)
    runtime_notes = Column(Text, nullable=True)

    owner = relationship("UserProfile", back_populates="clothing_items")

    @property
    def body_compatibility(self):
        if not self.body_compatibility_json:
            return None
        try:
            value = json.loads(self.body_compatibility_json)
        except json.JSONDecodeError:
            return None
        return value if isinstance(value, list) else None
