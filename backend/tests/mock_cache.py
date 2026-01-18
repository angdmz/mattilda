from typing import Optional, Dict, List
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


class MockCache:
    """Mock cache for testing that tracks all operations."""
    
    def __init__(self):
        self._store: Dict[str, dict] = {}
        self.get_calls: List[str] = []
        self.set_calls: List[tuple[str, dict, int]] = []
        self.delete_calls: List[str] = []
        self.delete_pattern_calls: List[str] = []
    
    async def get_client(self):
        """Mock get_client - not needed for mock."""
        return None
    
    async def close(self):
        """Mock close - not needed for mock."""
        pass
    
    async def get(self, key: str) -> Optional[dict]:
        """Get cached value by key and track the call."""
        self.get_calls.append(key)
        value = self._store.get(key)
        if value:
            logger.debug(f"MockCache HIT: {key}")
        else:
            logger.debug(f"MockCache MISS: {key}")
        return value
    
    async def set(self, key: str, value: dict, ttl: int = 3600):
        """Set cached value and track the call."""
        self.set_calls.append((key, value, ttl))
        self._store[key] = value
        logger.debug(f"MockCache SET: {key} (TTL: {ttl}s)")
    
    async def delete(self, key: str):
        """Delete cached value and track the call."""
        self.delete_calls.append(key)
        if key in self._store:
            del self._store[key]
        logger.debug(f"MockCache DELETE: {key}")
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern and track the call."""
        self.delete_pattern_calls.append(pattern)
        # Simple pattern matching for testing
        keys_to_delete = [k for k in self._store.keys() if pattern.replace('*', '') in k]
        for key in keys_to_delete:
            del self._store[key]
        logger.debug(f"MockCache DELETE pattern: {pattern} ({len(keys_to_delete)} keys)")
    
    def reset(self):
        """Reset all tracking and storage."""
        self._store.clear()
        self.get_calls.clear()
        self.set_calls.clear()
        self.delete_calls.clear()
        self.delete_pattern_calls.clear()
    
    def was_get_called_with(self, key: str) -> bool:
        """Check if get was called with specific key."""
        return key in self.get_calls
    
    def was_set_called_with(self, key: str) -> bool:
        """Check if set was called with specific key."""
        return any(k == key for k, _, _ in self.set_calls)
    
    def was_delete_called_with(self, key: str) -> bool:
        """Check if delete was called with specific key."""
        return key in self.delete_calls
    
    def get_call_count(self) -> int:
        """Get total number of get calls."""
        return len(self.get_calls)
    
    def set_call_count(self) -> int:
        """Get total number of set calls."""
        return len(self.set_calls)
    
    def delete_call_count(self) -> int:
        """Get total number of delete calls."""
        return len(self.delete_calls)
