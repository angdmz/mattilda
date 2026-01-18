from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class SchoolBase(BaseModel):
    name: str
    address: Optional[str] = None


class SchoolCreate(SchoolBase):
    pass


class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None


class SchoolResponse(SchoolBase):
    id: UUID

    class Config:
        from_attributes = True
