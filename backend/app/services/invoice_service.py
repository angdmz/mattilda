from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Invoice
from app.schemas import InvoiceCreate, InvoiceUpdate
from app.money import currency


class InvoiceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_invoice(self, invoice_data: InvoiceCreate) -> Invoice:
        currency(invoice_data.currency)
        invoice = Invoice(**invoice_data.model_dump())
        self.db.add(invoice)
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice

    async def get_invoice(self, invoice_id: UUID) -> Optional[Invoice]:
        result = await self.db.execute(
            select(Invoice).where(Invoice.id == invoice_id)
        )
        return result.scalar_one_or_none()

    async def get_invoices(self, skip: int = 0, limit: int = 100, student_id: Optional[UUID] = None) -> List[Invoice]:
        query = select(Invoice)
        if student_id:
            query = query.where(Invoice.student_id == student_id)
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_invoice(self, invoice_id: UUID, invoice_data: InvoiceUpdate) -> Optional[Invoice]:
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return None

        if invoice_data.currency is not None:
            currency(invoice_data.currency)
        
        update_data = invoice_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(invoice, field, value)
        
        await self.db.commit()
        await self.db.refresh(invoice)
        return invoice

    async def delete_invoice(self, invoice_id: UUID) -> bool:
        invoice = await self.get_invoice(invoice_id)
        if not invoice:
            return False
        
        await self.db.delete(invoice)
        await self.db.commit()
        return True
