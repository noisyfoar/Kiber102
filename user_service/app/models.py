from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255))
    birth_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("DreamSession", back_populates="user", cascade="all, delete-orphan")


class DreamSession(Base):
    __tablename__ = "dream_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    mood = Column(String(50), default="neutral")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="sessions")


class UserBase(BaseModel):
    phone: str = Field(..., min_length=5, max_length=20)
    name: Optional[str] = Field(default=None, max_length=255)
    birth_date: Optional[date] = None


class UserLogin(BaseModel):
    """Модель для авторизации - только телефон"""
    phone: str = Field(..., min_length=5, max_length=20)


class UserCreate(BaseModel):
    """Модель для регистрации - все поля обязательные"""
    phone: str = Field(..., min_length=5, max_length=20)
    name: str = Field(..., min_length=1, max_length=255)
    birth_date: date = Field(...)


class UserRead(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DreamSessionCreate(BaseModel):
    message: str = Field(..., min_length=3, max_length=2000)
    response: str = Field(..., min_length=3, max_length=2000)
    mood: str = Field(default="neutral", max_length=50)


class DreamSessionRead(DreamSessionCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
