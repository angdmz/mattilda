from pydantic import BaseModel, Field
from uuid import UUID


class PaymentImputationCreate(BaseModel):
    payment_id: UUID
    invoice_id: UUID
    amount_cents: int = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)


class PaymentImputationResponse(BaseModel):
    id: UUID
    payment_id: UUID
    invoice_id: UUID
    amount_cents: int
    currency: str

    class Config:
        from_attributes = True
