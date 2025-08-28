"""
CompanyCategories entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import QueryFilter
from .base import BaseEntity


class CompanyCategoriesEntity(BaseEntity):
    """
    Handles all Company Category-related operations for the Autotask API.

    Company Categories in Autotask represent classification systems for
    organizing and categorizing companies based on business requirements.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_company_category(
        self,
        category_name: str,
        description: Optional[str] = None,
        is_active: bool = True,
        color_code: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Create a new company category.

        Args:
            category_name: Name of the category
            description: Optional description of the category
            is_active: Whether the category is active
            color_code: Optional color code for visual identification
            **kwargs: Additional category fields

        Returns:
            Created company category data
        """
        category_data = {
            "Name": category_name,
            "IsActive": is_active,
            **kwargs,
        }

        if description:
            category_data["Description"] = description
        if color_code:
            category_data["ColorCode"] = color_code

        return self.create(category_data)

    def get_all_categories(
        self, active_only: bool = True, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all company categories.

        Args:
            active_only: Whether to return only active categories
            limit: Maximum number of categories to return

        Returns:
            List of company categories
        """
        filters = []
        if active_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        response = self.query(filters=filters if filters else None, max_records=limit)
        return response.items

    def search_categories_by_name(
        self,
        name: str,
        exact_match: bool = False,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for categories by name.

        Args:
            name: Category name to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of categories to return

        Returns:
            List of matching categories
        """
        if exact_match:
            filters = [QueryFilter(field="Name", op="eq", value=name)]
        else:
            filters = [QueryFilter(field="Name", op="contains", value=name)]

        response = self.query(filters=filters, max_records=limit)
        return response.items

    def get_companies_by_category(
        self,
        category_id: int,
        active_companies_only: bool = True,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get all companies assigned to a specific category.

        Args:
            category_id: ID of the category
            active_companies_only: Whether to return only active companies
            limit: Maximum number of companies to return

        Returns:
            List of companies in the category
        """
        filters = [QueryFilter(field="CategoryID", op="eq", value=category_id)]

        if active_companies_only:
            filters.append(QueryFilter(field="IsActive", op="eq", value=True))

        # Query companies with this category
        response = self.client.query("Companies", filters=filters, max_records=limit)
        return response.get("items", [])

    def assign_category_to_company(
        self, category_id: int, company_id: int
    ) -> Dict[str, Any]:
        """
        Assign a category to a company.

        Args:
            category_id: ID of the category to assign
            company_id: ID of the company

        Returns:
            Updated company data
        """
        companies_entity = self.client.entities.get_entity("Companies")
        return companies_entity.update_by_id(company_id, {"CategoryID": category_id})

    def remove_category_from_company(self, company_id: int) -> Dict[str, Any]:
        """
        Remove category assignment from a company.

        Args:
            company_id: ID of the company

        Returns:
            Updated company data
        """
        companies_entity = self.client.entities.get_entity("Companies")
        return companies_entity.update_by_id(company_id, {"CategoryID": None})

    def activate_category(self, category_id: int) -> Dict[str, Any]:
        """
        Activate a company category.

        Args:
            category_id: ID of category to activate

        Returns:
            Updated category data
        """
        return self.update_by_id(category_id, {"IsActive": True})

    def deactivate_category(self, category_id: int) -> Dict[str, Any]:
        """
        Deactivate a company category.

        Args:
            category_id: ID of category to deactivate

        Returns:
            Updated category data
        """
        return self.update_by_id(category_id, {"IsActive": False})

    def update_category_description(
        self, category_id: int, description: str
    ) -> Dict[str, Any]:
        """
        Update the description of a company category.

        Args:
            category_id: ID of category to update
            description: New description

        Returns:
            Updated category data
        """
        return self.update_by_id(category_id, {"Description": description})

    def update_category_color(
        self, category_id: int, color_code: str
    ) -> Dict[str, Any]:
        """
        Update the color code of a company category.

        Args:
            category_id: ID of category to update
            color_code: New color code (hex format)

        Returns:
            Updated category data
        """
        return self.update_by_id(category_id, {"ColorCode": color_code})

    def get_category_usage_stats(self, category_id: int) -> Dict[str, Any]:
        """
        Get usage statistics for a specific category.

        Args:
            category_id: ID of the category

        Returns:
            Dictionary with category usage statistics
        """
        # Get all companies in this category
        companies = self.get_companies_by_category(
            category_id, active_companies_only=False
        )

        active_companies = [c for c in companies if c.get("IsActive")]
        inactive_companies = [c for c in companies if not c.get("IsActive")]

        return {
            "category_id": category_id,
            "total_companies": len(companies),
            "active_companies": len(active_companies),
            "inactive_companies": len(inactive_companies),
            "usage_percentage": (
                len(companies) / self.count() * 100 if self.count() > 0 else 0
            ),
        }
