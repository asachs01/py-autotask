"""
Intelligent caching system for py-autotask.

Provides multi-layer caching (memory, disk, Redis) with smart invalidation,
automatic expiration, and cache-aside patterns.
"""

import hashlib
import json
import logging
import os
import pickle
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""

    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache."""

    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache entries."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""


class MemoryCache(CacheBackend):
    """In-memory cache backend with TTL support."""

    def __init__(self, max_size: int = 10000, default_ttl: int = 3600):
        """
        Initialize memory cache.

        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict] = {}
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "evictions": 0}

    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None

            entry = self._cache[key]

            # Check if expired
            if entry.get("expires_at", 0) < time.time():
                del self._cache[key]
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            return entry["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in memory cache."""
        with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_oldest()

            expires_at = time.time() + (ttl or self.default_ttl)

            self._cache[key] = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time(),
            }

            self._stats["sets"] += 1
            return True

    def delete(self, key: str) -> bool:
        """Delete key from memory cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._stats["deletes"] += 1
                return True
            return False

    def clear(self) -> bool:
        """Clear all entries from memory cache."""
        with self._lock:
            self._cache.clear()
            return True

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                (self._stats["hits"] / total_requests * 100)
                if total_requests > 0
                else 0
            )

            return {
                **self._stats,
                "entries": len(self._cache),
                "hit_rate": round(hit_rate, 2),
                "memory_usage": self._estimate_memory_usage(),
            }

    def _evict_oldest(self):
        """Evict the oldest entry."""
        if not self._cache:
            return

        oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["created_at"])
        del self._cache[oldest_key]
        self._stats["evictions"] += 1

    def _estimate_memory_usage(self) -> str:
        """Estimate memory usage of cache."""
        try:
            # Rough estimation
            size_bytes = sum(len(pickle.dumps(entry)) for entry in self._cache.values())

            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
        except Exception:
            return "Unknown"


class DiskCache(CacheBackend):
    """Disk-based cache backend with file storage."""

    def __init__(self, cache_dir: str = ".cache/autotask", default_ttl: int = 3600):
        """
        Initialize disk cache.

        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default TTL in seconds
        """
        self.cache_dir = os.path.expanduser(cache_dir)
        self.default_ttl = default_ttl
        self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}

        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_file_path(self, key: str) -> str:
        """Get file path for cache key."""
        # Use hash to handle special characters and long keys
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")

    def get(self, key: str) -> Optional[Any]:
        """Get value from disk cache."""
        file_path = self._get_file_path(key)

        try:
            if not os.path.exists(file_path):
                self._stats["misses"] += 1
                return None

            with open(file_path, "rb") as f:
                entry = pickle.load(f)

            # Check if expired
            if entry.get("expires_at", 0) < time.time():
                os.remove(file_path)
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            return entry["value"]

        except Exception as e:
            logger.debug(f"Error reading cache file {file_path}: {e}")
            self._stats["misses"] += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in disk cache."""
        file_path = self._get_file_path(key)

        try:
            expires_at = time.time() + (ttl or self.default_ttl)

            entry = {
                "value": value,
                "expires_at": expires_at,
                "created_at": time.time(),
            }

            with open(file_path, "wb") as f:
                pickle.dump(entry, f)

            self._stats["sets"] += 1
            return True

        except Exception as e:
            logger.error(f"Error writing cache file {file_path}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from disk cache."""
        file_path = self._get_file_path(key)

        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                self._stats["deletes"] += 1
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting cache file {file_path}: {e}")
            return False

    def clear(self) -> bool:
        """Clear all entries from disk cache."""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith(".cache"):
                    os.remove(os.path.join(self.cache_dir, filename))
            return True

        except Exception as e:
            logger.error(f"Error clearing cache directory: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        # Count cache files
        try:
            cache_files = len(
                [f for f in os.listdir(self.cache_dir) if f.endswith(".cache")]
            )
        except Exception:
            cache_files = 0

        return {
            **self._stats,
            "entries": cache_files,
            "hit_rate": round(hit_rate, 2),
            "cache_dir": self.cache_dir,
        }


class RedisCache(CacheBackend):
    """Redis cache backend."""

    def __init__(
        self, redis_url: str = "redis://localhost:6379/0", default_ttl: int = 3600
    ):
        """
        Initialize Redis cache.

        Args:
            redis_url: Redis connection URL
            default_ttl: Default TTL in seconds
        """
        try:
            import redis

            self.redis = redis.from_url(redis_url)
            self.default_ttl = default_ttl
            self._stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0}

            # Test connection
            self.redis.ping()
            logger.info("Redis cache backend initialized")

        except ImportError:
            raise ImportError("redis package is required for Redis cache backend")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        try:
            data = self.redis.get(key)
            if data is None:
                self._stats["misses"] += 1
                return None

            value = pickle.loads(data)
            self._stats["hits"] += 1
            return value

        except Exception as e:
            logger.error(f"Error getting from Redis cache: {e}")
            self._stats["misses"] += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in Redis cache."""
        try:
            data = pickle.dumps(value)
            expiry = ttl or self.default_ttl

            self.redis.setex(key, expiry, data)
            self._stats["sets"] += 1
            return True

        except Exception as e:
            logger.error(f"Error setting Redis cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        try:
            result = self.redis.delete(key)
            if result > 0:
                self._stats["deletes"] += 1
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting from Redis cache: {e}")
            return False

    def clear(self) -> bool:
        """Clear all entries from Redis cache."""
        try:
            self.redis.flushdb()
            return True

        except Exception as e:
            logger.error(f"Error clearing Redis cache: {e}")
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        try:
            return bool(self.redis.exists(key))
        except Exception:
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = (
            (self._stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        )

        redis_stats = {}
        try:
            info = self.redis.info()
            redis_stats = {
                "redis_memory": info.get("used_memory_human", "Unknown"),
                "redis_connected_clients": info.get("connected_clients", 0),
                "redis_keys": self.redis.dbsize(),
            }
        except Exception:
            pass

        return {**self._stats, "hit_rate": round(hit_rate, 2), **redis_stats}


class SmartCache:
    """
    Intelligent multi-layer cache with automatic failover and optimization.

    Uses multiple backends in order of preference with automatic failover.
    Implements cache-aside pattern with smart invalidation strategies.
    """

    def __init__(
        self,
        backends: Optional[List[CacheBackend]] = None,
        default_ttl: int = 3600,
        key_prefix: str = "autotask",
    ):
        """
        Initialize smart cache system.

        Args:
            backends: List of cache backends in order of preference
            default_ttl: Default TTL in seconds
            key_prefix: Prefix for all cache keys
        """
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix

        # Initialize backends if not provided
        if backends is None:
            backends = []

            # Try Redis first
            try:
                backends.append(RedisCache(default_ttl=default_ttl))
            except Exception as e:
                logger.info(f"Redis not available: {e}")

            # Always add memory and disk cache
            backends.extend(
                [
                    MemoryCache(default_ttl=default_ttl),
                    DiskCache(default_ttl=default_ttl),
                ]
            )

        self.backends = backends
        self._enabled = True

        logger.info(f"SmartCache initialized with {len(self.backends)} backends")

    def _make_key(self, key: str) -> str:
        """Create full cache key with prefix."""
        return f"{self.key_prefix}:{key}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache with automatic promotion.

        Checks backends in order and promotes values to faster caches.
        """
        if not self._enabled:
            return None

        full_key = self._make_key(key)

        for i, backend in enumerate(self.backends):
            try:
                value = backend.get(full_key)
                if value is not None:
                    # Promote to faster caches
                    for j in range(i):
                        try:
                            self.backends[j].set(full_key, value, self.default_ttl)
                        except Exception as e:
                            logger.debug(f"Failed to promote cache entry: {e}")

                    return value
            except Exception as e:
                logger.debug(f"Cache backend {type(backend).__name__} failed: {e}")
                continue

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in all available cache backends."""
        if not self._enabled:
            return False

        full_key = self._make_key(key)
        ttl = ttl or self.default_ttl
        success = False

        for backend in self.backends:
            try:
                if backend.set(full_key, value, ttl):
                    success = True
            except Exception as e:
                logger.debug(f"Cache backend {type(backend).__name__} set failed: {e}")

        return success

    def delete(self, key: str) -> bool:
        """Delete key from all cache backends."""
        if not self._enabled:
            return False

        full_key = self._make_key(key)
        success = False

        for backend in self.backends:
            try:
                if backend.delete(full_key):
                    success = True
            except Exception as e:
                logger.debug(
                    f"Cache backend {type(backend).__name__} delete failed: {e}"
                )

        return success

    def exists(self, key: str) -> bool:
        """Check if key exists in any cache backend."""
        if not self._enabled:
            return False

        full_key = self._make_key(key)

        for backend in self.backends:
            try:
                if backend.exists(full_key):
                    return True
            except Exception as e:
                logger.debug(
                    f"Cache backend {type(backend).__name__} exists check failed: {e}"
                )

        return False

    def clear(self) -> bool:
        """Clear all cache backends."""
        success = False

        for backend in self.backends:
            try:
                if backend.clear():
                    success = True
            except Exception as e:
                logger.error(
                    f"Failed to clear cache backend {type(backend).__name__}: {e}"
                )

        return success

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        stats = {"enabled": self._enabled, "backends": []}

        total_hits = 0
        total_misses = 0

        for backend in self.backends:
            try:
                backend_stats = backend.get_stats()
                backend_stats["type"] = type(backend).__name__
                stats["backends"].append(backend_stats)

                total_hits += backend_stats.get("hits", 0)
                total_misses += backend_stats.get("misses", 0)

            except Exception as e:
                logger.debug(f"Failed to get stats from {type(backend).__name__}: {e}")

        total_requests = total_hits + total_misses
        overall_hit_rate = (
            (total_hits / total_requests * 100) if total_requests > 0 else 0
        )

        stats["overall"] = {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "overall_hit_rate": round(overall_hit_rate, 2),
        }

        return stats

    def enable(self):
        """Enable caching."""
        self._enabled = True
        logger.info("Cache enabled")

    def disable(self):
        """Disable caching."""
        self._enabled = False
        logger.info("Cache disabled")

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache keys matching a pattern.

        Args:
            pattern: Pattern to match (supports * wildcards)

        Returns:
            Number of keys invalidated
        """
        # This is a simplified implementation
        # In production, you'd want more sophisticated pattern matching
        invalidated = 0

        for backend in self.backends:
            try:
                # For now, this is a placeholder
                # Real implementation would depend on backend capabilities
                if hasattr(backend, "delete_pattern"):
                    invalidated += backend.delete_pattern(pattern)
            except Exception as e:
                logger.debug(
                    f"Pattern invalidation failed for {type(backend).__name__}: {e}"
                )

        return invalidated


# Global cache instance
_default_cache: Optional[SmartCache] = None


def get_default_cache() -> SmartCache:
    """Get the default cache instance."""
    global _default_cache
    if _default_cache is None:
        _default_cache = SmartCache()
    return _default_cache


def cache_key_for_query(entity: str, filters: Optional[Dict] = None, **kwargs) -> str:
    """
    Generate cache key for API queries.

    Args:
        entity: Entity name
        filters: Query filters
        **kwargs: Additional query parameters

    Returns:
        Cache key string
    """
    key_parts = [f"query:{entity}"]

    if filters:
        # Sort filters for consistent keys
        filter_str = json.dumps(filters, sort_keys=True, separators=(",", ":"))
        key_parts.append(hashlib.md5(filter_str.encode()).hexdigest()[:8])

    if kwargs:
        kwargs_str = json.dumps(kwargs, sort_keys=True, separators=(",", ":"))
        key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest()[:8])

    return ":".join(key_parts)


def cache_key_for_entity(entity: str, entity_id: Union[int, str]) -> str:
    """
    Generate cache key for individual entities.

    Args:
        entity: Entity name
        entity_id: Entity ID

    Returns:
        Cache key string
    """
    return f"entity:{entity}:{entity_id}"
