from __future__ import annotations

from typing import Iterable, Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from . import models


def get_user_by_id(db: Session, user_id: int) -> Optional[models.User]:
    return db.get(models.User, user_id)


def get_user_by_phone(db: Session, phone: str) -> Optional[models.User]:
    stmt = select(models.User).where(models.User.phone == phone)
    return db.execute(stmt).scalar_one_or_none()


def create_user(db: Session, payload: models.UserCreate) -> models.User:
    user = models.User(phone=payload.phone, name=payload.name, birth_date=payload.birth_date)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def upsert_user_by_phone(db: Session, payload: models.UserCreate) -> models.User:
    user = get_user_by_phone(db, payload.phone)
    if user:
        user.name = payload.name or user.name
        user.birth_date = payload.birth_date or user.birth_date
        db.commit()
        db.refresh(user)
        return user
    return create_user(db, payload)


def list_users(db: Session, limit: int = 100) -> Iterable[models.User]:
    stmt = select(models.User).order_by(models.User.created_at.desc()).limit(limit)
    return db.execute(stmt).scalars().all()


def create_session(db: Session, user_id: int, payload: models.DreamSessionCreate) -> models.DreamSession:
    session = models.DreamSession(
        user_id=user_id,
        message=payload.message,
        response=payload.response,
        mood=payload.mood,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def list_sessions(db: Session, user_id: int, limit: int = 20) -> list[models.DreamSession]:
    stmt = (
        select(models.DreamSession)
        .where(models.DreamSession.user_id == user_id)
        .order_by(models.DreamSession.created_at.desc())
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def delete_sessions(db: Session, user_id: int) -> None:
    stmt = delete(models.DreamSession).where(models.DreamSession.user_id == user_id)
    db.execute(stmt)
    db.commit()
