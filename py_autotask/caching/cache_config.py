"""
Cache configuration for py-autotask caching system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Union


class CacheBackendType(Enum):
    """Supported cache backend types."""

    MEMORY = "memory"
    REDIS = "redis"
    DISK = "disk"
    COMPOSITE = "composite"


@dataclass
class CacheConfig:
    """
    Configuration for the caching system.

    Example:
        config = CacheConfig(
            backend="redis",
            redis_url="redis://localhost:6379",
            default_ttl=300,
            cache_patterns={
                "companies": 1800,    # 30 minutes
                "tickets": 60,        # 1 minute
                "time_entries": 3600  # 1 hour
            }
        )
    """

    # Backend configuration
    backend: Union[str, CacheBackendType] = CacheBackendType.MEMORY
    redis_url: Optional[str] = None
    redis_password: Optional[str] = None
    redis_db: int = 0
    redis_pool_size: int = 10

    # Disk cache configuration
    disk_cache_dir: Optional[str] = None
    disk_cache_size_limit: int = 1024 * 1024 * 1024  # 1GB

    # Memory cache configuration
    memory_max_entries: int = 10000
    memory_size_limit: int = 100 * 1024 * 1024  # 100MB

    # TTL configuration
    default_ttl: int = 300  # 5 minutes
    cache_patterns: Optional[Dict[str, int]] = None

    # Performance settings
    compression_enabled: bool = True
    compression_threshold: int = 1024  # Compress items larger than 1KB

    # Invalidation settings
    auto_invalidate: bool = True
    invalidation_patterns: Optional[Dict[str, list]] = None

    # Monitoring
    enable_stats: bool = True
    stats_ttl: int = 3600  # 1 hour

    def __post_init__(self):
        """Initialize default values and validate configuration."""
        if isinstance(self.backend, str):
            self.backend = CacheBackendType(self.backend.lower())

        if self.cache_patterns is None:
            self.cache_patterns = self._default_cache_patterns()

        if self.invalidation_patterns is None:
            self.invalidation_patterns = self._default_invalidation_patterns()

    def _default_cache_patterns(self) -> Dict[str, int]:
        """Default TTL patterns for common Autotask entities."""
        return {
            # Long-term stable data
            "companies": 1800,  # 30 minutes
            "contacts": 1200,  # 20 minutes
            "resources": 1800,  # 30 minutes
            "products": 3600,  # 1 hour
            "services": 3600,  # 1 hour
            # Medium-term data
            "contracts": 900,  # 15 minutes
            "projects": 600,  # 10 minutes
            "opportunities": 300,  # 5 minutes
            # Short-term volatile data
            "tickets": 60,  # 1 minute
            "time_entries": 120,  # 2 minutes
            "expenses": 180,  # 3 minutes
            # Very short-term data
            "ticket_notes": 30,  # 30 seconds
            "notifications": 15,  # 15 seconds
            # System/config data (longer TTL)
            "picklist_values": 7200,  # 2 hours
            "user_defined_fields": 3600,  # 1 hour
            "system_configuration": 1800,  # 30 minutes
        }

    def _default_invalidation_patterns(self) -> Dict[str, list]:
        """Default cache invalidation patterns based on entity relationships."""
        return {
            # When tickets change, invalidate related data
            "tickets": [
                "tickets:*",
                "companies:{accountID}:tickets",
                "resources:{assignedResourceID}:tickets",
                "projects:{projectID}:tickets",
            ],
            # When companies change, invalidate related data
            "companies": [
                "companies:*",
                "companies:{id}:*",
                "contacts:company:{id}",
                "tickets:company:{id}",
                "contracts:company:{id}",
            ],
            # When contacts change
            "contacts": ["contacts:*", "companies:{companyID}:contacts"],
            # When time entries change
            "time_entries": [
                "time_entries:*",
                "tickets:{ticketID}:time_entries",
                "resources:{resourceID}:time_entries",
                "projects:{projectID}:time_entries",
            ],
            # When projects change
            "projects": [
                "projects:*",
                "companies:{accountID}:projects",
                "tickets:project:{id}",
                "time_entries:project:{id}",
            ],
        }

    def get_ttl_for_entity(self, entity_name: str) -> int:
        """
        Get TTL for a specific entity type.

        Args:
            entity_name: Name of the entity

        Returns:
            TTL in seconds
        """
        return self.cache_patterns.get(entity_name.lower(), self.default_ttl)

    def should_compress(self, data_size: int) -> bool:
        """
        Determine if data should be compressed based on size.

        Args:
            data_size: Size of data in bytes

        Returns:
            True if data should be compressed
        """
        return self.compression_enabled and data_size >= self.compression_threshold
