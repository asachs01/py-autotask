"""
ContractBlockHourFactors Entity for py-autotask

This module provides the ContractBlockHourFactorsEntity class for managing contract
block hour factors in Autotask. Block hour factors determine how time entries are
calculated against contract blocks based on various factors like time of day,
day of week, resource role, or other multipliers.
"""

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union

from .base import BaseEntity


class ContractBlockHourFactorsEntity(BaseEntity):
    """
    Manages Autotask ContractBlockHourFactors - multipliers for contract block hour consumption.

    Contract block hour factors define how time entries are multiplied when consumed
    against contract blocks. These factors can be based on various criteria such as
    time of day, day of week, resource roles, work types, or other business rules.

    Attributes:
        entity_name (str): The name of the entity in the Autotask API
    """

    entity_name = "ContractBlockHourFactors"

    # Core CRUD Operations

    def create_hour_factor(
        self,
        contract_block_id: int,
        factor_name: str,
        factor_value: Union[float, Decimal],
        factor_type: str,
        effective_date: Optional[date] = None,
        expiration_date: Optional[date] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new contract block hour factor.

        Args:
            contract_block_id: ID of the contract block
            factor_name: Name of the factor
            factor_value: The multiplier value (e.g., 1.5 for 50% premium)
            factor_type: Type of factor (TimeOfDay, DayOfWeek, ResourceRole, etc.)
            effective_date: When the factor becomes effective
            expiration_date: When the factor expires
            **kwargs: Additional fields for the hour factor

        Returns:
            Create response with new hour factor ID

        Example:
            factor = client.contract_block_hour_factors.create_hour_factor(
                contract_block_id=12345,
                factor_name="After Hours Premium",
                factor_value=1.5,
                factor_type="TimeOfDay"
            )
        """
        if effective_date is None:
            effective_date = date.today()

        factor_data = {
            "contractBlockID": contract_block_id,
            "factorName": factor_name,
            "factorValue": float(factor_value),
            "factorType": factor_type,
            "effectiveDate": effective_date.isoformat(),
            **kwargs,
        }

        if expiration_date:
            factor_data["expirationDate"] = expiration_date.isoformat()

        return self.create(factor_data)

    def get_factors_by_contract_block(
        self,
        contract_block_id: int,
        active_only: bool = True,
        factor_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get hour factors for a specific contract block.

        Args:
            contract_block_id: ID of the contract block
            active_only: Whether to return only active factors
            factor_type: Filter by factor type

        Returns:
            List of contract block hour factors
        """
        filters = [{"field": "contractBlockID", "op": "eq", "value": contract_block_id}]

        if active_only:
            today = date.today().isoformat()
            filters.extend(
                [
                    {"field": "isActive", "op": "eq", "value": True},
                    {"field": "effectiveDate", "op": "lte", "value": today},
                ]
            )

        if factor_type:
            filters.append({"field": "factorType", "op": "eq", "value": factor_type})

        return self.query(filters=filters).items

    def get_effective_factors(
        self,
        contract_block_id: int,
        evaluation_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all effective hour factors for a contract block on a specific date.

        Args:
            contract_block_id: ID of the contract block
            evaluation_date: Date to evaluate factors for (defaults to today)

        Returns:
            List of effective hour factors
        """
        if evaluation_date is None:
            evaluation_date = date.today()

        eval_date_str = evaluation_date.isoformat()

        filters = [
            {"field": "contractBlockID", "op": "eq", "value": contract_block_id},
            {"field": "isActive", "op": "eq", "value": True},
            {"field": "effectiveDate", "op": "lte", "value": eval_date_str},
        ]

        # Add expiration date filter (either null or greater than evaluation date)
        factors = self.query(filters=filters).items

        # Filter out expired factors
        effective_factors = []
        for factor in factors:
            expiration_date = factor.get("expirationDate")
            if not expiration_date or expiration_date >= eval_date_str:
                effective_factors.append(factor)

        return effective_factors

    # Business Logic Methods

    def calculate_consumed_hours(
        self,
        contract_block_id: int,
        actual_hours: Union[float, Decimal],
        evaluation_time: Optional[datetime] = None,
        resource_role_id: Optional[int] = None,
        work_type_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calculate consumed hours based on applicable factors.

        Args:
            contract_block_id: ID of the contract block
            actual_hours: Actual hours worked
            evaluation_time: When the work was performed
            resource_role_id: ID of the resource role
            work_type_id: ID of the work type

        Returns:
            Calculated consumed hours with factor breakdown
        """
        if evaluation_time is None:
            evaluation_time = datetime.now()

        actual_hours = Decimal(str(actual_hours))
        factors = self.get_effective_factors(contract_block_id, evaluation_time.date())

        applicable_factors = []
        total_multiplier = Decimal("1.0")

        # Determine which factors apply
        for factor in factors:
            factor_type = factor.get("factorType")
            factor_value = Decimal(str(factor.get("factorValue", 1.0)))
            applies = False

            if factor_type == "TimeOfDay":
                applies = self._check_time_of_day_factor(factor, evaluation_time.time())
            elif factor_type == "DayOfWeek":
                applies = self._check_day_of_week_factor(
                    factor, evaluation_time.weekday()
                )
            elif factor_type == "ResourceRole" and resource_role_id:
                applies = self._check_resource_role_factor(factor, resource_role_id)
            elif factor_type == "WorkType" and work_type_id:
                applies = self._check_work_type_factor(factor, work_type_id)
            elif factor_type == "General":
                applies = True

            if applies:
                applicable_factors.append(
                    {
                        "factor_id": factor.get("id"),
                        "factor_name": factor.get("factorName"),
                        "factor_type": factor_type,
                        "factor_value": factor_value,
                    }
                )
                total_multiplier *= factor_value

        consumed_hours = actual_hours * total_multiplier

        return {
            "contract_block_id": contract_block_id,
            "actual_hours": actual_hours,
            "consumed_hours": consumed_hours,
            "total_multiplier": total_multiplier,
            "evaluation_time": evaluation_time.isoformat(),
            "applicable_factors": applicable_factors,
        }

    def create_time_of_day_factor(
        self,
        contract_block_id: int,
        factor_name: str,
        factor_value: Union[float, Decimal],
        start_time: time,
        end_time: time,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Create a time-of-day based hour factor.

        Args:
            contract_block_id: ID of the contract block
            factor_name: Name of the factor
            factor_value: The multiplier value
            start_time: Start time for the factor
            end_time: End time for the factor
            effective_date: When the factor becomes effective

        Returns:
            Create response
        """
        return self.create_hour_factor(
            contract_block_id=contract_block_id,
            factor_name=factor_name,
            factor_value=factor_value,
            factor_type="TimeOfDay",
            effective_date=effective_date,
            startTime=start_time.strftime("%H:%M:%S"),
            endTime=end_time.strftime("%H:%M:%S"),
        )

    def create_day_of_week_factor(
        self,
        contract_block_id: int,
        factor_name: str,
        factor_value: Union[float, Decimal],
        days_of_week: List[int],  # 0=Monday, 6=Sunday
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Create a day-of-week based hour factor.

        Args:
            contract_block_id: ID of the contract block
            factor_name: Name of the factor
            factor_value: The multiplier value
            days_of_week: List of day numbers (0=Monday, 6=Sunday)
            effective_date: When the factor becomes effective

        Returns:
            Create response
        """
        return self.create_hour_factor(
            contract_block_id=contract_block_id,
            factor_name=factor_name,
            factor_value=factor_value,
            factor_type="DayOfWeek",
            effective_date=effective_date,
            daysOfWeek=",".join(map(str, days_of_week)),
        )

    def create_resource_role_factor(
        self,
        contract_block_id: int,
        factor_name: str,
        factor_value: Union[float, Decimal],
        resource_role_id: int,
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Create a resource role based hour factor.

        Args:
            contract_block_id: ID of the contract block
            factor_name: Name of the factor
            factor_value: The multiplier value
            resource_role_id: ID of the resource role
            effective_date: When the factor becomes effective

        Returns:
            Create response
        """
        return self.create_hour_factor(
            contract_block_id=contract_block_id,
            factor_name=factor_name,
            factor_value=factor_value,
            factor_type="ResourceRole",
            effective_date=effective_date,
            resourceRoleID=resource_role_id,
        )

    def update_factor_value(
        self,
        factor_id: int,
        new_value: Union[float, Decimal],
        effective_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Update the value of an hour factor.

        Args:
            factor_id: ID of the hour factor
            new_value: New multiplier value
            effective_date: When the new value becomes effective

        Returns:
            Update response
        """
        if effective_date is None:
            effective_date = date.today()

        update_data = {
            "factorValue": float(new_value),
            "effectiveDate": effective_date.isoformat(),
            "lastModifiedDate": datetime.now().isoformat(),
        }

        return self.update_by_id(factor_id, update_data)

    def get_factor_usage_report(
        self,
        contract_block_id: int,
        date_from: date,
        date_to: date,
    ) -> Dict[str, Any]:
        """
        Generate a report of hour factor usage for a contract block.

        Args:
            contract_block_id: ID of the contract block
            date_from: Start date for the report
            date_to: End date for the report

        Returns:
            Usage report with factor statistics
        """
        factors = self.get_factors_by_contract_block(
            contract_block_id, active_only=False
        )

        # This would typically integrate with time entries to show actual usage
        # For now, we'll return factor configuration information

        factor_summary = {}
        for factor in factors:
            factor_type = factor.get("factorType")
            if factor_type not in factor_summary:
                factor_summary[factor_type] = {
                    "count": 0,
                    "factors": [],
                    "avg_multiplier": Decimal("0"),
                    "min_multiplier": None,
                    "max_multiplier": None,
                }

            factor_value = Decimal(str(factor.get("factorValue", 1.0)))
            type_data = factor_summary[factor_type]
            type_data["count"] += 1
            type_data["factors"].append(
                {
                    "id": factor.get("id"),
                    "name": factor.get("factorName"),
                    "value": factor_value,
                    "effective_date": factor.get("effectiveDate"),
                    "expiration_date": factor.get("expirationDate"),
                }
            )

            if (
                type_data["min_multiplier"] is None
                or factor_value < type_data["min_multiplier"]
            ):
                type_data["min_multiplier"] = factor_value
            if (
                type_data["max_multiplier"] is None
                or factor_value > type_data["max_multiplier"]
            ):
                type_data["max_multiplier"] = factor_value

        # Calculate averages
        for type_data in factor_summary.values():
            if type_data["count"] > 0:
                total = sum(f["value"] for f in type_data["factors"])
                type_data["avg_multiplier"] = total / type_data["count"]

        return {
            "contract_block_id": contract_block_id,
            "report_period": {
                "from": date_from.isoformat(),
                "to": date_to.isoformat(),
            },
            "total_factors": len(factors),
            "by_type": factor_summary,
        }

    def bulk_update_factors(
        self,
        factor_updates: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Update multiple hour factors in batch.

        Args:
            factor_updates: List of factor updates, each containing factor_id and update data

        Returns:
            Summary of the bulk update operation
        """
        results = []

        for update in factor_updates:
            factor_id = update.get("factor_id")
            update_data = update.get("update_data", {})

            try:
                result = self.update_by_id(factor_id, update_data)
                results.append(
                    {
                        "factor_id": factor_id,
                        "success": True,
                        "result": result,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "factor_id": factor_id,
                        "success": False,
                        "error": str(e),
                    }
                )

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        return {
            "total_updates": len(factor_updates),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
        }

    # Helper methods for factor evaluation

    def _check_time_of_day_factor(
        self, factor: Dict[str, Any], check_time: time
    ) -> bool:
        """Check if a time-of-day factor applies."""
        start_time_str = factor.get("startTime")
        end_time_str = factor.get("endTime")

        if not start_time_str or not end_time_str:
            return False

        try:
            start_time = datetime.strptime(start_time_str, "%H:%M:%S").time()
            end_time = datetime.strptime(end_time_str, "%H:%M:%S").time()

            if start_time <= end_time:
                return start_time <= check_time <= end_time
            else:
                # Handle overnight periods
                return check_time >= start_time or check_time <= end_time
        except ValueError:
            return False

    def _check_day_of_week_factor(self, factor: Dict[str, Any], weekday: int) -> bool:
        """Check if a day-of-week factor applies."""
        days_str = factor.get("daysOfWeek")
        if not days_str:
            return False

        try:
            applicable_days = [int(d.strip()) for d in days_str.split(",")]
            return weekday in applicable_days
        except (ValueError, AttributeError):
            return False

    def _check_resource_role_factor(
        self, factor: Dict[str, Any], resource_role_id: int
    ) -> bool:
        """Check if a resource role factor applies."""
        factor_role_id = factor.get("resourceRoleID")
        return factor_role_id == resource_role_id

    def _check_work_type_factor(
        self, factor: Dict[str, Any], work_type_id: int
    ) -> bool:
        """Check if a work type factor applies."""
        factor_work_type_id = factor.get("workTypeID")
        return factor_work_type_id == work_type_id
