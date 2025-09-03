"""
Document to Procedure Associations entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict
from .base import BaseEntity


class DocumentToProcedureAssociationsEntity(BaseEntity):
    """
    Handles all Document to Procedure Association-related operations for the Autotask API.

    These associations link documents to procedures, enabling standardized
    documentation for procedures and ensuring relevant documents are easily
    accessible when following specific procedures.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_document_procedure_association(
        self,
        document_id: int,
        procedure_id: int,
        association_type: Optional[str] = None,
        order_number: Optional[int] = None,
        is_required: bool = False,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new document to procedure association.

        Args:
            document_id: ID of the document
            procedure_id: ID of the procedure
            association_type: Type of association (e.g., 'reference', 'attachment')
            order_number: Order in which document appears in procedure
            is_required: Whether document is required for procedure
            **kwargs: Additional association fields

        Returns:
            Created association data
        """
        association_data = {
            "DocumentID": document_id,
            "ProcedureID": procedure_id,
            "IsRequired": is_required,
            **kwargs,
        }

        if association_type:
            association_data["AssociationType"] = association_type
        if order_number is not None:
            association_data["OrderNumber"] = order_number

        return self.create(association_data)

    def get_documents_for_procedure(
        self, procedure_id: int, required_only: bool = False
    ) -> List[EntityDict]:
        """
        Get all documents associated with a specific procedure.

        Args:
            procedure_id: Procedure ID to get documents for
            required_only: Whether to return only required documents

        Returns:
            List of document associations for the procedure
        """
        filters = [{"field": "ProcedureID", "op": "eq", "value": procedure_id}]

        if required_only:
            filters.append({"field": "IsRequired", "op": "eq", "value": "true"})

        return self.query_all(filters=filters)

    def get_procedures_for_document(self, document_id: int) -> List[EntityDict]:
        """
        Get all procedures associated with a specific document.

        Args:
            document_id: Document ID to get procedures for

        Returns:
            List of procedure associations for the document
        """
        return self.query_all(
            filters={"field": "DocumentID", "op": "eq", "value": document_id}
        )

    def update_association_order(
        self, association_id: int, new_order: int
    ) -> EntityDict:
        """
        Update the order number of a document-procedure association.

        Args:
            association_id: ID of the association to update
            new_order: New order number

        Returns:
            Updated association data
        """
        return self.update_by_id(association_id, {"OrderNumber": new_order})

    def set_document_required_status(
        self, association_id: int, is_required: bool
    ) -> EntityDict:
        """
        Set whether a document is required for a procedure.

        Args:
            association_id: ID of the association to update
            is_required: Whether document should be required

        Returns:
            Updated association data
        """
        return self.update_by_id(association_id, {"IsRequired": is_required})

    def get_associations_by_type(
        self, association_type: str, procedure_id: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get document-procedure associations by type.

        Args:
            association_type: Type of association to filter by
            procedure_id: Optional procedure ID to further filter

        Returns:
            List of associations matching the type
        """
        filters = [{"field": "AssociationType", "op": "eq", "value": association_type}]

        if procedure_id:
            filters.append({"field": "ProcedureID", "op": "eq", "value": procedure_id})

        return self.query_all(filters=filters)

    def reorder_procedure_documents(
        self, procedure_id: int, document_order: List[Dict[str, int]]
    ) -> List[EntityDict]:
        """
        Reorder documents for a specific procedure.

        Args:
            procedure_id: Procedure ID to reorder documents for
            document_order: List of dicts with 'association_id' and 'order_number'

        Returns:
            List of updated associations
        """
        results = []

        for item in document_order:
            association_id = item["association_id"]
            order_number = item["order_number"]

            try:
                updated = self.update_association_order(association_id, order_number)
                results.append(updated)
            except Exception as e:
                self.logger.error(
                    f"Failed to update order for association {association_id}: {e}"
                )
                continue

        return results

    def bulk_associate_documents(
        self,
        procedure_id: int,
        document_ids: List[int],
        association_type: Optional[str] = None,
        is_required: bool = False,
    ) -> List[EntityDict]:
        """
        Associate multiple documents with a procedure in bulk.

        Args:
            procedure_id: Procedure ID to associate documents with
            document_ids: List of document IDs to associate
            association_type: Type of association
            is_required: Whether documents are required

        Returns:
            List of created associations
        """
        results = []

        for i, document_id in enumerate(document_ids):
            try:
                association = self.create_document_procedure_association(
                    document_id=document_id,
                    procedure_id=procedure_id,
                    association_type=association_type,
                    order_number=i + 1,
                    is_required=is_required,
                )
                results.append(association)
            except Exception as e:
                self.logger.error(
                    f"Failed to associate document {document_id} with procedure {procedure_id}: {e}"
                )
                continue

        return results

    def remove_association(self, document_id: int, procedure_id: int) -> bool:
        """
        Remove association between a document and procedure.

        Args:
            document_id: Document ID
            procedure_id: Procedure ID

        Returns:
            True if association was removed successfully
        """
        # Find the association
        associations = self.query_all(
            filters=[
                {"field": "DocumentID", "op": "eq", "value": document_id},
                {"field": "ProcedureID", "op": "eq", "value": procedure_id},
            ]
        )

        if not associations:
            return False

        # Remove the first matching association
        return self.delete(associations[0]["id"])

    def get_procedure_document_summary(self, procedure_id: int) -> Dict[str, Any]:
        """
        Get summary of documents associated with a procedure.

        Args:
            procedure_id: Procedure ID to get summary for

        Returns:
            Dictionary containing document association summary
        """
        associations = self.get_documents_for_procedure(procedure_id)

        required_count = sum(1 for assoc in associations if assoc.get("IsRequired"))

        # Group by association type
        by_type = {}
        for assoc in associations:
            assoc_type = assoc.get("AssociationType", "unspecified")
            if assoc_type not in by_type:
                by_type[assoc_type] = []
            by_type[assoc_type].append(assoc)

        return {
            "procedure_id": procedure_id,
            "total_documents": len(associations),
            "required_documents": required_count,
            "optional_documents": len(associations) - required_count,
            "documents_by_type": {
                type_name: len(docs) for type_name, docs in by_type.items()
            },
            "has_ordered_documents": any(
                assoc.get("OrderNumber") is not None for assoc in associations
            ),
        }
