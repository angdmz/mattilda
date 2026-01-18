from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.dependencies import get_invoice_service
from app.services import InvoiceService
from app.schemas import InvoiceCreate, InvoiceUpdate, InvoiceResponse
from app.auth import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    invoice_data: InvoiceCreate,
    service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_active_user),
):
    invoice = await service.create_invoice(invoice_data)
    return invoice


@router.get("/", response_model=List[InvoiceResponse])
async def list_invoices(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[UUID] = Query(None),
    service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_active_user),
):
    invoices = await service.get_invoices(skip=skip, limit=limit, student_id=student_id)
    return invoices


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: UUID,
    service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_active_user),
):
    invoice = await service.get_invoice(invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


@router.put("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice(
    invoice_id: UUID,
    invoice_data: InvoiceUpdate,
    service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_active_user),
):
    invoice = await service.update_invoice(invoice_id, invoice_data)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: UUID,
    service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_active_user),
):
    deleted = await service.delete_invoice(invoice_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
