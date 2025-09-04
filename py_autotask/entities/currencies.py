"""
Currencies entity for Autotask API operations.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..types import EntityDict, EntityList
from .base import BaseEntity


class CurrenciesEntity(BaseEntity):
    """
    Handles Currency reference data operations for the Autotask API.

    Manages currency codes, exchange rates, and formatting information
    used throughout the Autotask system for international operations.
    """

    def __init__(self, client, entity_name: str = "Currencies"):
        super().__init__(client, entity_name)

    def get_all_currencies(self, active_only: bool = True) -> EntityList:
        """
        Get all currencies in the system.

        Args:
            active_only: Whether to include only active currencies

        Returns:
            List of currencies
        """
        filters = []
        if active_only:
            filters = [{"field": "IsActive", "op": "eq", "value": "true"}]

        return self.query_all(filters=filters)

    def get_currency_by_code(self, currency_code: str) -> Optional[EntityDict]:
        """
        Get a currency by its ISO currency code.

        Args:
            currency_code: ISO currency code (e.g., 'USD', 'EUR', 'GBP')

        Returns:
            Currency data or None if not found
        """
        filters = [
            {"field": "CurrencyCode", "op": "eq", "value": currency_code.upper()}
        ]
        result = self.query(filters=filters)
        return result.items[0] if result.items else None

    def get_currency_by_name(self, currency_name: str) -> Optional[EntityDict]:
        """
        Get a currency by its name.

        Args:
            currency_name: Currency name (e.g., 'US Dollar', 'Euro')

        Returns:
            Currency data or None if not found
        """
        filters = [{"field": "Name", "op": "eq", "value": currency_name}]
        result = self.query(filters=filters)
        return result.items[0] if result.items else None

    def search_currencies_by_name(self, name_pattern: str) -> EntityList:
        """
        Search currencies by name pattern.

        Args:
            name_pattern: Name pattern to search for

        Returns:
            List of matching currencies
        """
        filters = [{"field": "Name", "op": "contains", "value": name_pattern}]
        return self.query_all(filters=filters)

    def get_base_currency(self) -> Optional[EntityDict]:
        """
        Get the system's base currency.

        Returns:
            Base currency data or None if not found
        """
        filters = [{"field": "IsBaseCurrency", "op": "eq", "value": "true"}]
        result = self.query(filters=filters)
        return result.items[0] if result.items else None

    def get_currencies_with_recent_rates(self, days: int = 7) -> EntityList:
        """
        Get currencies that have recent exchange rate updates.

        Args:
            days: Number of days to consider "recent"

        Returns:
            List of currencies with recent rate updates
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        filters = [
            {"field": "LastRateUpdate", "op": "gte", "value": cutoff_date},
            {"field": "IsActive", "op": "eq", "value": "true"},
        ]
        return self.query_all(filters=filters)

    def get_currencies_needing_rate_updates(self, days: int = 30) -> EntityList:
        """
        Get currencies that haven't had rate updates recently.

        Args:
            days: Number of days to consider "stale"

        Returns:
            List of currencies needing rate updates
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        filters = [
            {"field": "LastRateUpdate", "op": "lt", "value": cutoff_date},
            {"field": "IsActive", "op": "eq", "value": "true"},
            {
                "field": "IsBaseCurrency",
                "op": "ne",
                "value": "true",
            },  # Base currency doesn't need updates
        ]
        return self.query_all(filters=filters)

    def convert_amount(
        self,
        amount: float,
        from_currency_code: str,
        to_currency_code: str,
        rate_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Convert an amount from one currency to another.

        Args:
            amount: Amount to convert
            from_currency_code: Source currency code
            to_currency_code: Target currency code
            rate_date: Optional specific date for rates (defaults to latest)

        Returns:
            Dictionary with conversion results
        """
        result = {
            "original_amount": amount,
            "from_currency": from_currency_code.upper(),
            "to_currency": to_currency_code.upper(),
            "converted_amount": None,
            "exchange_rate": None,
            "rate_date": None,
            "base_currency": None,
            "error": None,
        }

        try:
            # Get currency information
            from_currency = self.get_currency_by_code(from_currency_code)
            to_currency = self.get_currency_by_code(to_currency_code)
            base_currency = self.get_base_currency()

            if not from_currency:
                result["error"] = f"Source currency {from_currency_code} not found"
                return result

            if not to_currency:
                result["error"] = f"Target currency {to_currency_code} not found"
                return result

            if not base_currency:
                result["error"] = "Base currency not configured"
                return result

            result["base_currency"] = base_currency.get("CurrencyCode")

            # If same currency, no conversion needed
            if from_currency_code.upper() == to_currency_code.upper():
                result["converted_amount"] = amount
                result["exchange_rate"] = 1.0
                result["rate_date"] = datetime.now().date().isoformat()
                return result

            # Get exchange rates (relative to base currency)
            from_rate = float(from_currency.get("ExchangeRate", 1.0))
            to_rate = float(to_currency.get("ExchangeRate", 1.0))

            # Convert: amount -> base currency -> target currency
            if from_currency.get("IsBaseCurrency", False):
                # From base currency to target
                conversion_rate = 1.0 / to_rate
            elif to_currency.get("IsBaseCurrency", False):
                # From source to base currency
                conversion_rate = from_rate
            else:
                # From source -> base -> target
                conversion_rate = from_rate / to_rate

            result["converted_amount"] = round(amount * conversion_rate, 4)
            result["exchange_rate"] = conversion_rate
            result["rate_date"] = (
                from_currency.get("LastRateUpdate") or datetime.now().date().isoformat()
            )

        except Exception as e:
            result["error"] = f"Conversion error: {str(e)}"

        return result

    def format_currency_amount(
        self,
        amount: float,
        currency_code: str,
        include_symbol: bool = True,
        include_code: bool = False,
    ) -> str:
        """
        Format an amount according to currency conventions.

        Args:
            amount: Amount to format
            currency_code: Currency code
            include_symbol: Whether to include currency symbol
            include_code: Whether to include currency code

        Returns:
            Formatted currency string
        """
        currency = self.get_currency_by_code(currency_code)
        if not currency:
            return f"{amount:.2f} {currency_code}"

        # Get formatting properties
        symbol = currency.get("Symbol", currency_code)
        decimal_places = int(currency.get("DecimalPlaces", 2))
        thousands_separator = currency.get("ThousandsSeparator", ",")
        decimal_separator = currency.get("DecimalSeparator", ".")
        symbol_position = currency.get("SymbolPosition", "before")  # before/after

        # Format the number
        formatted_amount = f"{amount:,.{decimal_places}f}"

        # Replace default separators with currency-specific ones
        if thousands_separator != ",":
            formatted_amount = formatted_amount.replace(",", "~TEMP~")
            formatted_amount = formatted_amount.replace(".", decimal_separator)
            formatted_amount = formatted_amount.replace("~TEMP~", thousands_separator)
        elif decimal_separator != ".":
            formatted_amount = formatted_amount.replace(".", decimal_separator)

        # Add symbol and/or code
        result = formatted_amount

        if include_symbol:
            if symbol_position == "after":
                result = f"{result} {symbol}"
            else:
                result = f"{symbol}{result}"

        if include_code:
            result = f"{result} {currency_code.upper()}"

        return result

    def update_exchange_rate(
        self,
        currency_code: str,
        new_rate: float,
        rate_source: Optional[str] = None,
    ) -> Optional[EntityDict]:
        """
        Update the exchange rate for a currency.

        Args:
            currency_code: Currency code to update
            new_rate: New exchange rate (relative to base currency)
            rate_source: Optional source of the rate

        Returns:
            Updated currency data
        """
        currency = self.get_currency_by_code(currency_code)
        if not currency:
            return None

        update_data = {
            "ExchangeRate": new_rate,
            "LastRateUpdate": datetime.now().isoformat(),
        }

        if rate_source:
            update_data["RateSource"] = rate_source

        return self.update_by_id(int(currency["id"]), update_data)

    def get_currency_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about currencies in the system.

        Returns:
            Dictionary with currency statistics
        """
        all_currencies = self.query_all()
        active_currencies = self.get_all_currencies(active_only=True)

        stats = {
            "total_currencies": len(all_currencies),
            "active_currencies": len(active_currencies),
            "inactive_currencies": len(all_currencies) - len(active_currencies),
            "base_currency": None,
            "currencies_with_rates": 0,
            "currencies_without_rates": 0,
            "stale_rates_count": 0,  # Older than 7 days
            "major_currencies": 0,
            "minor_currencies": 0,
            "average_exchange_rate": 0.0,
        }

        base_currency = self.get_base_currency()
        if base_currency:
            stats["base_currency"] = base_currency.get("CurrencyCode")

        # Major currency codes (most traded)
        major_currency_codes = {"USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY"}

        total_rates = 0
        rate_count = 0
        seven_days_ago = datetime.now() - timedelta(days=7)

        for currency in all_currencies:
            # Check if currency has exchange rate
            exchange_rate = currency.get("ExchangeRate")
            if exchange_rate and exchange_rate != 0:
                stats["currencies_with_rates"] += 1
                total_rates += float(exchange_rate)
                rate_count += 1

                # Check if rate is stale
                last_update_str = currency.get("LastRateUpdate")
                if last_update_str:
                    try:
                        last_update = datetime.fromisoformat(
                            last_update_str.replace("Z", "+00:00")
                        )
                        if last_update < seven_days_ago:
                            stats["stale_rates_count"] += 1
                    except (ValueError, TypeError):
                        stats["stale_rates_count"] += 1
            else:
                stats["currencies_without_rates"] += 1

            # Count major vs minor currencies
            currency_code = currency.get("CurrencyCode", "")
            if currency_code in major_currency_codes:
                stats["major_currencies"] += 1
            else:
                stats["minor_currencies"] += 1

        # Calculate average exchange rate
        if rate_count > 0:
            stats["average_exchange_rate"] = round(total_rates / rate_count, 4)

        return stats

    def get_popular_currencies(self, limit: int = 20) -> EntityList:
        """
        Get commonly used currencies.

        Args:
            limit: Maximum number of currencies to return

        Returns:
            List of popular currencies
        """
        # Popular currencies based on global trade volume
        popular_codes = [
            "USD",
            "EUR",
            "GBP",
            "JPY",
            "AUD",
            "CAD",
            "CHF",
            "CNY",
            "SEK",
            "NZD",
            "MXN",
            "SGD",
            "HKD",
            "NOK",
            "KRW",
            "TRY",
            "RUB",
            "INR",
            "BRL",
            "ZAR",
        ]

        popular_currencies = []
        for code in popular_codes[:limit]:
            currency = self.get_currency_by_code(code)
            if currency:
                popular_currencies.append(currency)

        return popular_currencies

    def validate_currency_code(self, currency_code: str) -> Dict[str, Any]:
        """
        Validate if a currency code is valid and active.

        Args:
            currency_code: Currency code to validate

        Returns:
            Validation result dictionary
        """
        result = {
            "valid": False,
            "currency_code": currency_code.upper(),
            "currency_data": None,
            "is_active": False,
            "has_current_rate": False,
            "warnings": [],
        }

        currency = self.get_currency_by_code(currency_code)
        if currency:
            result["valid"] = True
            result["currency_data"] = currency
            result["is_active"] = currency.get("IsActive", True)

            # Check if exchange rate is current
            exchange_rate = currency.get("ExchangeRate")
            last_update_str = currency.get("LastRateUpdate")

            if exchange_rate and exchange_rate != 0:
                result["has_current_rate"] = True

                if last_update_str:
                    try:
                        last_update = datetime.fromisoformat(
                            last_update_str.replace("Z", "+00:00")
                        )
                        days_old = (datetime.now() - last_update).days

                        if days_old > 7:
                            result["warnings"].append(
                                f"Exchange rate is {days_old} days old"
                            )
                    except (ValueError, TypeError):
                        result["warnings"].append("Exchange rate date is invalid")
            else:
                result["warnings"].append("No current exchange rate available")

            if not result["is_active"]:
                result["warnings"].append("Currency is not currently active")
        else:
            result["warnings"].append("Currency code not found in system")

        return result

    def bulk_update_exchange_rates(
        self,
        rate_updates: List[Dict[str, Any]],
        rate_source: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update exchange rates for multiple currencies.

        Args:
            rate_updates: List of dictionaries with currency_code and rate
            rate_source: Optional source of the rates

        Returns:
            Dictionary with update results
        """
        results = {
            "total_requested": len(rate_updates),
            "successful_updates": [],
            "failed_updates": [],
            "update_timestamp": datetime.now().isoformat(),
            "rate_source": rate_source,
        }

        for update in rate_updates:
            currency_code = update.get("currency_code", "").upper()
            new_rate = update.get("rate")

            try:
                if not currency_code or new_rate is None:
                    results["failed_updates"].append(
                        {
                            "currency_code": currency_code,
                            "error": "Missing currency code or rate",
                        }
                    )
                    continue

                updated_currency = self.update_exchange_rate(
                    currency_code, float(new_rate), rate_source
                )

                if updated_currency:
                    results["successful_updates"].append(
                        {
                            "currency_code": currency_code,
                            "old_rate": update.get("old_rate"),
                            "new_rate": new_rate,
                        }
                    )
                else:
                    results["failed_updates"].append(
                        {
                            "currency_code": currency_code,
                            "error": "Currency not found or update failed",
                        }
                    )

            except Exception as e:
                results["failed_updates"].append(
                    {"currency_code": currency_code, "error": str(e)}
                )

        return results

    def get_exchange_rate_history(
        self, currency_code: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get exchange rate history for a currency.

        Note: This assumes historical data is stored separately.

        Args:
            currency_code: Currency code
            days: Number of days of history to retrieve

        Returns:
            List of historical rate data
        """
        # This would typically query a separate exchange rate history table
        # For now, return current rate as placeholder
        current_currency = self.get_currency_by_code(currency_code)

        if not current_currency:
            return []

        # Placeholder implementation
        return [
            {
                "date": datetime.now().date().isoformat(),
                "rate": current_currency.get("ExchangeRate", 1.0),
                "source": current_currency.get("RateSource", "system"),
            }
        ]
