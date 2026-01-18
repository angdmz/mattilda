from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import School, Student
from app.schemas import SchoolCreate, SchoolUpdate


class SchoolService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_school(self, school_data: SchoolCreate) -> School:
        school = School(**school_data.model_dump())
        self.db.add(school)
        await self.db.commit()
        await self.db.refresh(school)
        return school

    async def get_school(self, school_id: UUID) -> Optional[School]:
        result = await self.db.execute(
            select(School).where(School.id == school_id)
        )
        return result.scalar_one_or_none()

    async def get_schools(self, skip: int = 0, limit: int = 100) -> List[School]:
        result = await self.db.execute(
            select(School).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def update_school(self, school_id: UUID, school_data: SchoolUpdate) -> Optional[School]:
        school = await self.get_school(school_id)
        if not school:
            return None
        
        update_data = school_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(school, field, value)
        
        await self.db.commit()
        await self.db.refresh(school)
        return school

    async def delete_school(self, school_id: UUID) -> bool:
        school = await self.get_school(school_id)
        if not school:
            return False
        
        await self.db.delete(school)
        await self.db.commit()
        return True

    async def get_student_count(self, school_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count(Student.id)).where(Student.school_id == school_id)
        )
        return result.scalar() or 0
