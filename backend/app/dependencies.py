from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.services import (
    AccountStatementService,
    InvoiceService,
    PaymentService,
    SchoolService,
    StudentService,
)


async def get_school_service(db: AsyncSession = Depends(get_db)) -> SchoolService:
    return SchoolService(db)


async def get_student_service(db: AsyncSession = Depends(get_db)) -> StudentService:
    return StudentService(db)


async def get_invoice_service(db: AsyncSession = Depends(get_db)) -> InvoiceService:
    return InvoiceService(db)


async def get_payment_service(db: AsyncSession = Depends(get_db)) -> PaymentService:
    return PaymentService(db)


async def get_account_statement_service(
    db: AsyncSession = Depends(get_db),
) -> AccountStatementService:
    return AccountStatementService(db)
