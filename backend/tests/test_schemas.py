"""
Test schemas - Pydantic models for test data.
These are aliased from the actual application schemas to ensure type safety
and prevent validation errors in tests.
"""
from app.schemas import (
    SchoolCreate as _SchoolCreate,
    SchoolUpdate as _SchoolUpdate,
    StudentCreate as _StudentCreate,
    StudentUpdate as _StudentUpdate,
    InvoiceCreate as _InvoiceCreate,
    InvoiceUpdate as _InvoiceUpdate,
    PaymentCreate as _PaymentCreate,
)
from app.schemas.payment import PaymentImputationInput as _PaymentImputationInput
from app.models.payment import PaymentMethod

# Re-export schemas for tests
SchoolCreate = _SchoolCreate
SchoolUpdate = _SchoolUpdate
StudentCreate = _StudentCreate
StudentUpdate = _StudentUpdate
InvoiceCreate = _InvoiceCreate
InvoiceUpdate = _InvoiceUpdate
PaymentCreate = _PaymentCreate
PaymentImputationInput = _PaymentImputationInput

# Export enum for easy access
PaymentMethod = PaymentMethod


def create_school_data(name: str = "Test School", address: str | None = None) -> dict:
    """Create school data for testing."""
    return SchoolCreate(name=name, address=address).model_dump(mode='json', exclude_none=True)


def create_student_data(name: str, school_id: str, email: str | None = None) -> dict:
    """Create student data for testing."""
    return StudentCreate(name=name, school_id=school_id, email=email).model_dump(mode='json', exclude_none=True)


def create_invoice_data(
    student_id: str,
    amount_cents: int,
    currency: str = "USD",
    description: str | None = None,
    due_date: str | None = None
) -> dict:
    """Create invoice data for testing."""
    return InvoiceCreate(
        student_id=student_id,
        amount_cents=amount_cents,
        currency=currency,
        description=description,
        due_date=due_date
    ).model_dump(mode='json', exclude_none=True)


def create_payment_data(
    student_id: str,
    amount_cents: int,
    invoice_id: str,
    imputation_amount: int | None = None,
    currency: str = "USD",
    payment_method: PaymentMethod = PaymentMethod.CASH,
    reference: str | None = None
) -> dict:
    """Create payment data for testing."""
    if imputation_amount is None:
        imputation_amount = amount_cents
    
    return PaymentCreate(
        student_id=student_id,
        amount_cents=amount_cents,
        currency=currency,
        payment_method=payment_method,
        reference=reference,
        imputations=[
            PaymentImputationInput(
                invoice_id=invoice_id,
                amount_cents=imputation_amount
            )
        ]
    ).model_dump(mode='json', exclude_none=True)
