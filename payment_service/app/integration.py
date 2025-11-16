from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional
from uuid import uuid4

from ..config import settings


@dataclass
class MockPayment:
    invoice_id: str
    user_id: int
    amount: float
    description: str
    status: str = "pending"
    payment_url: str = field(
        init=False,
        default="",
    )

    def __post_init__(self) -> None:
        self.payment_url = f"{settings.mock_provider_url}/{self.invoice_id}"


_PAYMENTS: Dict[str, MockPayment] = {}


def create_payment_payload(amount: float, description: str, user_id: int) -> Dict[str, str]:
    invoice_id = uuid4().hex
    payment = MockPayment(invoice_id=invoice_id, user_id=user_id, amount=amount, description=description)
    _PAYMENTS[invoice_id] = payment
    return {"invoice_id": invoice_id, "payment_url": payment.payment_url}


def mark_payment_paid(invoice_id: str) -> Optional[MockPayment]:
    payment = _PAYMENTS.get(invoice_id)
    if payment:
        payment.status = "paid"
    return payment
