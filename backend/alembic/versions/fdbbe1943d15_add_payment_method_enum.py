"""add payment_method enum

Revision ID: fdbbe1943d15
Revises: 001
Create Date: 2026-01-18 05:26:13.051029

"""
from alembic import op
import sqlalchemy as sa


revision = 'fdbbe1943d15'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the enum type
    payment_method_enum = sa.Enum('CASH', 'CREDIT_CARD', 'DEBIT_CARD', 'BANK_TRANSFER', 'WIRE_TRANSFER', 'CHECK', 'OTHER', name='paymentmethod')
    payment_method_enum.create(op.get_bind(), checkfirst=True)
    
    # Alter the column to use the enum type and make it NOT NULL
    op.alter_column('payments', 'payment_method',
               existing_type=sa.VARCHAR(),
               type_=payment_method_enum,
               existing_nullable=True,
               nullable=False,
               postgresql_using='payment_method::paymentmethod')


def downgrade() -> None:
    # Revert column back to VARCHAR
    op.alter_column('payments', 'payment_method',
               existing_type=sa.Enum('CASH', 'CREDIT_CARD', 'DEBIT_CARD', 'BANK_TRANSFER', 'WIRE_TRANSFER', 'CHECK', 'OTHER', name='paymentmethod'),
               type_=sa.VARCHAR(),
               nullable=True)
    
    # Drop the enum type
    sa.Enum(name='paymentmethod').drop(op.get_bind(), checkfirst=True)
