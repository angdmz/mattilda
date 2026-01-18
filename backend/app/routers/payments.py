from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.dependencies import get_payment_service
from app.services import PaymentService
from app.schemas import PaymentCreate, PaymentResponse
from app.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        payment = await service.create_payment(payment_data)
        return payment
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/", response_model=List[PaymentResponse])
async def list_payments(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[UUID] = Query(None),
    service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_active_user),
):
    payments = await service.get_payments(skip=skip, limit=limit, student_id=student_id)
    return payments


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_active_user),
):
    payment = await service.get_payment(payment_id)
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


@router.delete("/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(get_current_active_user),
):
    deleted = await service.delete_payment(payment_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
