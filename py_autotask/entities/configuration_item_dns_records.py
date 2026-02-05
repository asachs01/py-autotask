"""
Configuration Item DNS Records entity for Autotask API operations.
"""

import re
from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class ConfigurationItemDnsRecordsEntity(BaseEntity):
    """
    Handles all Configuration Item DNS Record-related operations for the Autotask API.

    Configuration Item DNS Records represent DNS entries associated with configuration items,
    typically used for network devices, servers, and other networked assets.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_ci_dns_record(
        self,
        configuration_item_id: int,
        hostname: str,
        record_type: str,
        record_value: str,
        ttl: Optional[int] = None,
        priority: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new configuration item DNS record.

        Args:
            configuration_item_id: ID of the configuration item
            hostname: Hostname or domain name
            record_type: DNS record type (A, AAAA, CNAME, MX, TXT, etc.)
            record_value: Value of the DNS record
            ttl: Time to live in seconds
            priority: Priority for MX records
            **kwargs: Additional DNS record fields

        Returns:
            Created DNS record data
        """
        dns_record_data = {
            "ConfigurationItemID": configuration_item_id,
            "Hostname": hostname.lower(),  # DNS names are case insensitive
            "RecordType": record_type.upper(),
            "RecordValue": record_value,
            **kwargs,
        }

        if ttl is not None:
            dns_record_data["TTL"] = ttl

        if priority is not None and record_type.upper() == "MX":
            dns_record_data["Priority"] = priority

        # Validate the record before creation
        validation_result = self.validate_dns_record(dns_record_data)
        if not validation_result["is_valid"]:
            raise ValueError(
                f"Invalid DNS record: {', '.join(validation_result['errors'])}"
            )

        return self.create(dns_record_data)

    def get_ci_dns_records(
        self,
        configuration_item_id: int,
        record_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all DNS records for a specific configuration item.

        Args:
            configuration_item_id: ID of the configuration item
            record_type: Optional filter by DNS record type
            limit: Maximum number of records to return

        Returns:
            List of DNS records
        """
        filters = [
            QueryFilter(
                field="ConfigurationItemID", op="eq", value=configuration_item_id
            )
        ]

        if record_type:
            filters.append(
                QueryFilter(field="RecordType", op="eq", value=record_type.upper())
            )

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_dns_records_by_hostname(
        self,
        hostname: str,
        record_type: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get DNS records by hostname pattern.

        Args:
            hostname: Hostname to search for (supports wildcards)
            record_type: Optional filter by DNS record type
            limit: Maximum number of records to return

        Returns:
            List of matching DNS records
        """
        filters = [QueryFilter(field="Hostname", op="contains", value=hostname.lower())]

        if record_type:
            filters.append(
                QueryFilter(field="RecordType", op="eq", value=record_type.upper())
            )

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_dns_records_by_type(
        self,
        record_type: str,
        configuration_item_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get DNS records filtered by record type.

        Args:
            record_type: DNS record type to filter by
            configuration_item_id: Optional filter by configuration item
            limit: Maximum number of records to return

        Returns:
            List of DNS records of the specified type
        """
        filters = [QueryFilter(field="RecordType", op="eq", value=record_type.upper())]

        if configuration_item_id:
            filters.append(
                QueryFilter(
                    field="ConfigurationItemID", op="eq", value=configuration_item_id
                )
            )

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def update_dns_record_value(self, record_id: int, new_value: str) -> Dict[str, Any]:
        """
        Update the value of a DNS record.

        Args:
            record_id: ID of DNS record to update
            new_value: New record value

        Returns:
            Updated DNS record data
        """
        return self.update_by_id(record_id, {"RecordValue": new_value})

    def update_dns_record_ttl(self, record_id: int, new_ttl: int) -> Dict[str, Any]:
        """
        Update the TTL of a DNS record.

        Args:
            record_id: ID of DNS record to update
            new_ttl: New TTL value in seconds

        Returns:
            Updated DNS record data
        """
        return self.update_by_id(record_id, {"TTL": new_ttl})

    def get_expiring_dns_records(
        self,
        days_ahead: int = 30,
        configuration_item_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get DNS records that may need attention (based on TTL or other criteria).

        Args:
            days_ahead: Number of days ahead to check
            configuration_item_id: Optional filter by configuration item

        Returns:
            List of DNS records needing attention
        """
        # This is a simplified implementation - actual logic may vary
        # based on your specific requirements for "expiring" DNS records

        filters = []

        if configuration_item_id:
            filters.append(
                QueryFilter(
                    field="ConfigurationItemID", op="eq", value=configuration_item_id
                )
            )

        # Add filters for records with very low TTL (might indicate temporary records)
        filters.append(QueryFilter(field="TTL", op="lte", value=3600))  # 1 hour or less

        response = self.query(filters=filters)
        return response.items

    def get_ci_dns_summary(self, configuration_item_id: int) -> Dict[str, Any]:
        """
        Get a DNS summary for a configuration item.

        Args:
            configuration_item_id: ID of the configuration item

        Returns:
            Dictionary with DNS statistics
        """
        dns_records = self.get_ci_dns_records(configuration_item_id)

        summary = {
            "configuration_item_id": configuration_item_id,
            "total_records": len(dns_records),
            "by_type": {},
            "unique_hostnames": set(),
            "average_ttl": 0,
            "has_mx_records": False,
            "has_ipv6_records": False,
        }

        total_ttl = 0
        ttl_count = 0

        for record in dns_records:
            record_type = record.get("RecordType", "Unknown")
            hostname = record.get("Hostname", "")
            ttl = record.get("TTL")

            # Count by type
            summary["by_type"][record_type] = summary["by_type"].get(record_type, 0) + 1

            # Track unique hostnames
            if hostname:
                summary["unique_hostnames"].add(hostname)

            # Calculate average TTL
            if ttl:
                total_ttl += int(ttl)
                ttl_count += 1

            # Check for specific record types
            if record_type == "MX":
                summary["has_mx_records"] = True
            elif record_type == "AAAA":
                summary["has_ipv6_records"] = True

        # Convert set to count
        summary["unique_hostnames"] = len(summary["unique_hostnames"])

        # Calculate average TTL
        if ttl_count > 0:
            summary["average_ttl"] = total_ttl // ttl_count

        return summary

    def validate_dns_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate DNS record data.

        Args:
            record_data: DNS record data to validate

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        hostname = record_data.get("Hostname", "")
        record_type = record_data.get("RecordType", "").upper()
        record_value = record_data.get("RecordValue", "")
        ttl = record_data.get("TTL")
        priority = record_data.get("Priority")

        # Validate hostname
        if not hostname:
            errors.append("Hostname is required")
        elif not self._is_valid_hostname(hostname):
            errors.append("Invalid hostname format")

        # Validate record type
        valid_types = ["A", "AAAA", "CNAME", "MX", "TXT", "NS", "PTR", "SRV", "SOA"]
        if not record_type:
            errors.append("Record type is required")
        elif record_type not in valid_types:
            warnings.append(f"Record type '{record_type}' may not be standard")

        # Validate record value based on type
        if not record_value:
            errors.append("Record value is required")
        else:
            type_validation = self._validate_record_value_by_type(
                record_type, record_value
            )
            if not type_validation["is_valid"]:
                errors.extend(type_validation["errors"])

        # Validate TTL
        if ttl is not None:
            try:
                ttl_int = int(ttl)
                if ttl_int < 0:
                    errors.append("TTL cannot be negative")
                elif ttl_int < 300:
                    warnings.append("TTL less than 5 minutes may cause high DNS load")
            except (ValueError, TypeError):
                errors.append("TTL must be a valid number")

        # Validate priority for MX records
        if record_type == "MX":
            if priority is None:
                errors.append("Priority is required for MX records")
            else:
                try:
                    priority_int = int(priority)
                    if priority_int < 0:
                        errors.append("MX priority cannot be negative")
                except (ValueError, TypeError):
                    errors.append("MX priority must be a valid number")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def _is_valid_hostname(self, hostname: str) -> bool:
        """
        Validate hostname format.

        Args:
            hostname: Hostname to validate

        Returns:
            True if valid hostname format
        """
        if not hostname or len(hostname) > 253:
            return False

        # Basic regex for hostname validation
        hostname_pattern = re.compile(
            r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
        )
        return bool(hostname_pattern.match(hostname))

    def _validate_record_value_by_type(
        self, record_type: str, value: str
    ) -> Dict[str, Any]:
        """
        Validate record value based on DNS record type.

        Args:
            record_type: DNS record type
            value: Record value to validate

        Returns:
            Dictionary with validation results
        """
        errors = []

        if record_type == "A":
            # IPv4 address validation
            if not self._is_valid_ipv4(value):
                errors.append("Invalid IPv4 address format")
        elif record_type == "AAAA":
            # IPv6 address validation
            if not self._is_valid_ipv6(value):
                errors.append("Invalid IPv6 address format")
        elif record_type == "CNAME":
            # CNAME should be a valid hostname
            if not self._is_valid_hostname(value):
                errors.append("Invalid hostname format for CNAME record")
        elif record_type == "MX":
            # MX record should be a valid hostname
            if not self._is_valid_hostname(value):
                errors.append("Invalid hostname format for MX record")

        return {"is_valid": len(errors) == 0, "errors": errors}

    def _is_valid_ipv4(self, ip: str) -> bool:
        """Validate IPv4 address format."""
        try:
            parts = ip.split(".")
            if len(parts) != 4:
                return False
            for part in parts:
                if not (0 <= int(part) <= 255):
                    return False
            return True
        except (ValueError, AttributeError):
            return False

    def _is_valid_ipv6(self, ip: str) -> bool:
        """Validate IPv6 address format (simplified)."""
        try:
            # Very basic IPv6 validation
            import socket

            socket.inet_pton(socket.AF_INET6, ip)
            return True
        except (socket.error, AttributeError):
            return False

    def bulk_update_ttl(
        self, record_ids: List[int], new_ttl: int
    ) -> List[Dict[str, Any]]:
        """
        Update TTL for multiple DNS records in bulk.

        Args:
            record_ids: List of DNS record IDs to update
            new_ttl: New TTL value

        Returns:
            List of updated DNS record data
        """
        update_data = [{"id": record_id, "TTL": new_ttl} for record_id in record_ids]
        return self.batch_update(update_data)
