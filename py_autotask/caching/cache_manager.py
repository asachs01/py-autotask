"""
Cache manager for coordinating caching operations across py-autotask.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from ..exceptions import AutotaskCacheError
from .backends import (
    CompositeCacheBackend,
    DiskCacheBackend,
    MemoryCacheBackend,
    RedisCacheBackend,
)
from .cache_config import CacheBackendType, CacheConfig
from .invalidation import CacheInvalidator

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Central cache manager that coordinates all caching operations.

    Provides a unified interface for caching across different backends
    with intelligent invalidation, compression, and performance monitoring.

    Example:
        cache_config = CacheConfig(
            backend="redis",
            redis_url="redis://localhost:6379",
            default_ttl=300
        )

        cache_manager = CacheManager(cache_config)
        await cache_manager.initialize()

        # Cache data
        await cache_manager.set("tickets:12345", ticket_data, ttl=60)

        # Retrieve data
        cached_ticket = await cache_manager.get("tickets:12345")

        # Invalidate related data
        await cache_manager.invalidate_pattern("tickets:*")
    """

    def __init__(self, config: CacheConfig):
        """
        Initialize cache manager with configuration.

        Args:
            config: Cache configuration
        """
        self.config = config
        self.backend = None
        self.invalidator = CacheInvalidator(self)

        # Statistics tracking
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "invalidations": 0,
            "errors": 0,
        }

        # Performance monitoring
        self._operation_times = []
        self._max_operation_history = 1000

        self.logger = logging.getLogger(f"{__name__}.CacheManager")

    async def initialize(self) -> None:
        """Initialize the cache backend."""
        try:
            if self.config.backend == CacheBackendType.MEMORY:
                self.backend = MemoryCacheBackend(self.config)

            elif self.config.backend == CacheBackendType.REDIS:
                self.backend = RedisCacheBackend(self.config)

            elif self.config.backend == CacheBackendType.DISK:
                self.backend = DiskCacheBackend(self.config)

            elif self.config.backend == CacheBackendType.COMPOSITE:
                # Multi-tier cache (Memory -> Redis -> Disk)
                memory_backend = MemoryCacheBackend(self.config)
                redis_backend = RedisCacheBackend(self.config)

                self.backend = CompositeCacheBackend([memory_backend, redis_backend])

            await self.backend.initialize()
            self.logger.info(
                f"Cache initialized with {self.config.backend.value} backend"
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize cache backend: {e}")
            raise AutotaskCacheError(f"Cache initialization failed: {e}")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get data from cache.

        Args:
            key: Cache key

        Returns:
            Cached data or None if not found
        """
        start_time = time.time()

        try:
            data = await self.backend.get(key)

            if data is not None:
                self.stats["hits"] += 1
                self.logger.debug(f"Cache hit for key: {key}")
            else:
                self.stats["misses"] += 1
                self.logger.debug(f"Cache miss for key: {key}")

            return data

        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Cache get error for key {key}: {e}")
            return None

        finally:
            self._record_operation_time("get", time.time() - start_time)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        entity_type: Optional[str] = None,
    ) -> bool:
        """
        Set data in cache.

        Args:
            key: Cache key
            value: Data to cache
            ttl: Time to live in seconds (uses default if not specified)
            entity_type: Entity type for intelligent TTL selection

        Returns:
            True if successfully cached
        """
        start_time = time.time()

        try:
            # Determine TTL
            if ttl is None:
                if entity_type:
                    ttl = self.config.get_ttl_for_entity(entity_type)
                else:
                    ttl = self.config.default_ttl

            success = await self.backend.set(key, value, ttl)

            if success:
                self.stats["sets"] += 1
                self.logger.debug(f"Cached data for key: {key} (TTL: {ttl}s)")
            else:
                self.stats["errors"] += 1
                self.logger.warning(f"Failed to cache data for key: {key}")

            return success

        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Cache set error for key {key}: {e}")
            return False

        finally:
            self._record_operation_time("set", time.time() - start_time)

    async def delete(self, key: str) -> bool:
        """
        Delete data from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if successfully deleted
        """
        start_time = time.time()

        try:
            success = await self.backend.delete(key)

            if success:
                self.stats["deletes"] += 1
                self.logger.debug(f"Deleted cache key: {key}")

            return success

        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Cache delete error for key {key}: {e}")
            return False

        finally:
            self._record_operation_time("delete", time.time() - start_time)

    async def exists(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists
        """
        try:
            return await self.backend.exists(key)
        except Exception as e:
            self.logger.error(f"Cache exists check error for key {key}: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.

        Args:
            pattern: Pattern to match (supports wildcards)

        Returns:
            Number of keys invalidated
        """
        start_time = time.time()

        try:
            count = await self.backend.delete_pattern(pattern)
            self.stats["invalidations"] += count

            self.logger.debug(f"Invalidated {count} keys matching pattern: {pattern}")
            return count

        except Exception as e:
            self.stats["errors"] += 1
            self.logger.error(f"Cache pattern invalidation error for {pattern}: {e}")
            return 0

        finally:
            self._record_operation_time("invalidate_pattern", time.time() - start_time)

    async def invalidate_entity(
        self, entity_type: str, entity_id: str, entity_data: Optional[Dict] = None
    ) -> None:
        """
        Invalidate cache entries related to an entity change.

        Args:
            entity_type: Type of entity that changed
            entity_id: ID of the entity
            entity_data: Entity data for relationship-based invalidation
        """
        await self.invalidator.invalidate_entity(entity_type, entity_id, entity_data)

    async def warm_cache(self, entities: List[str], background: bool = False) -> None:
        """
        Warm the cache by preloading common data.

        Args:
            entities: List of entity types to preload
            background: Whether to run warming in background
        """

        async def _warm_entities():
            for entity_type in entities:
                try:
                    # This would typically fetch popular data
                    # Implementation depends on having access to the client
                    self.logger.info(f"Warming cache for {entity_type}")
                    # TODO: Implement cache warming logic
                    await asyncio.sleep(0.1)  # Placeholder

                except Exception as e:
                    self.logger.error(f"Failed to warm cache for {entity_type}: {e}")

        if background:
            asyncio.create_task(_warm_entities())
        else:
            await _warm_entities()

    async def clear_all(self) -> bool:
        """
        Clear all cached data.

        Returns:
            True if successfully cleared
        """
        try:
            success = await self.backend.clear()
            if success:
                self.logger.info("Cache cleared successfully")
                # Reset stats
                for key in self.stats:
                    self.stats[key] = 0

            return success

        except Exception as e:
            self.logger.error(f"Failed to clear cache: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache performance statistics
        """
        total_operations = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total_operations if total_operations > 0 else 0

        avg_operation_time = (
            sum(self._operation_times) / len(self._operation_times)
            if self._operation_times
            else 0
        )

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "total_operations": total_operations,
            "avg_operation_time_ms": avg_operation_time * 1000,
            "backend_type": self.config.backend.value,
        }

    def _record_operation_time(self, operation: str, duration: float) -> None:
        """Record operation timing for performance monitoring."""
        self._operation_times.append(duration)

        # Keep only recent operations
        if len(self._operation_times) > self._max_operation_history:
            self._operation_times.pop(0)

    async def close(self) -> None:
        """Close cache connections and cleanup resources."""
        if self.backend:
            await self.backend.close()
            self.logger.info("Cache manager closed")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
