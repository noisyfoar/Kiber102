from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from . import crud, models
from .db import get_session

router = APIRouter(tags=["users"])


@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/users", response_model=List[models.UserRead])
def list_users(
    limit: int = 100,
    db: Session = Depends(get_session),
) -> List[models.UserRead]:
    return list(crud.list_users(db, limit=limit))


@router.get("/users/{user_id}", response_model=models.UserRead)
def get_user(user_id: int, db: Session = Depends(get_session)) -> models.UserRead:
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.post("/auth/register", response_model=models.UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: models.UserCreate, db: Session = Depends(get_session)) -> models.UserRead:
    # Проверяем, существует ли пользователь с таким телефоном
    existing_user = crud.get_user_by_phone(db, payload.phone)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь с таким номером телефона уже зарегистрирован"
        )
    return crud.create_user(db, payload)


@router.post("/auth/login", response_model=models.UserRead)
def login(payload: models.UserLogin, db: Session = Depends(get_session)) -> models.UserRead:
    user = crud.get_user_by_phone(db, payload.phone)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден. Пожалуйста, зарегистрируйтесь."
        )
    return user


@router.get("/users/{user_id}/sessions", response_model=List[models.DreamSessionRead])
def get_user_sessions(
    user_id: int,
    limit: int = 20,
    db: Session = Depends(get_session),
) -> List[models.DreamSessionRead]:
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return crud.list_sessions(db, user_id=user_id, limit=limit)


@router.post(
    "/users/{user_id}/sessions",
    response_model=models.DreamSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    user_id: int,
    payload: models.DreamSessionCreate,
    db: Session = Depends(get_session),
) -> models.DreamSessionRead:
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return crud.create_session(db, user_id=user_id, payload=payload)


@router.delete("/users/{user_id}/sessions", status_code=status.HTTP_204_NO_CONTENT)
def delete_sessions(
    user_id: int,
    db: Session = Depends(get_session),
) -> None:
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    crud.delete_sessions(db, user_id=user_id)
