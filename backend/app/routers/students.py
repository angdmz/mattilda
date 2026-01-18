from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.dependencies import get_student_service
from app.services import StudentService
from app.schemas import StudentCreate, StudentUpdate, StudentResponse
from app.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/students", tags=["students"])


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_data: StudentCreate,
    service: StudentService = Depends(get_student_service),
    current_user: User = Depends(get_current_active_user),
):
    student = await service.create_student(student_data)
    return student


@router.get("/", response_model=List[StudentResponse])
async def list_students(
    skip: int = 0,
    limit: int = 100,
    school_id: Optional[UUID] = Query(None),
    service: StudentService = Depends(get_student_service),
    current_user: User = Depends(get_current_active_user),
):
    students = await service.get_students(skip=skip, limit=limit, school_id=school_id)
    return students


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: UUID,
    service: StudentService = Depends(get_student_service),
    current_user: User = Depends(get_current_active_user),
):
    student = await service.get_student(student_id)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@router.put("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: UUID,
    student_data: StudentUpdate,
    service: StudentService = Depends(get_student_service),
    current_user: User = Depends(get_current_active_user),
):
    student = await service.update_student(student_id, student_data)
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(
    student_id: UUID,
    service: StudentService = Depends(get_student_service),
    current_user: User = Depends(get_current_active_user),
):
    deleted = await service.delete_student(student_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
