import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class Student(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "students"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    school_id = Column(UUID(as_uuid=True), ForeignKey("schools.id"), nullable=False)
    
    school = relationship("School", back_populates="students")
    invoices = relationship("Invoice", back_populates="student", cascade="all, delete-orphan")
