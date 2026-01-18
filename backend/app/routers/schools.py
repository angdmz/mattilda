from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_school_service
from app.services import SchoolService
from app.schemas import SchoolCreate, SchoolUpdate, SchoolResponse
from app.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/schools", tags=["schools"])


@router.post("/", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
async def create_school(
    school_data: SchoolCreate,
    service: SchoolService = Depends(get_school_service),
    current_user: User = Depends(get_current_active_user),
):
    school = await service.create_school(school_data)
    return school


@router.get("/", response_model=List[SchoolResponse])
async def list_schools(
    skip: int = 0,
    limit: int = 100,
    service: SchoolService = Depends(get_school_service),
    current_user: User = Depends(get_current_active_user),
):
    schools = await service.get_schools(skip=skip, limit=limit)
    return schools


@router.get("/{school_id}", response_model=SchoolResponse)
async def get_school(
    school_id: UUID,
    service: SchoolService = Depends(get_school_service),
    current_user: User = Depends(get_current_active_user),
):
    school = await service.get_school(school_id)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
    return school


@router.put("/{school_id}", response_model=SchoolResponse)
async def update_school(
    school_id: UUID,
    school_data: SchoolUpdate,
    service: SchoolService = Depends(get_school_service),
    current_user: User = Depends(get_current_active_user),
):
    school = await service.update_school(school_id, school_data)
    if not school:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
    return school


@router.delete("/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school(
    school_id: UUID,
    service: SchoolService = Depends(get_school_service),
    current_user: User = Depends(get_current_active_user),
):
    deleted = await service.delete_school(school_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="School not found")
