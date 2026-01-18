import sqlalchemy as sa

from app.enums import PaymentMethod

payment_method_type = sa.Enum(PaymentMethod, name="enum_payment_method_type")


