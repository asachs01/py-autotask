"""
QuoteTemplates entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class QuoteTemplatesEntity(BaseEntity):
    """
    Handles all Quote Template-related operations for the Autotask API.

    Quote Templates are predefined templates for creating quotes with standard content.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_quote_template(
        self,
        name: str,
        description: str,
        is_active: bool = True,
        template_category: Optional[str] = None,
        default_payment_terms_id: Optional[int] = None,
        default_tax_category_id: Optional[int] = None,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new quote template.

        Args:
            name: Name of the template
            description: Description of the template
            is_active: Whether the template is active
            template_category: Category/type of the template
            default_payment_terms_id: Default payment terms for quotes from this template
            default_tax_category_id: Default tax category
            header_text: Header text to include in quotes
            footer_text: Footer text to include in quotes
            **kwargs: Additional template fields

        Returns:
            Created quote template data
        """
        template_data = {
            "Name": name,
            "Description": description,
            "IsActive": is_active,
            **kwargs,
        }

        if template_category:
            template_data["TemplateCategory"] = template_category
        if default_payment_terms_id:
            template_data["DefaultPaymentTermsID"] = default_payment_terms_id
        if default_tax_category_id:
            template_data["DefaultTaxCategoryID"] = default_tax_category_id
        if header_text:
            template_data["HeaderText"] = header_text
        if footer_text:
            template_data["FooterText"] = footer_text

        return self.create(template_data)

    def get_active_templates(self, limit: Optional[int] = None) -> List[EntityDict]:
        """
        Get all active quote templates.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of active quote templates
        """
        filters = [QueryFilter(field="IsActive", op="eq", value=True)]

        return self.query(filters=filters, max_records=limit)

    def search_templates_by_name(
        self, name: str, exact_match: bool = False, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search for quote templates by name.

        Args:
            name: Template name to search for
            exact_match: Whether to do exact match or partial match
            limit: Maximum number of records to return

        Returns:
            List of matching templates
        """
        if exact_match:
            filters = [QueryFilter(field="Name", op="eq", value=name)]
        else:
            filters = [QueryFilter(field="Name", op="contains", value=name)]

        return self.query(filters=filters, max_records=limit)

    def get_templates_by_category(
        self, category: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get quote templates by category.

        Args:
            category: Template category to filter by
            limit: Maximum number of records to return

        Returns:
            List of templates in the specified category
        """
        filters = [QueryFilter(field="TemplateCategory", op="eq", value=category)]

        return self.query(filters=filters, max_records=limit)

    def search_templates_by_description(
        self, search_text: str, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Search templates by description content.

        Args:
            search_text: Text to search for in descriptions
            limit: Maximum number of records to return

        Returns:
            List of templates with matching descriptions
        """
        filters = [QueryFilter(field="Description", op="contains", value=search_text)]

        return self.query(filters=filters, max_records=limit)

    def get_templates_with_payment_terms(
        self, payment_terms_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get templates that use specific payment terms.

        Args:
            payment_terms_id: ID of the payment terms
            limit: Maximum number of records to return

        Returns:
            List of templates using the specified payment terms
        """
        filters = [
            QueryFilter(field="DefaultPaymentTermsID", op="eq", value=payment_terms_id)
        ]

        return self.query(filters=filters, max_records=limit)

    def activate_template(self, template_id: int) -> EntityDict:
        """
        Activate a quote template.

        Args:
            template_id: ID of the template

        Returns:
            Updated template data
        """
        return self.update_by_id(template_id, {"IsActive": True})

    def deactivate_template(self, template_id: int) -> EntityDict:
        """
        Deactivate a quote template.

        Args:
            template_id: ID of the template

        Returns:
            Updated template data
        """
        return self.update_by_id(template_id, {"IsActive": False})

    def update_template_content(
        self,
        template_id: int,
        header_text: Optional[str] = None,
        footer_text: Optional[str] = None,
        description: Optional[str] = None,
    ) -> EntityDict:
        """
        Update the content of a quote template.

        Args:
            template_id: ID of the template
            header_text: New header text
            footer_text: New footer text
            description: New description

        Returns:
            Updated template data
        """
        update_data = {}
        if header_text is not None:
            update_data["HeaderText"] = header_text
        if footer_text is not None:
            update_data["FooterText"] = footer_text
        if description is not None:
            update_data["Description"] = description

        return self.update_by_id(template_id, update_data)

    def update_template_defaults(
        self,
        template_id: int,
        payment_terms_id: Optional[int] = None,
        tax_category_id: Optional[int] = None,
    ) -> EntityDict:
        """
        Update the default settings of a template.

        Args:
            template_id: ID of the template
            payment_terms_id: New default payment terms ID
            tax_category_id: New default tax category ID

        Returns:
            Updated template data
        """
        update_data = {}
        if payment_terms_id is not None:
            update_data["DefaultPaymentTermsID"] = payment_terms_id
        if tax_category_id is not None:
            update_data["DefaultTaxCategoryID"] = tax_category_id

        return self.update_by_id(template_id, update_data)

    def clone_template(self, template_id: int, new_name: str) -> EntityDict:
        """
        Clone an existing template with a new name.

        Args:
            template_id: ID of the template to clone
            new_name: Name for the cloned template

        Returns:
            Created template data
        """
        original_template = self.get_by_id(template_id)
        if not original_template:
            raise ValueError(f"Template {template_id} not found")

        # Create new template with copied data
        clone_data = {
            "Name": new_name,
            "Description": f"Copy of {original_template.get('Description', '')}",
            "IsActive": True,  # New templates start as active
            "TemplateCategory": original_template.get("TemplateCategory"),
            "DefaultPaymentTermsID": original_template.get("DefaultPaymentTermsID"),
            "DefaultTaxCategoryID": original_template.get("DefaultTaxCategoryID"),
            "HeaderText": original_template.get("HeaderText"),
            "FooterText": original_template.get("FooterText"),
        }

        # Remove None values
        clone_data = {k: v for k, v in clone_data.items() if v is not None}

        return self.create(clone_data)

    def get_template_usage_statistics(self, template_id: int) -> Dict[str, Any]:
        """
        Get usage statistics for a specific template.

        Note: This would require querying quote data to see how often the template is used.

        Args:
            template_id: ID of the template

        Returns:
            Dictionary with usage statistics
        """
        template = self.get_by_id(template_id)
        if not template:
            return {"error": "Template not found"}

        # Note: This would need to query the Quotes entity to get actual usage stats
        # For now, return basic template information
        stats = {
            "template_id": template_id,
            "template_name": template.get("Name"),
            "is_active": template.get("IsActive", False),
            "category": template.get("TemplateCategory"),
            "has_header": bool(template.get("HeaderText")),
            "has_footer": bool(template.get("FooterText")),
            "has_default_payment_terms": bool(template.get("DefaultPaymentTermsID")),
            # Actual usage stats would come from querying quotes:
            # "quotes_created": 0,  # Would need to query Quotes table
            # "last_used_date": None,  # Would need to query Quotes table
        }

        return stats

    def get_template_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about quote templates.

        Returns:
            Dictionary containing template statistics
        """
        all_templates = self.query()

        # Group by category
        category_counts = {}
        for template in all_templates:
            category = template.get("TemplateCategory", "Uncategorized")
            category_counts[category] = category_counts.get(category, 0) + 1

        stats = {
            "total_templates": len(all_templates),
            "active_templates": len(
                [t for t in all_templates if t.get("IsActive", False)]
            ),
            "inactive_templates": len(
                [t for t in all_templates if not t.get("IsActive", False)]
            ),
            "templates_with_header": len(
                [t for t in all_templates if t.get("HeaderText")]
            ),
            "templates_with_footer": len(
                [t for t in all_templates if t.get("FooterText")]
            ),
            "templates_with_payment_terms": len(
                [t for t in all_templates if t.get("DefaultPaymentTermsID")]
            ),
            "templates_by_category": category_counts,
            "unique_categories": len(category_counts),
        }

        return stats

    def create_standard_templates(self) -> List[EntityDict]:
        """
        Create a set of standard quote templates.

        Returns:
            List of created standard templates
        """
        standard_templates = [
            {
                "name": "Standard Service Quote",
                "description": "Template for standard service quotations",
                "template_category": "Services",
                "header_text": "Thank you for your interest in our services.",
                "footer_text": "We look forward to working with you.",
            },
            {
                "name": "Product Quote",
                "description": "Template for product-based quotations",
                "template_category": "Products",
                "header_text": "Product Quote - Quality products at competitive prices",
                "footer_text": "All products include warranty and support.",
            },
            {
                "name": "Maintenance Agreement",
                "description": "Template for maintenance service agreements",
                "template_category": "Maintenance",
                "header_text": "Maintenance Service Agreement Quote",
                "footer_text": "Regular maintenance ensures optimal performance.",
            },
            {
                "name": "Custom Project",
                "description": "Template for custom project quotations",
                "template_category": "Projects",
                "header_text": "Custom Project Proposal",
                "footer_text": "Timeline and deliverables as discussed.",
            },
        ]

        created_templates = []
        for template_data in standard_templates:
            try:
                created_template = self.create_quote_template(**template_data)
                created_templates.append(created_template)
            except Exception as e:
                # Log the error but continue with other templates
                print(f"Error creating template {template_data['name']}: {e}")

        return created_templates
