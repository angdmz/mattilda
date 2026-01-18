from uuid import UUID
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from moneyed import Money
from app.models import Student, School, Invoice, PaymentImputation
from app.schemas.account_statement import (
    StudentAccountStatement, SchoolAccountStatement,
    MoneyAmount, InvoiceDetail, StudentSummary
)
from app.money import currency, cents_from_money, money_from_cents
import logging

logger = logging.getLogger(__name__)

class AccountStatementService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_student_statement(self, student_id: UUID) -> StudentAccountStatement:
        result = await self.db.execute(
            select(Student)
            .options(
                selectinload(Student.school),
                selectinload(Student.invoices).selectinload(Invoice.payment_imputations)
            )
            .where(Student.id == student_id)
        )
        student = result.scalar_one_or_none()
        if not student:
            raise ValueError(f"Student {student_id} not found")
        
        currency_code = student.invoices[0].currency if student.invoices else "USD"
        cur = currency(currency_code)
        total_invoiced_money = Money(0, cur)
        total_paid_money = Money(0, cur)
        invoice_details = []
        
        for invoice in student.invoices:
            if invoice.currency != currency_code:
                raise ValueError("Mixed currencies are not supported in a single student statement")
            
            total_invoiced_money += money_from_cents(invoice.amount_cents, currency_code)
            
            paid_amount_cents = sum(imp.amount_cents for imp in invoice.payment_imputations)
            total_paid_money += money_from_cents(paid_amount_cents, currency_code)
            
            invoice_details.append(InvoiceDetail(
                id=invoice.id,
                amount=MoneyAmount(amount_cents=invoice.amount_cents, currency=invoice.currency),
                paid_amount=MoneyAmount(amount_cents=paid_amount_cents, currency=invoice.currency),
                outstanding_amount=MoneyAmount(amount_cents=invoice.amount_cents - paid_amount_cents, currency=invoice.currency),
                issued_at=invoice.issued_at,
                description=invoice.description
            ))
        
        return StudentAccountStatement(
            student_id=student.id,
            student_name=student.name,
            school_id=student.school.id,
            school_name=student.school.name,
            total_invoiced=MoneyAmount(amount_cents=cents_from_money(total_invoiced_money), currency=currency_code),
            total_paid=MoneyAmount(amount_cents=cents_from_money(total_paid_money), currency=currency_code),
            total_outstanding=MoneyAmount(amount_cents=cents_from_money(total_invoiced_money - total_paid_money), currency=currency_code),
            invoices=invoice_details
        )

    async def get_school_statement(self, school_id: UUID) -> SchoolAccountStatement:
        result = await self.db.execute(
            select(School)
            .options(
                selectinload(School.students).selectinload(Student.invoices).selectinload(Invoice.payment_imputations)
            )
            .where(School.id == school_id)
        )
        school = result.scalar_one_or_none()
        if not school:
            raise ValueError(f"School {school_id} not found")
        
        currency_code = None
        total_invoiced_money = None
        total_paid_money = None
        student_summaries = []
        
        for student in school.students:
            student_invoiced_cents = 0
            student_paid_cents = 0
            student_currency = None
            
            logger.debug(f"Processing student: {student.name}, invoices count: {len(student.invoices)}")
            
            for invoice in student.invoices:
                if currency_code is None:
                    currency_code = invoice.currency
                    cur = currency(currency_code)
                    total_invoiced_money = Money(0, cur)
                    total_paid_money = Money(0, cur)
                    logger.debug(f"Initialized currency: {currency_code}")
                elif invoice.currency != currency_code:
                    raise ValueError("Mixed currencies are not supported in a single school statement")
                
                student_currency = invoice.currency
                invoice_amount = invoice.amount_cents
                student_invoiced_cents += invoice_amount
                
                paid_amount = sum(imp.amount_cents for imp in invoice.payment_imputations)
                student_paid_cents += paid_amount
                logger.debug(f"Invoice {invoice.id}: amount={invoice_amount}, paid={paid_amount}, imputations count={len(invoice.payment_imputations)}")

            logger.debug(f"Student totals: invoiced={student_invoiced_cents}, paid={student_paid_cents}, currency={student_currency}")
            
            # Only add to totals and summaries if student has invoices
            if student_currency is not None:
                total_invoiced_money += money_from_cents(student_invoiced_cents, currency_code)
                total_paid_money += money_from_cents(student_paid_cents, currency_code)
                student_outstanding = student_invoiced_cents - student_paid_cents
                
                logger.debug(f"Adding to totals: total_invoiced={total_invoiced_money}, total_paid={total_paid_money}")
                
                student_summaries.append(StudentSummary(
                    student_id=student.id,
                    student_name=student.name,
                    total_outstanding=MoneyAmount(amount_cents=student_outstanding, currency=currency_code)
                ))
        
        # Handle case where school has no students or no invoices
        if currency_code is None:
            currency_code = "USD"
            cur = currency(currency_code)
            total_invoiced_money = Money(0, cur)
            total_paid_money = Money(0, cur)
        
        return SchoolAccountStatement(
            school_id=school.id,
            school_name=school.name,
            total_invoiced=MoneyAmount(amount_cents=cents_from_money(total_invoiced_money), currency=currency_code),
            total_paid=MoneyAmount(amount_cents=cents_from_money(total_paid_money), currency=currency_code),
            total_outstanding=MoneyAmount(amount_cents=cents_from_money(total_invoiced_money - total_paid_money), currency=currency_code),
            number_of_students=len(school.students),
            students=student_summaries
        )
