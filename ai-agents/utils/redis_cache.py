"""Redis caching utility for InstaBids API endpoints"""

import json
import hashlib
import os
from typing import Any, Optional, Dict
from datetime import timedelta
import redis
from redis.exceptions import ConnectionError, TimeoutError
import logging

logger = logging.getLogger(__name__)

class RedisCache:
    """Redis cache manager for API response caching"""
    
    def __init__(self):
        """Initialize Redis connection"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            self.client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2
            )
            # Test connection
            self.client.ping()
            self.enabled = True
            logger.info("Redis cache connected successfully")
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis cache not available: {e}")
            self.client = None
            self.enabled = False
    
    def _generate_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Generate cache key from prefix and parameters"""
        # Sort params for consistent key generation
        sorted_params = json.dumps(params, sort_keys=True)
        param_hash = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
        return f"instabids:{prefix}:{param_hash}"
    
    def get(self, key_prefix: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """Get cached value"""
        if not self.enabled:
            return None
            
        try:
            params = params or {}
            cache_key = self._generate_key(key_prefix, params)
            cached_value = self.client.get(cache_key)
            
            if cached_value:
                logger.debug(f"Cache hit for {cache_key}")
                return json.loads(cached_value)
            
            logger.debug(f"Cache miss for {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    def set(
        self, 
        key_prefix: str, 
        value: Any, 
        params: Optional[Dict[str, Any]] = None,
        ttl_seconds: int = 300  # Default 5 minutes
    ) -> bool:
        """Set cached value with TTL"""
        if not self.enabled:
            return False
            
        try:
            params = params or {}
            cache_key = self._generate_key(key_prefix, params)
            serialized_value = json.dumps(value)
            
            self.client.setex(
                cache_key,
                ttl_seconds,
                serialized_value
            )
            
            logger.debug(f"Cache set for {cache_key} with TTL {ttl_seconds}s")
            return True
            
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    def delete(self, key_prefix: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """Delete cached value"""
        if not self.enabled:
            return False
            
        try:
            params = params or {}
            cache_key = self._generate_key(key_prefix, params)
            result = self.client.delete(cache_key)
            
            if result:
                logger.debug(f"Cache deleted for {cache_key}")
            
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.enabled:
            return 0
            
        try:
            full_pattern = f"instabids:{pattern}:*"
            keys = self.client.keys(full_pattern)
            
            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Flushed {deleted} keys matching {full_pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            logger.error(f"Redis flush pattern error: {e}")
            return 0
    
    def invalidate_campaigns(self):
        """Invalidate all campaign-related caches"""
        patterns = [
            "campaigns",
            "campaign_details",
            "contractors",
            "contractor_details",
            "dashboard_stats"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = self.flush_pattern(pattern)
            total_deleted += deleted
        
        logger.info(f"Invalidated {total_deleted} campaign cache entries")
        return total_deleted

# Global cache instance
cache = RedisCache()