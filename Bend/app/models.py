from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

try:
    from .database import Base
except ImportError:  # Allows direct execution of this file in IDE run mode.
    from database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
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
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("UserProfile", back_populates="body_measurements")


class ClothingItem(Base):
    __tablename__ = "clothing_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    size_label = Column(String(20), nullable=False)
    color = Column(String(30), nullable=False)
    image_path = Column(String(300), nullable=True)

    owner = relationship("UserProfile", back_populates="clothing_items")

