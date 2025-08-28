"""
Intelligent caching system for py-autotask.

This module provides a comprehensive caching framework with multiple backends,
smart invalidation, and performance optimization for Autotask API operations.
"""

from .cache_config import CacheConfig
from .cache_manager import CacheManager
from .backends import (
    MemoryCacheBackend,
    RedisCacheBackend,
    DiskCacheBackend,
    CompositeCacheBackend,
)
from .invalidation import CacheInvalidator
from .patterns import CachePatterns
from .decorators import cached, cache_invalidate

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
