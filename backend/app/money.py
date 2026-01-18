from decimal import Decimal, ROUND_HALF_UP

from moneyed import Currency, Money, get_currency


def currency(code: str) -> Currency:
    try:
        return get_currency(code)
    except Exception as e:
        raise ValueError(f"Unsupported currency: {code}") from e


def money_from_cents(amount_cents: int, currency_code: str) -> Money:
    cur = currency(currency_code)
    amount = (Decimal(amount_cents) / Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return Money(amount, cur)


def cents_from_money(m: Money) -> int:
    return int((m.amount * Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
