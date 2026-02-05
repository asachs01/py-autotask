"""
Configuration Item SSL Subject Alternative Name entity for Autotask API operations.
"""

import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class ConfigurationItemSslSubjectAlternativeNameEntity(BaseEntity):
    """
    Handles all Configuration Item SSL Subject Alternative Name-related operations for the Autotask API.

    Configuration Item SSL Subject Alternative Names represent SSL certificate SAN entries
    associated with configuration items, enabling SSL certificate management and monitoring.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_ssl_san(
        self,
        configuration_item_id: int,
        subject_alternative_name: str,
        certificate_serial_number: Optional[str] = None,
        issuer: Optional[str] = None,
        expiration_date: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new SSL Subject Alternative Name entry.

        Args:
            configuration_item_id: ID of the configuration item
            subject_alternative_name: The SAN value (domain name, IP, etc.)
            certificate_serial_number: Optional SSL certificate serial number
            issuer: Optional certificate issuer
            expiration_date: Optional certificate expiration date (ISO format)
            **kwargs: Additional SSL SAN fields

        Returns:
            Created SSL SAN data
        """
        san_data = {
            "ConfigurationItemID": configuration_item_id,
            "SubjectAlternativeName": subject_alternative_name.lower(),  # Normalize case
            **kwargs,
        }

        if certificate_serial_number:
            san_data["CertificateSerialNumber"] = certificate_serial_number

        if issuer:
            san_data["Issuer"] = issuer

        if expiration_date:
            san_data["ExpirationDate"] = expiration_date

        # Validate the SAN before creation
        validation_result = self.validate_ssl_san(san_data)
        if not validation_result["is_valid"]:
            raise ValueError(
                f"Invalid SSL SAN: {', '.join(validation_result['errors'])}"
            )

        return self.create(san_data)

    def get_ci_ssl_sans(
        self,
        configuration_item_id: int,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all SSL Subject Alternative Names for a specific configuration item.

        Args:
            configuration_item_id: ID of the configuration item
            active_only: Whether to return only non-expired certificates
            limit: Maximum number of SAN entries to return

        Returns:
            List of SSL SAN entries
        """
        filters = [
            QueryFilter(
                field="ConfigurationItemID", op="eq", value=configuration_item_id
            )
        ]

        if active_only:
            # Filter out expired certificates
            current_date = datetime.now().isoformat()
            filters.append(
                QueryFilter(field="ExpirationDate", op="gt", value=current_date)
            )

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_ssl_sans_by_domain(
        self,
        domain_pattern: str,
        active_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get SSL SANs by domain pattern.

        Args:
            domain_pattern: Domain pattern to search for (supports wildcards)
            active_only: Whether to return only non-expired certificates
            limit: Maximum number of SAN entries to return

        Returns:
            List of matching SSL SAN entries
        """
        filters = [
            QueryFilter(
                field="SubjectAlternativeName",
                op="contains",
                value=domain_pattern.lower(),
            )
        ]

        if active_only:
            current_date = datetime.now().isoformat()
            filters.append(
                QueryFilter(field="ExpirationDate", op="gt", value=current_date)
            )

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_expiring_certificates(
        self,
        days_ahead: int = 30,
        configuration_item_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get SSL certificates that are expiring within a specified timeframe.

        Args:
            days_ahead: Number of days ahead to check for expiration
            configuration_item_id: Optional filter by configuration item

        Returns:
            List of SSL SANs with expiring certificates
        """
        future_date = (datetime.now() + timedelta(days=days_ahead)).isoformat()
        current_date = datetime.now().isoformat()

        filters = [
            QueryFilter(field="ExpirationDate", op="lte", value=future_date),
            QueryFilter(field="ExpirationDate", op="gte", value=current_date),
        ]

        if configuration_item_id:
            filters.append(
                QueryFilter(
                    field="ConfigurationItemID", op="eq", value=configuration_item_id
                )
            )

        response = self.query(filters=filters)
        return response.items

    def get_expired_certificates(
        self,
        configuration_item_id: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get SSL certificates that have already expired.

        Args:
            configuration_item_id: Optional filter by configuration item
            limit: Maximum number of expired certificates to return

        Returns:
            List of SSL SANs with expired certificates
        """
        current_date = datetime.now().isoformat()

        filters = [QueryFilter(field="ExpirationDate", op="lt", value=current_date)]

        if configuration_item_id:
            filters.append(
                QueryFilter(
                    field="ConfigurationItemID", op="eq", value=configuration_item_id
                )
            )

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def update_certificate_info(
        self,
        san_id: int,
        certificate_serial_number: Optional[str] = None,
        issuer: Optional[str] = None,
        expiration_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update certificate information for an SSL SAN entry.

        Args:
            san_id: ID of SSL SAN entry to update
            certificate_serial_number: New certificate serial number
            issuer: New certificate issuer
            expiration_date: New expiration date

        Returns:
            Updated SSL SAN data
        """
        update_data = {}

        if certificate_serial_number is not None:
            update_data["CertificateSerialNumber"] = certificate_serial_number

        if issuer is not None:
            update_data["Issuer"] = issuer

        if expiration_date is not None:
            update_data["ExpirationDate"] = expiration_date

        if not update_data:
            raise ValueError("At least one field must be provided for update")

        return self.update_by_id(san_id, update_data)

    def get_ssl_certificate_summary(self, configuration_item_id: int) -> Dict[str, Any]:
        """
        Get an SSL certificate summary for a configuration item.

        Args:
            configuration_item_id: ID of the configuration item

        Returns:
            Dictionary with SSL certificate statistics
        """
        all_sans = self.get_ci_ssl_sans(configuration_item_id, active_only=False)

        summary = {
            "configuration_item_id": configuration_item_id,
            "total_san_entries": len(all_sans),
            "active_certificates": 0,
            "expired_certificates": 0,
            "expiring_soon": 0,  # Within 30 days
            "by_issuer": {},
            "unique_domains": set(),
            "wildcard_domains": 0,
            "ip_addresses": 0,
        }

        current_date = datetime.now()
        warning_date = current_date + timedelta(days=30)

        for san in all_sans:
            san_name = san.get("SubjectAlternativeName", "")
            expiration_str = san.get("ExpirationDate")
            issuer = san.get("Issuer", "Unknown")

            # Count by issuer
            summary["by_issuer"][issuer] = summary["by_issuer"].get(issuer, 0) + 1

            # Analyze domain types
            if san_name:
                summary["unique_domains"].add(san_name)

                if san_name.startswith("*."):
                    summary["wildcard_domains"] += 1
                elif self._is_ip_address(san_name):
                    summary["ip_addresses"] += 1

            # Analyze expiration status
            if expiration_str:
                try:
                    expiration_date = datetime.fromisoformat(
                        expiration_str.replace("Z", "+00:00")
                    )

                    if expiration_date < current_date:
                        summary["expired_certificates"] += 1
                    elif expiration_date <= warning_date:
                        summary["expiring_soon"] += 1
                    else:
                        summary["active_certificates"] += 1

                except ValueError:
                    pass
            else:
                summary["active_certificates"] += 1  # Assume active if no expiration

        # Convert set to count
        summary["unique_domains"] = len(summary["unique_domains"])

        return summary

    def validate_ssl_san(self, san_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate SSL Subject Alternative Name data.

        Args:
            san_data: SSL SAN data to validate

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        san_name = san_data.get("SubjectAlternativeName", "")
        expiration_date = san_data.get("ExpirationDate")
        serial_number = san_data.get("CertificateSerialNumber")

        # Validate SAN name
        if not san_name:
            errors.append("Subject Alternative Name is required")
        else:
            if not self._is_valid_san_name(san_name):
                errors.append("Invalid Subject Alternative Name format")

        # Validate expiration date
        if expiration_date:
            try:
                exp_date = datetime.fromisoformat(
                    expiration_date.replace("Z", "+00:00")
                )

                if exp_date < datetime.now():
                    warnings.append("Certificate has already expired")
                elif exp_date < datetime.now() + timedelta(days=30):
                    warnings.append("Certificate expires within 30 days")

            except ValueError:
                errors.append("Expiration date must be a valid ISO date")

        # Validate serial number format
        if serial_number:
            if not self._is_valid_serial_number(serial_number):
                warnings.append("Certificate serial number format may be invalid")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def get_certificate_renewal_report(self, days_ahead: int = 90) -> Dict[str, Any]:
        """
        Generate a certificate renewal report.

        Args:
            days_ahead: Number of days ahead to include in renewal planning

        Returns:
            Dictionary with renewal planning data
        """
        expiring_certs = self.get_expiring_certificates(days_ahead)
        expired_certs = self.get_expired_certificates()

        report = {
            "report_date": datetime.now().isoformat(),
            "planning_horizon_days": days_ahead,
            "immediate_action_required": len(expired_certs),
            "renewal_planning_required": len(expiring_certs),
            "by_urgency": {
                "expired": [],
                "expires_7_days": [],
                "expires_30_days": [],
                "expires_90_days": [],
            },
            "by_configuration_item": {},
        }

        current_date = datetime.now()

        # Categorize by urgency
        for cert in expired_certs:
            report["by_urgency"]["expired"].append(cert)

        for cert in expiring_certs:
            expiration_str = cert.get("ExpirationDate")
            if expiration_str:
                try:
                    exp_date = datetime.fromisoformat(
                        expiration_str.replace("Z", "+00:00")
                    )
                    days_until_expiry = (exp_date - current_date).days

                    if days_until_expiry <= 7:
                        report["by_urgency"]["expires_7_days"].append(cert)
                    elif days_until_expiry <= 30:
                        report["by_urgency"]["expires_30_days"].append(cert)
                    else:
                        report["by_urgency"]["expires_90_days"].append(cert)

                except ValueError:
                    pass

        # Group by configuration item
        all_certs = expired_certs + expiring_certs
        for cert in all_certs:
            ci_id = cert.get("ConfigurationItemID")
            if ci_id:
                if ci_id not in report["by_configuration_item"]:
                    report["by_configuration_item"][ci_id] = []
                report["by_configuration_item"][ci_id].append(cert)

        return report

    def _is_valid_san_name(self, san_name: str) -> bool:
        """
        Validate Subject Alternative Name format.

        Args:
            san_name: SAN name to validate

        Returns:
            True if valid SAN name format
        """
        if not san_name:
            return False

        # Check if it's an IP address
        if self._is_ip_address(san_name):
            return True

        # Check if it's a valid domain name (including wildcards)
        domain_pattern = re.compile(
            r"^(\*\.)?[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
        )
        return bool(domain_pattern.match(san_name))

    def _is_ip_address(self, value: str) -> bool:
        """
        Check if value is an IP address.

        Args:
            value: Value to check

        Returns:
            True if valid IP address
        """
        # Simple IPv4 check
        ipv4_pattern = re.compile(r"^(\d{1,3}\.){3}\d{1,3}$")
        if ipv4_pattern.match(value):
            try:
                parts = value.split(".")
                return all(0 <= int(part) <= 255 for part in parts)
            except ValueError:
                return False

        # Simple IPv6 check
        if ":" in value:
            try:
                import socket

                socket.inet_pton(socket.AF_INET6, value)
                return True
            except (socket.error, AttributeError):
                return False

        return False

    def _is_valid_serial_number(self, serial_number: str) -> bool:
        """
        Validate certificate serial number format.

        Args:
            serial_number: Serial number to validate

        Returns:
            True if valid format
        """
        if not serial_number:
            return False

        # Remove common separators
        clean_serial = serial_number.replace(":", "").replace("-", "").replace(" ", "")

        # Check if it's a valid hexadecimal string
        try:
            int(clean_serial, 16)
            return len(clean_serial) % 2 == 0 and len(clean_serial) >= 2
        except ValueError:
            return False

    def bulk_update_expiration_dates(
        self, san_updates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Update expiration dates for multiple SSL SAN entries in bulk.

        Args:
            san_updates: List of dicts with 'san_id' and 'expiration_date'

        Returns:
            List of updated SSL SAN data
        """
        update_data = [
            {"id": update["san_id"], "ExpirationDate": update["expiration_date"]}
            for update in san_updates
        ]
        return self.batch_update(update_data)

    def search_by_certificate_serial(
        self, serial_number: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search SSL SANs by certificate serial number.

        Args:
            serial_number: Certificate serial number to search for
            limit: Maximum number of results to return

        Returns:
            List of SSL SANs with matching serial number
        """
        filters = [
            QueryFilter(field="CertificateSerialNumber", op="eq", value=serial_number)
        ]

        response = self.query(filters=filters, max_records=limit)
        return response.items
