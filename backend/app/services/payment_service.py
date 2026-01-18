from uuid import UUID
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from moneyed import Money
from app.models import Payment, PaymentImputation, Invoice
from app.schemas import PaymentCreate
from app.money import currency, money_from_cents


class PaymentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_payment(self, payment_data: PaymentCreate) -> Payment:
        cur = currency(payment_data.currency)
        payment_total = money_from_cents(payment_data.amount_cents, payment_data.currency)
        imputed_total = Money(0, cur)
        
        for imputation_input in payment_data.imputations:
            invoice = await self.db.get(Invoice, imputation_input.invoice_id)
            if not invoice:
                raise ValueError(f"Invoice {imputation_input.invoice_id} not found")
            if invoice.student_id != payment_data.student_id:
                raise ValueError(f"Invoice {imputation_input.invoice_id} does not belong to student {payment_data.student_id}")
            if invoice.currency != payment_data.currency:
                raise ValueError(f"Invoice currency {invoice.currency} does not match payment currency {payment_data.currency}")

            paid_cents = await self.db.scalar(
                select(func.coalesce(func.sum(PaymentImputation.amount_cents), 0)).where(
                    PaymentImputation.invoice_id == invoice.id
                )
            )
            outstanding_cents = invoice.amount_cents - int(paid_cents or 0)
            if imputation_input.amount_cents > outstanding_cents:
                raise ValueError(f"Imputation exceeds outstanding amount for invoice {invoice.id}")

            imputed_total += money_from_cents(imputation_input.amount_cents, payment_data.currency)

        if imputed_total != payment_total:
            raise ValueError("Total imputation amount must equal payment amount")
        
        payment = Payment(
            student_id=payment_data.student_id,
            amount_cents=payment_data.amount_cents,
            currency=payment_data.currency,
            payment_method=payment_data.payment_method,
            reference=payment_data.reference
        )
        self.db.add(payment)
        await self.db.flush()
        
        for imputation_input in payment_data.imputations:
            imputation = PaymentImputation(
                payment_id=payment.id,
                invoice_id=imputation_input.invoice_id,
                amount_cents=imputation_input.amount_cents,
                currency=payment_data.currency
            )
            self.db.add(imputation)
        
        await self.db.commit()
        await self.db.refresh(payment)
        return payment

    async def get_payment(self, payment_id: UUID) -> Optional[Payment]:
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_payments(self, skip: int = 0, limit: int = 100, student_id: Optional[UUID] = None) -> List[Payment]:
        query = select(Payment)
        if student_id:
            query = query.where(Payment.student_id == student_id)
        query = query.offset(skip).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_payment(self, payment_id: UUID) -> bool:
        payment = await self.get_payment(payment_id)
        if not payment:
            return False
        
        await self.db.delete(payment)
        await self.db.commit()
        return True
