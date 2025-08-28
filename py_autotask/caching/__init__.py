"""
Intelligent caching system for py-autotask.

This module provides a comprehensive caching framework with multiple backends,
smart invalidation, and performance optimization for Autotask API operations.
"""

from .backends import (
    CompositeCacheBackend,
    DiskCacheBackend,
    MemoryCacheBackend,
    RedisCacheBackend,
)
from .cache_config import CacheConfig
from .cache_manager import CacheManager
from .decorators import cache_invalidate, cached
from .invalidation import CacheInvalidator
from .patterns import CachePatterns

__all__ = [
    "CacheConfig",
    "CacheManager",
    "MemoryCacheBackend",
    "RedisCacheBackend",
    "DiskCacheBackend",
    "CompositeCacheBackend",
    "CacheInvalidator",
    "CachePatterns",
    "cached",
    "cache_invalidate",
]
