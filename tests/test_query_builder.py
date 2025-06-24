"""
Tests for QueryBuilder functionality.
"""

from unittest.mock import Mock, patch

import pytest

from py_autotask.entities.base import BaseEntity
from py_autotask.entities.query_builder import (
    FilterOperator,
    QueryBuilder,
)
from py_autotask.exceptions import AutotaskValidationError
from py_autotask.types import QueryRequest


class TestQueryBuilder:
    """Test cases for QueryBuilder class."""

    @pytest.fixture
    def mock_entity(self):
        """Create a mock entity for testing."""
        mock_client = Mock()
        entity = BaseEntity(mock_client, "TestEntity")
        return entity

    @pytest.fixture
    def query_builder(self, mock_entity):
        """Create a QueryBuilder instance for testing."""
        return QueryBuilder(mock_entity)

    def test_where_basic(self, query_builder):
        """Test basic where clause."""
        qb = query_builder.where("status", FilterOperator.EQUAL, "1")

        # Check that filter was added
        assert len(qb._filters) == 1
        assert qb._filters[0]["field"] == "status"
        assert qb._filters[0]["op"] == "eq"
        assert qb._filters[0]["value"] == "1"

    def test_where_string_operator(self, query_builder):
        """Test where clause with string operator."""
        qb = query_builder.where("priority", "gte", 3)

        assert len(qb._filters) == 1
        assert qb._filters[0]["field"] == "priority"
        assert qb._filters[0]["op"] == "gte"
        assert qb._filters[0]["value"] == "3"  # Should be converted to string

    def test_where_null(self, query_builder):
        """Test null filters."""
        qb = query_builder.where_null("description")

        assert len(qb._filters) == 1
        assert qb._filters[0]["field"] == "description"
        assert qb._filters[0]["op"] == "isNull"
        assert "value" not in qb._filters[0]  # No value for null checks

    def test_where_not_null(self, query_builder):
        """Test not null filters."""
        qb = query_builder.where_null("assignedResourceID", False)

        assert len(qb._filters) == 1
        assert qb._filters[0]["field"] == "assignedResourceID"
        assert qb._filters[0]["op"] == "isNotNull"

    def test_where_in(self, query_builder):
        """Test IN filter."""
        qb = query_builder.where_in("status", ["1", "2", "3"])

        assert len(qb._filters) == 1
        assert qb._filters[0]["field"] == "status"
        assert qb._filters[0]["op"] == "in"
        assert qb._filters[0]["value"] == ["1", "2", "3"]

    def test_where_in_empty_list(self, query_builder):
        """Test IN filter with empty list should raise error."""
        with pytest.raises(AutotaskValidationError):
            query_builder.where_in("status", [])

    def test_where_date_range(self, query_builder):
        """Test date range filter."""
        start = "2023-01-01T00:00:00Z"
        end = "2023-12-31T23:59:59Z"

        qb = query_builder.where_date_range("createDateTime", start, end)

        # Should create two filters
        assert len(qb._filters) == 2
        assert qb._filters[0]["field"] == "createDateTime"
        assert qb._filters[0]["op"] == "gte"
        assert qb._filters[0]["value"] == start
        assert qb._filters[1]["field"] == "createDateTime"
        assert qb._filters[1]["op"] == "lte"
        assert qb._filters[1]["value"] == end

    def test_method_chaining(self, query_builder):
        """Test method chaining functionality."""
        qb = (
            query_builder.where("status", "eq", "1")
            .where("priority", "gte", 3)
            .limit(100)
            .select(["id", "title", "status"])
        )

        assert len(qb._filters) == 2
        assert qb._max_records == 100
        assert qb._include_fields == ["id", "title", "status"]

    def test_select(self, query_builder):
        """Test field selection."""
        qb = query_builder.select(["id", "title", "status", "priority"])

        assert qb._include_fields == ["id", "title", "status", "priority"]

    def test_limit(self, query_builder):
        """Test record limit."""
        qb = query_builder.limit(50)

        assert qb._max_records == 50

    def test_order_by(self, query_builder):
        """Test ordering."""
        qb = query_builder.order_by("createDateTime", "desc")

        assert len(qb._sort_fields) == 1
        assert qb._sort_fields[0]["field"] == "createDateTime"
        assert qb._sort_fields[0]["direction"] == "desc"

    def test_order_by_invalid_direction(self, query_builder):
        """Test ordering with invalid direction."""
        with pytest.raises(AutotaskValidationError):
            query_builder.order_by("createDateTime", "invalid")

    def test_reset(self, query_builder):
        """Test query builder reset."""
        qb = (
            query_builder.where("status", "eq", "1")
            .limit(100)
            .select(["id"])
            .order_by("createDateTime")
        )

        # Verify data exists
        assert len(qb._filters) > 0
        assert qb._max_records is not None
        assert qb._include_fields is not None
        assert len(qb._sort_fields) > 0

        # Reset and verify everything is cleared
        qb.reset()
        assert len(qb._filters) == 0
        assert qb._max_records is None
        assert qb._include_fields is None
        assert len(qb._sort_fields) == 0

    def test_build(self, query_builder):
        """Test query request building."""
        qb = (
            query_builder.where("status", "eq", "1")
            .where("priority", "gte", 3)
            .limit(100)
            .select(["id", "title"])
        )

        request = qb.build()

        assert isinstance(request, QueryRequest)
        assert len(request.filter) == 2
        assert request.max_records == 100
        assert request.include_fields == ["id", "title"]

    def test_execute(self, query_builder):
        """Test query execution."""
        mock_response = Mock()
        query_builder.entity.client.query.return_value = mock_response

        qb = query_builder.where("status", "eq", "1")
        result = qb.execute()

        assert result == mock_response
        query_builder.entity.client.query.assert_called_once()

    @patch.object(BaseEntity, "query_all")
    def test_execute_all(self, mock_query_all, query_builder):
        """Test paginated query execution."""
        mock_entities = [{"id": 1}, {"id": 2}]
        mock_query_all.return_value = mock_entities

        qb = query_builder.where("status", "eq", "1")
        result = qb.execute_all()

        assert result == mock_entities
        mock_query_all.assert_called_once()

    @patch.object(BaseEntity, "count")
    def test_count(self, mock_count, query_builder):
        """Test count query."""
        mock_count.return_value = 42

        qb = query_builder.where("status", "eq", "1")
        result = qb.count()

        assert result == 42
        mock_count.assert_called_once()

    def test_first(self, query_builder):
        """Test first result query."""
        mock_response = Mock()
        mock_response.items = [{"id": 1, "title": "Test"}]
        query_builder.entity.client.query.return_value = mock_response

        qb = query_builder.where("status", "eq", "1")
        result = qb.first()

        assert result == {"id": 1, "title": "Test"}

    def test_first_no_results(self, query_builder):
        """Test first result query with no results."""
        mock_response = Mock()
        mock_response.items = []
        query_builder.entity.client.query.return_value = mock_response

        qb = query_builder.where("status", "eq", "1")
        result = qb.first()

        assert result is None

    @patch.object(QueryBuilder, "count")
    def test_exists_true(self, mock_count, query_builder):
        """Test exists check when records exist."""
        mock_count.return_value = 5

        qb = query_builder.where("status", "eq", "1")
        result = qb.exists()

        assert result is True

    @patch.object(QueryBuilder, "count")
    def test_exists_false(self, mock_count, query_builder):
        """Test exists check when no records exist."""
        mock_count.return_value = 0

        qb = query_builder.where("status", "eq", "1")
        result = qb.exists()

        assert result is False

    def test_where_value_required(self, query_builder):
        """Test that value is required for most operators."""
        with pytest.raises(AutotaskValidationError):
            query_builder.where("status", "eq", None)

    def test_where_related(self, query_builder, mock_entity):
        """Test related entity filtering."""
        # Mock the related entity and query
        mock_related_entity = Mock()
        mock_related_response = Mock()
        mock_related_response.items = [{"id": 100}, {"id": 200}]

        mock_entity.client.entities.get_entity.return_value = mock_related_entity

        # Create a mock query builder chain
        mock_qb_chain = Mock()
        mock_qb_chain.where.return_value = mock_qb_chain
        mock_qb_chain.select.return_value = mock_qb_chain
        mock_qb_chain.execute.return_value = mock_related_response

        # Patch the QueryBuilder constructor to return our mock chain
        with patch(
            "py_autotask.entities.query_builder.QueryBuilder",
            return_value=mock_qb_chain,
        ):
            with patch.object(
                mock_entity, "_get_parent_field_name", return_value="companyID"
            ):
                qb = query_builder.where_related(
                    "Companies", "companyName", "contains", "Acme"
                )

        # Should add an IN filter with the related entity IDs
        assert len(qb._filters) == 1
        assert qb._filters[0]["field"] == "companyID"
        assert qb._filters[0]["op"] == "in"
        assert qb._filters[0]["value"] == ["100", "200"]


class TestBaseEntityQueryBuilder:
    """Test the query_builder method added to BaseEntity."""

    def test_query_builder_method_exists(self):
        """Test that query_builder method was added to BaseEntity."""
        mock_client = Mock()
        entity = BaseEntity(mock_client, "TestEntity")

        assert hasattr(entity, "query_builder")

    def test_query_builder_returns_instance(self):
        """Test that query_builder returns a QueryBuilder instance."""
        mock_client = Mock()
        entity = BaseEntity(mock_client, "TestEntity")

        qb = entity.query_builder()

        assert isinstance(qb, QueryBuilder)
        assert qb.entity == entity
