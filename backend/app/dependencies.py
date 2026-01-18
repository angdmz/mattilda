from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.cache import RedisCache
from app.services import (
    AccountStatementService,
    InvoiceService,
    PaymentService,
    SchoolService,
    StudentService,
)

# Cache instance - created once per application lifecycle
_cache_instance = None


async def get_cache() -> RedisCache:
    """Get or create Redis cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = RedisCache()
    return _cache_instance


async def get_school_service(db: AsyncSession = Depends(get_db)) -> SchoolService:
    return SchoolService(db)


async def get_student_service(db: AsyncSession = Depends(get_db)) -> StudentService:
    return StudentService(db)


async def get_invoice_service(
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
) -> InvoiceService:
    return InvoiceService(db, cache)


async def get_payment_service(
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
) -> PaymentService:
    return PaymentService(db, cache)


async def get_account_statement_service(
    db: AsyncSession = Depends(get_db),
    cache: RedisCache = Depends(get_cache)
) -> AccountStatementService:
    return AccountStatementService(db, cache)
