"""
ChangeRequestLinks entity for Autotask API operations.
"""

from typing import Any, Dict, List, Optional

from ..types import EntityDict, QueryFilter
from .base import BaseEntity


class ChangeRequestLinksEntity(BaseEntity):
    """
    Handles all ChangeRequestLinks-related operations for the Autotask API.

    ChangeRequestLinks represent relationships between change requests and other
    entities like tickets, projects, or configuration items, enabling traceability.
    """

    def __init__(self, client, entity_name):
        super().__init__(client, entity_name)

    def create_change_request_link(
        self,
        change_request_id: int,
        linked_entity_type: str,
        linked_entity_id: int,
        link_type: int = 1,
        **kwargs,
    ) -> EntityDict:
        """
        Create a new change request link.

        Args:
            change_request_id: ID of the change request
            linked_entity_type: Type of entity being linked (Ticket, Project, etc.)
            linked_entity_id: ID of the linked entity
            link_type: Type of link relationship (1=Related, 2=Depends, 3=Blocks, etc.)
            **kwargs: Additional link properties

        Returns:
            Created change request link data
        """
        link_data = {
            "ChangeRequestID": change_request_id,
            "LinkedEntityType": linked_entity_type,
            "LinkedEntityID": linked_entity_id,
            "LinkType": link_type,
            **kwargs,
        }

        return self.create(link_data)

    def get_links_by_change_request(
        self, change_request_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all links for a specific change request.

        Args:
            change_request_id: ID of the change request
            limit: Maximum number of links to return

        Returns:
            List of links for the change request
        """
        filters = [
            QueryFilter(field="ChangeRequestID", op="eq", value=change_request_id)
        ]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_links_by_entity(
        self, entity_type: str, entity_id: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get all change request links for a specific entity.

        Args:
            entity_type: Type of the linked entity
            entity_id: ID of the linked entity
            limit: Maximum number of links to return

        Returns:
            List of change request links for the entity
        """
        filters = [
            QueryFilter(field="LinkedEntityType", op="eq", value=entity_type),
            QueryFilter(field="LinkedEntityID", op="eq", value=entity_id),
        ]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_links_by_type(
        self, link_type: int, limit: Optional[int] = None
    ) -> List[EntityDict]:
        """
        Get change request links by link type.

        Args:
            link_type: Type of link relationship
            limit: Maximum number of links to return

        Returns:
            List of links of the specified type
        """
        filters = [QueryFilter(field="LinkType", op="eq", value=link_type)]
        response = self.query(filters=filters, max_records=limit)
        return response.items if hasattr(response, "items") else response

    def get_bidirectional_links(
        self, change_request_id: int
    ) -> Dict[str, List[EntityDict]]:
        """
        Get both outgoing and incoming links for a change request.

        Args:
            change_request_id: ID of the change request

        Returns:
            Dictionary with 'outgoing' and 'incoming' link lists
        """
        # Outgoing links (this change request links to other entities)
        outgoing = self.get_links_by_change_request(change_request_id)

        # Incoming links (other entities link to this change request)
        incoming = self.get_links_by_entity("ChangeRequests", change_request_id)

        return {
            "outgoing_links": outgoing,
            "incoming_links": incoming,
            "total_links": len(outgoing) + len(incoming),
        }

    def create_ticket_link(
        self, change_request_id: int, ticket_id: int, link_type: int = 1
    ) -> EntityDict:
        """
        Create a link between a change request and a ticket.

        Args:
            change_request_id: ID of the change request
            ticket_id: ID of the ticket
            link_type: Type of link relationship

        Returns:
            Created change request link data
        """
        return self.create_change_request_link(
            change_request_id=change_request_id,
            linked_entity_type="Tickets",
            linked_entity_id=ticket_id,
            link_type=link_type,
        )

    def create_project_link(
        self, change_request_id: int, project_id: int, link_type: int = 1
    ) -> EntityDict:
        """
        Create a link between a change request and a project.

        Args:
            change_request_id: ID of the change request
            project_id: ID of the project
            link_type: Type of link relationship

        Returns:
            Created change request link data
        """
        return self.create_change_request_link(
            change_request_id=change_request_id,
            linked_entity_type="Projects",
            linked_entity_id=project_id,
            link_type=link_type,
        )

    def bulk_create_links(
        self, change_request_links: List[Dict[str, Any]]
    ) -> List[EntityDict]:
        """
        Create multiple change request links in batch.

        Args:
            change_request_links: List of link data dictionaries

        Returns:
            List of created link responses
        """
        return self.batch_create(change_request_links)

    def delete_links_by_change_request(self, change_request_id: int) -> List[bool]:
        """
        Delete all links for a specific change request.

        Args:
            change_request_id: ID of the change request

        Returns:
            List of deletion success indicators
        """
        links = self.get_links_by_change_request(change_request_id)
        link_ids = [link["id"] for link in links if "id" in link]

        if link_ids:
            return self.batch_delete(link_ids)
        return []

    def get_link_impact_analysis(self, change_request_id: int) -> Dict[str, Any]:
        """
        Analyze the impact scope of a change request based on its links.

        Args:
            change_request_id: ID of the change request

        Returns:
            Dictionary containing impact analysis
        """
        links = self.get_links_by_change_request(change_request_id)

        impact_analysis = {
            "total_linked_entities": len(links),
            "entity_types": {},
            "link_types": {},
            "high_impact_links": [],
            "dependency_chain_depth": 0,
        }

        # Analyze entity types and link types
        for link in links:
            entity_type = link.get("LinkedEntityType", "Unknown")
            link_type = link.get("LinkType", 0)

            # Count entity types
            if entity_type not in impact_analysis["entity_types"]:
                impact_analysis["entity_types"][entity_type] = 0
            impact_analysis["entity_types"][entity_type] += 1

            # Count link types
            if link_type not in impact_analysis["link_types"]:
                impact_analysis["link_types"][link_type] = 0
            impact_analysis["link_types"][link_type] += 1

            # Identify high-impact links (blocking or dependency relationships)
            if link_type in [2, 3]:  # Depends or Blocks
                impact_analysis["high_impact_links"].append(link)

        impact_analysis["has_dependencies"] = (
            len(impact_analysis["high_impact_links"]) > 0
        )

        return impact_analysis

    def find_circular_dependencies(
        self, change_request_id: int, visited: Optional[List[int]] = None
    ) -> List[List[int]]:
        """
        Find circular dependencies in change request links.

        Args:
            change_request_id: ID of the change request to analyze
            visited: List of already visited change request IDs

        Returns:
            List of circular dependency chains found
        """
        if visited is None:
            visited = []

        if change_request_id in visited:
            # Found circular dependency
            cycle_start = visited.index(change_request_id)
            return [visited[cycle_start:] + [change_request_id]]

        circular_deps = []
        visited = visited + [change_request_id]

        # Get dependency links (link type 2 = depends on)
        links = self.get_links_by_change_request(change_request_id)
        dependency_links = [
            link
            for link in links
            if link.get("LinkType") == 2
            and link.get("LinkedEntityType") == "ChangeRequests"
        ]

        for link in dependency_links:
            linked_cr_id = link.get("LinkedEntityID")
            if linked_cr_id:
                circular_deps.extend(
                    self.find_circular_dependencies(linked_cr_id, visited)
                )

        return circular_deps

    def copy_links_to_change_request(
        self, source_change_request_id: int, target_change_request_id: int
    ) -> List[EntityDict]:
        """
        Copy all links from one change request to another.

        Args:
            source_change_request_id: ID of the source change request
            target_change_request_id: ID of the target change request

        Returns:
            List of created link responses
        """
        source_links = self.get_links_by_change_request(source_change_request_id)

        target_links = []
        for link in source_links:
            # Skip self-referential links
            if (
                link.get("LinkedEntityType") == "ChangeRequests"
                and link.get("LinkedEntityID") == source_change_request_id
            ):
                continue

            target_data = {
                "ChangeRequestID": target_change_request_id,
                "LinkedEntityType": link.get("LinkedEntityType"),
                "LinkedEntityID": link.get("LinkedEntityID"),
                "LinkType": link.get("LinkType"),
            }
            target_links.append(target_data)

        if target_links:
            return self.bulk_create_links(target_links)
        return []
