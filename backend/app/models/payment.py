import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from app.enums import PaymentMethod
from app.models.base import TimestampMixin, SoftDeleteMixin


class Payment(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False)
    amount_cents = Column(Integer, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    payment_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    payment_method = Column(SQLAlchemyEnum(PaymentMethod), nullable=False)
    reference = Column(String, nullable=True)
    
    student = relationship("Student")
    payment_imputations = relationship("PaymentImputation", back_populates="payment", cascade="all, delete-orphan")
