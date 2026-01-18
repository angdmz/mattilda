from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import get_account_statement_service
from app.services import AccountStatementService
from app.schemas import StudentAccountStatement, SchoolAccountStatement
from app.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/account-statements", tags=["account-statements"])


@router.get("/students/{student_id}", response_model=StudentAccountStatement)
async def get_student_statement(
    student_id: UUID,
    service: AccountStatementService = Depends(get_account_statement_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        statement = await service.get_student_statement(student_id)
        return statement
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/schools/{school_id}", response_model=SchoolAccountStatement)
async def get_school_statement(
    school_id: UUID,
    service: AccountStatementService = Depends(get_account_statement_service),
    current_user: User = Depends(get_current_active_user),
):
    try:
        statement = await service.get_school_statement(school_id)
        return statement
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
