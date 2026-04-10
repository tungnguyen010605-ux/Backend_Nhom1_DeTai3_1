from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


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


class ClothingItem(Base):
    __tablename__ = "clothing_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_profiles.id"), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    size_label = Column(String(20), nullable=False)
    color = Column(String(30), nullable=False)
    image_path = Column(String(300), nullable=True)

    owner = relationship("UserProfile", back_populates="clothing_items")

