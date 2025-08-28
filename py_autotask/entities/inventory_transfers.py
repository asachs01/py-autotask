"""
InventoryTransfers entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class InventoryTransfersEntity(BaseEntity):
    """
    Handles all Inventory Transfer-related operations for the Autotask API.

    Inventory Transfers represent movements of inventory items between locations.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_inventory_transfer(
        self,
        product_id: int,
        from_location_id: int,
        to_location_id: int,
        quantity: int,
        transfer_date: str,
        reason: Optional[str] = None,
        notes: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new inventory transfer record.

        Args:
            product_id: ID of the product being transferred
            from_location_id: ID of the source location
            to_location_id: ID of the destination location
            quantity: Quantity to transfer
            transfer_date: Date of the transfer
            reason: Reason for the transfer
            notes: Additional notes about the transfer
            **kwargs: Additional transfer fields

        Returns:
            Created inventory transfer data
        """
        transfer_data = {
            "ProductID": product_id,
            "FromLocationID": from_location_id,
            "ToLocationID": to_location_id,
            "Quantity": quantity,
            "TransferDate": transfer_date,
            **kwargs,
        }

        if reason:
            transfer_data["Reason"] = reason
        if notes:
            transfer_data["Notes"] = notes

        return self.create(transfer_data)

    def get_transfers_by_product(
        self, product_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all transfers for a specific product.

        Args:
            product_id: ID of the product
            limit: Maximum number of records to return

        Returns:
            List of transfers for the product
        """
        filters = [QueryFilter(field="ProductID", op="eq", value=product_id)]

        return self.query(filters=filters, max_records=limit)

    def get_transfers_from_location(
        self, location_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all transfers from a specific location.

        Args:
            location_id: ID of the source location
            limit: Maximum number of records to return

        Returns:
            List of transfers from the location
        """
        filters = [QueryFilter(field="FromLocationID", op="eq", value=location_id)]

        return self.query(filters=filters, max_records=limit)

    def get_transfers_to_location(
        self, location_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all transfers to a specific location.

        Args:
            location_id: ID of the destination location
            limit: Maximum number of records to return

        Returns:
            List of transfers to the location
        """
        filters = [QueryFilter(field="ToLocationID", op="eq", value=location_id)]

        return self.query(filters=filters, max_records=limit)

    def get_transfers_by_date_range(
        self, start_date: str, end_date: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get transfers within a specific date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            limit: Maximum number of records to return

        Returns:
            List of transfers within the date range
        """
        filters = [
            QueryFilter(field="TransferDate", op="ge", value=start_date),
            QueryFilter(field="TransferDate", op="le", value=end_date),
        ]

        return self.query(filters=filters, max_records=limit)

    def get_recent_transfers(
        self, days: int = 30, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get recent inventory transfers.

        Args:
            days: Number of days back to look for transfers
            limit: Maximum number of records to return

        Returns:
            List of recent transfers
        """
        from datetime import date, timedelta

        start_date = (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")
        filters = [QueryFilter(field="TransferDate", op="ge", value=start_date)]

        return self.query(filters=filters, max_records=limit)

    def get_large_quantity_transfers(
        self, minimum_quantity: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get transfers with quantities above a threshold.

        Args:
            minimum_quantity: Minimum quantity to filter by
            limit: Maximum number of records to return

        Returns:
            List of large quantity transfers
        """
        filters = [QueryFilter(field="Quantity", op="ge", value=minimum_quantity)]

        return self.query(filters=filters, max_records=limit)

    def update_transfer_notes(self, transfer_id: int, notes: str) -> EntityDict:
        """
        Update the notes for a transfer.

        Args:
            transfer_id: ID of the transfer
            notes: New notes content

        Returns:
            Updated transfer data
        """
        return self.update_by_id(transfer_id, {"Notes": notes})

    def get_transfer_statistics(
        self, location_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get statistics about inventory transfers.

        Args:
            location_id: Optional location ID to filter statistics

        Returns:
            Dictionary containing transfer statistics
        """
        if location_id:
            # Get transfers either from or to the specified location
            from_transfers = self.get_transfers_from_location(location_id)
            to_transfers = self.get_transfers_to_location(location_id)
            all_transfers = from_transfers + to_transfers
        else:
            all_transfers = self.query()

        total_quantity_transferred = sum(
            transfer.get("Quantity", 0) for transfer in all_transfers
        )

        stats = {
            "total_transfers": len(all_transfers),
            "total_quantity_transferred": total_quantity_transferred,
            "transfers_with_notes": len(
                [transfer for transfer in all_transfers if transfer.get("Notes")]
            ),
        }

        if location_id:
            stats["transfers_from_location"] = len(from_transfers)
            stats["transfers_to_location"] = len(to_transfers)

        return stats

    def get_product_transfer_history(
        self, product_id: int, limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive transfer history for a product.

        Args:
            product_id: ID of the product
            limit: Maximum number of transfers to analyze

        Returns:
            Dictionary with transfer history summary
        """
        transfers = self.get_transfers_by_product(product_id, limit=limit)

        # Sort transfers by date
        sorted_transfers = sorted(
            transfers, key=lambda x: x.get("TransferDate", ""), reverse=True
        )

        total_moved = sum(transfer.get("Quantity", 0) for transfer in transfers)

        # Get unique locations involved
        locations_from = set(transfer.get("FromLocationID") for transfer in transfers)
        locations_to = set(transfer.get("ToLocationID") for transfer in transfers)
        all_locations = locations_from.union(locations_to)

        history = {
            "product_id": product_id,
            "total_transfers": len(transfers),
            "total_quantity_moved": total_moved,
            "locations_involved": len(all_locations),
            "recent_transfers": sorted_transfers[:10],  # Last 10 transfers
            "transfer_frequency": {
                "last_30_days": len(
                    [
                        t
                        for t in transfers
                        if self._is_recent_date(t.get("TransferDate"), 30)
                    ]
                ),
                "last_90_days": len(
                    [
                        t
                        for t in transfers
                        if self._is_recent_date(t.get("TransferDate"), 90)
                    ]
                ),
            },
        }

        return history

    def _is_recent_date(self, date_str: Optional[str], days: int) -> bool:
        """
        Helper method to check if a date is within the last N days.

        Args:
            date_str: Date string to check
            days: Number of days to check against

        Returns:
            True if the date is within the last N days
        """
        if not date_str:
            return False

        try:
            from datetime import date, datetime, timedelta

            transfer_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            cutoff_date = date.today() - timedelta(days=days)
            return transfer_date >= cutoff_date
        except (ValueError, TypeError):
            return False
