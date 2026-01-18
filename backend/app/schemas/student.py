from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class StudentBase(BaseModel):
    name: str
    email: Optional[str] = None
    school_id: UUID


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    school_id: Optional[UUID] = None


class StudentResponse(StudentBase):
    id: UUID

    class Config:
        from_attributes = True
