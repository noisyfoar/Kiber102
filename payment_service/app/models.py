from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text

from .db import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    invoice_id = Column(String(64), unique=True, nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)
    description = Column(Text)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    paid_at = Column(DateTime, nullable=True)


class PaymentCreate(BaseModel):
    user_id: int = Field(..., gt=0)
    amount: float = Field(..., ge=199.0)
    description: str = Field(..., min_length=3, max_length=255)


class PaymentRead(BaseModel):
    id: int
    user_id: int
    invoice_id: str
    amount: float
    description: str | None
    status: str
    created_at: datetime
    paid_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

