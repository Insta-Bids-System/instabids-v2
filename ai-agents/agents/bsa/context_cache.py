"""
BSA Context Cache - TTL caching for static contractor data
Prevents reloading the same data on every message
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
import logging
import hashlib
import json

logger = logging.getLogger(__name__)


class BSAContextCache:
    """TTL cache for BSA context data to avoid constant reloading"""
    
    def __init__(self, default_ttl_seconds: int = 3600):
        """
        Initialize context cache
        
        Args:
            default_ttl_seconds: Default TTL for cached items (1 hour default)
        """
        self.cache: Dict[str, tuple[Any, datetime]] = {}
        self.default_ttl = timedelta(seconds=default_ttl_seconds)
        self.hit_count = 0
        self.miss_count = 0
        
    def _get_cache_key(self, key_type: str, **kwargs) -> str:
        """Generate a unique cache key from parameters"""
        # Create deterministic key from parameters
        key_data = f"{key_type}:" + json.dumps(kwargs, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_or_load(
        self, 
        key: str,
        loader_func: Callable,
        ttl_seconds: Optional[int] = None
    ) -> Any:
        """
        Get cached data or load it if missing/expired
        
        Args:
            key: Cache key
            loader_func: Async function to load data if not cached
            ttl_seconds: Optional custom TTL for this item
            
        Returns:
            Cached or freshly loaded data
        """
        # Check cache
        if key in self.cache:
            data, timestamp = self.cache[key]
            ttl = timedelta(seconds=ttl_seconds) if ttl_seconds else self.default_ttl
            
            if datetime.now() - timestamp < ttl:
                self.hit_count += 1
                logger.debug(f"BSA Cache HIT: {key} (hit rate: {self.get_hit_rate():.1%})")
                return data
        
        # Cache miss - load data
        self.miss_count += 1
        logger.debug(f"BSA Cache MISS: {key} - loading fresh data")
        
        try:
            data = await loader_func()
            self.cache[key] = (data, datetime.now())
            return data
        except Exception as e:
            logger.error(f"BSA Cache: Failed to load data for {key} - {e}")
            raise
    
    async def get_contractor_context(
        self,
        contractor_id: str,
        loader_func: Callable
    ) -> Dict[str, Any]:
        """Get cached contractor context (1 hour TTL)"""
        key = self._get_cache_key("contractor_context", contractor_id=contractor_id)
        return await self.get_or_load(key, loader_func, ttl_seconds=3600)
    
    async def get_ai_memory(
        self,
        contractor_id: str,
        loader_func: Callable
    ) -> str:
        """Get cached AI memory context (30 minute TTL)"""
        key = self._get_cache_key("ai_memory", contractor_id=contractor_id)
        return await self.get_or_load(key, loader_func, ttl_seconds=1800)
    
    async def get_my_bids(
        self,
        contractor_id: str,
        loader_func: Callable
    ) -> Dict[str, Any]:
        """Get cached my bids context (15 minute TTL)"""
        key = self._get_cache_key("my_bids", contractor_id=contractor_id)
        return await self.get_or_load(key, loader_func, ttl_seconds=900)
    
    async def get_company_info(
        self,
        contractor_id: str,
        loader_func: Callable
    ) -> Dict[str, Any]:
        """Get cached company info (2 hour TTL - rarely changes)"""
        key = self._get_cache_key("company_info", contractor_id=contractor_id)
        return await self.get_or_load(key, loader_func, ttl_seconds=7200)
    
    def invalidate(self, key: str):
        """Invalidate a specific cache entry"""
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"BSA Cache: Invalidated {key}")
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching a pattern"""
        keys_to_delete = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.cache[key]
        logger.debug(f"BSA Cache: Invalidated {len(keys_to_delete)} keys matching '{pattern}'")
    
    def clear(self):
        """Clear entire cache"""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0
        logger.info("BSA Cache: Cleared all entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        return {
            "entries": len(self.cache),
            "hit_count": self.hit_count,
            "miss_count": self.miss_count,
            "total_requests": total_requests,
            "hit_rate": self.get_hit_rate(),
            "memory_size_estimate": sum(
                len(str(k)) + len(str(v[0])) for k, v in self.cache.items()
            )
        }
    
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hit_count + self.miss_count
        return self.hit_count / total if total > 0 else 0.0
    
    def cleanup_expired(self):
        """Remove expired entries from cache"""
        now = datetime.now()
        expired_keys = []
        
        for key, (data, timestamp) in self.cache.items():
            if now - timestamp > self.default_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.debug(f"BSA Cache: Cleaned up {len(expired_keys)} expired entries")


# Global cache instance for BSA
bsa_context_cache = BSAContextCache(default_ttl_seconds=3600)