import uuid
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class PaymentImputation(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "payment_imputations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id"), nullable=False)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id"), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    
    payment = relationship("Payment", back_populates="payment_imputations")
    invoice = relationship("Invoice", back_populates="payment_imputations")
