from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Student
from app.schemas import StudentCreate, StudentUpdate


class StudentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_student(self, student_data: StudentCreate) -> Student:
        student = Student(**student_data.model_dump())
        self.db.add(student)
        await self.db.commit()
        await self.db.refresh(student)
        return student

    async def get_student(self, student_id: UUID) -> Optional[Student]:
        result = await self.db.execute(
            select(Student).where(Student.id == student_id)
        )
        return result.scalar_one_or_none()

    async def get_students(self, skip: int = 0, limit: int = 100, school_id: Optional[UUID] = None) -> List[Student]:
        query = select(Student)
        if school_id:
            query = query.where(Student.school_id == school_id)
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_student(self, student_id: UUID, student_data: StudentUpdate) -> Optional[Student]:
        student = await self.get_student(student_id)
        if not student:
            return None
        
        update_data = student_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(student, field, value)
        
        await self.db.commit()
        await self.db.refresh(student)
        return student

    async def delete_student(self, student_id: UUID) -> bool:
        student = await self.get_student(student_id)
        if not student:
            return False
        
        await self.db.delete(student)
        await self.db.commit()
        return True
