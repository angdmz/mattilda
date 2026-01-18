import enum


class PaymentMethod(str, enum.Enum):
    """Payment method options for payments."""
    CASH = "cash"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    WIRE_TRANSFER = "wire_transfer"
    CHECK = "check"
    OTHER = "other"
