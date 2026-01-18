from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional, List
from datetime import datetime
from app.enums import PaymentMethod


class PaymentImputationInput(BaseModel):
    invoice_id: UUID
    amount_cents: int = Field(..., gt=0)


class PaymentCreate(BaseModel):
    student_id: UUID
    amount_cents: int = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    payment_method: PaymentMethod
    reference: Optional[str] = None
    imputations: List[PaymentImputationInput]


class PaymentResponse(BaseModel):
    id: UUID
    student_id: UUID
    amount_cents: int
    currency: str
    payment_date: datetime
    payment_method: PaymentMethod
    reference: Optional[str]

    class Config:
        from_attributes = True
