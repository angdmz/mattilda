from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

T = TypeVar('T')


class CursorPage(BaseModel, Generic[T]):
    """Cursor-based pagination response."""
    items: List[T]
    next_cursor: Optional[str] = None
    has_more: bool = False
    
    class Config:
        arbitrary_types_allowed = True


class CursorPagination:
    """Cursor-based pagination using created_at timestamp."""
    
    @staticmethod
    async def paginate(
        db: AsyncSession,
        query: Select,
        limit: int = 20,
        cursor: Optional[str] = None,
        model_class = None
    ):
        """
        Paginate a query using cursor-based pagination.
        
        Args:
            db: Database session
            query: SQLAlchemy select query
            limit: Number of items per page
            cursor: Cursor string (ISO format datetime)
            model_class: Model class for filtering
            
        Returns:
            Tuple of (items, next_cursor, has_more)
        """
        # Parse cursor if provided
        if cursor:
            try:
                cursor_dt = datetime.fromisoformat(cursor)
                query = query.where(model_class.created_at < cursor_dt)
            except (ValueError, AttributeError):
                # Invalid cursor, ignore it
                pass
        
        # Order by created_at descending (newest first)
        query = query.order_by(model_class.created_at.desc())
        
        # Fetch limit + 1 to check if there are more items
        query = query.limit(limit + 1)
        
        result = await db.execute(query)
        items = list(result.scalars().all())
        
        # Check if there are more items
        has_more = len(items) > limit
        if has_more:
            items = items[:limit]
        
        # Generate next cursor from the last item's created_at
        next_cursor = None
        if has_more and items:
            next_cursor = items[-1].created_at.isoformat()
        
        return items, next_cursor, has_more
