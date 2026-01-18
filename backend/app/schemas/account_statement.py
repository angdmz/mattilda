from pydantic import BaseModel
from uuid import UUID
from typing import List
from datetime import datetime


class MoneyAmount(BaseModel):
    amount_cents: int
    currency: str


class InvoiceDetail(BaseModel):
    id: UUID
    amount: MoneyAmount
    paid_amount: MoneyAmount
    outstanding_amount: MoneyAmount
    issued_at: datetime
    description: str | None


class StudentAccountStatement(BaseModel):
    student_id: UUID
    student_name: str
    school_id: UUID
    school_name: str
    total_invoiced: MoneyAmount
    total_paid: MoneyAmount
    total_outstanding: MoneyAmount
    invoices: List[InvoiceDetail]


class StudentSummary(BaseModel):
    student_id: UUID
    student_name: str
    total_outstanding: MoneyAmount


class SchoolAccountStatement(BaseModel):
    school_id: UUID
    school_name: str
    total_invoiced: MoneyAmount
    total_paid: MoneyAmount
    total_outstanding: MoneyAmount
    number_of_students: int
    students: List[StudentSummary]
