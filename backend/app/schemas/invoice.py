from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from datetime import datetime


class InvoiceBase(BaseModel):
    student_id: UUID
    amount_cents: int = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    description: Optional[str] = None
    due_date: Optional[datetime] = None


class InvoiceCreate(InvoiceBase):
    pass


class InvoiceUpdate(BaseModel):
    amount_cents: Optional[int] = Field(None, gt=0)
    currency: Optional[str] = Field(None, max_length=3)
    description: Optional[str] = None
    due_date: Optional[datetime] = None


class InvoiceResponse(InvoiceBase):
    id: UUID
    issued_at: datetime

    class Config:
        from_attributes = True
