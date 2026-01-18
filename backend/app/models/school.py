import uuid
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class School(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "schools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    
    students = relationship("Student", back_populates="school", cascade="all, delete-orphan")
