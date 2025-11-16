from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from . import crud, models
from .db import get_session

router = APIRouter()
# Определяем путь к шаблонам относительно корня проекта
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(parents=True, exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


class PayRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    amount: float = Field(..., ge=199.0)
    description: str = Field(..., min_length=3, max_length=255)


class PayResponse(BaseModel):
    invoice_id: str
    payment_url: str


class ConfirmPaymentRequest(BaseModel):
    amount: float = Field(..., ge=199.0)


@router.post("/pay", response_model=PayResponse)
def pay(payload: PayRequest, db: Session = Depends(get_session)) -> PayResponse:
    """Создать новый платеж и вернуть ссылку на страницу оплаты"""
    from ..config import settings
    
    payment = crud.create_payment(
        db=db,
        user_id=payload.user_id,
        amount=payload.amount,
        description=payload.description,
    )
    
    # Формируем URL для страницы оплаты
    base_url = str(settings.api_gateway_url).rstrip("/")
    payment_url = f"{base_url}/payments/{payment.invoice_id}"
    
    return PayResponse(invoice_id=payment.invoice_id, payment_url=payment_url)


@router.get("/payments/{invoice_id}", response_class=HTMLResponse)
def payment_page(
    invoice_id: str,
    request: Request,
    db: Session = Depends(get_session),
) -> HTMLResponse:
    """Отобразить страницу оплаты"""
    from ..config import settings
    
    payment = crud.get_payment_by_invoice_id(db, invoice_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платеж не найден")
    
    if payment.status == "paid":
        # Если платеж уже оплачен, показываем успешное сообщение
        return templates.TemplateResponse(
            "payment.html",
            {
                "request": request,
                "invoice_id": invoice_id,
                "api_gateway_url": str(settings.api_gateway_url).rstrip("/"),
                "chat_url": None,  # Можно добавить URL чата
                "payment_status": "paid",
                "amount": float(payment.amount),
            },
        )
    
    # Определяем URL чата (можно передать через параметр или настройки)
    chat_url = request.query_params.get("chat_url") or None
    
    return templates.TemplateResponse(
        "payment.html",
        {
            "request": request,
            "invoice_id": invoice_id,
            "api_gateway_url": str(settings.api_gateway_url).rstrip("/"),
            "chat_url": chat_url,
            "payment_status": "pending",
            "amount": float(payment.amount),
        },
    )


@router.post("/payments/{invoice_id}/confirm")
def confirm_payment(
    invoice_id: str,
    payload: ConfirmPaymentRequest,
    db: Session = Depends(get_session),
) -> dict:
    """Подтвердить платеж (отметить как оплаченный)"""
    payment = crud.get_payment_by_invoice_id(db, invoice_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платеж не найден")
    
    if payment.status == "paid":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Платеж уже оплачен")
    
    # Обновляем сумму, если она была изменена пользователем (но не меньше 199)
    if payload.amount >= 199.0 and payload.amount != float(payment.amount):
        payment.amount = payload.amount
        db.commit()
        db.refresh(payment)
    
    payment = crud.mark_payment_paid(db, invoice_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при обновлении платежа")
    
    return {
        "status": "success",
        "invoice_id": invoice_id,
        "amount": float(payment.amount),
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
    }


class CallbackRequest(BaseModel):
    invoice_id: str


@router.post("/callback")
def callback(payload: CallbackRequest, db: Session = Depends(get_session)) -> dict:
    """Callback для внешних платежных систем (заглушка)"""
    payment = crud.mark_payment_paid(db, payload.invoice_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="invoice not found")
    return {"status": "ok", "invoice_id": payload.invoice_id}
