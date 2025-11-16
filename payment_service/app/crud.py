from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from . import models


def create_payment(db: Session, user_id: int, amount: float, description: str) -> models.Payment:
    """Создать новый платеж"""
    invoice_id = uuid4().hex
    payment = models.Payment(
        user_id=user_id,
        invoice_id=invoice_id,
        amount=amount,
        description=description,
        status="pending",
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_payment_by_invoice_id(db: Session, invoice_id: str) -> Optional[models.Payment]:
    """Получить платеж по invoice_id"""
    return db.query(models.Payment).filter(models.Payment.invoice_id == invoice_id).first()


def mark_payment_paid(db: Session, invoice_id: str) -> Optional[models.Payment]:
    """Отметить платеж как оплаченный"""
    payment = get_payment_by_invoice_id(db, invoice_id)
    if payment and payment.status == "pending":
        payment.status = "paid"
        payment.paid_at = datetime.utcnow()
        db.commit()
        db.refresh(payment)
    return payment


def get_user_payments(db: Session, user_id: int, limit: int = 100) -> list[models.Payment]:
    """Получить платежи пользователя"""
    return (
        db.query(models.Payment)
        .filter(models.Payment.user_id == user_id)
        .order_by(models.Payment.created_at.desc())
        .limit(limit)
        .all()
    )

