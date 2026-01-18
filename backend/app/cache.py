import json
import redis.asyncio as redis
from typing import Optional, Any
from uuid import UUID
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class UUIDEncoder(json.JSONEncoder):
    """JSON encoder that handles UUID and datetime objects."""
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


class RedisCache:
    def __init__(self, redis_url: str = "redis://redis:6379"):
        self.redis_url = redis_url
        self._client: Optional[redis.Redis] = None
    
    async def get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.close()
    
    async def get(self, key: str) -> Optional[dict]:
        """Get cached value by key."""
        try:
            client = await self.get_client()
            value = await client.get(key)
            if value:
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            logger.debug(f"Cache MISS: {key}")
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: dict, ttl: int = 3600):
        """Set cached value with TTL in seconds (default 1 hour)."""
        try:
            client = await self.get_client()
            await client.setex(key, ttl, json.dumps(value, cls=UUIDEncoder))
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
    
    async def delete(self, key: str):
        """Delete cached value by key."""
        try:
            client = await self.get_client()
            await client.delete(key)
            logger.debug(f"Cache DELETE: {key}")
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        try:
            client = await self.get_client()
            keys = []
            async for key in client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await client.delete(*keys)
                logger.debug(f"Cache DELETE pattern: {pattern} ({len(keys)} keys)")
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")


# Cache key generators
def student_statement_key(student_id: UUID) -> str:
    return f"statement:student:{student_id}"

def school_statement_key(school_id: UUID) -> str:
    return f"statement:school:{school_id}"

def student_pattern(student_id: UUID) -> str:
    """Pattern to match all cache keys related to a student."""
    return f"statement:student:{student_id}*"

def school_pattern(school_id: UUID) -> str:
    """Pattern to match all cache keys related to a school."""
    return f"statement:school:{school_id}*"
