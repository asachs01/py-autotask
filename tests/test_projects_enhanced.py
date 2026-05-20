"""
Comprehensive tests for the enhanced ProjectsEntity with PSA features.

Tests cover budgeting, cost tracking, resource allocation, milestone management,
profitability analysis, templates, and Gantt/dependency functionality.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from py_autotask.entities.projects import ProjectsEntity, ProjectConstants
from py_autotask.exceptions import AutotaskValidationError


@pytest.fixture
def mock_client():
    """Create a mock client for testing."""
    client = Mock()
    return client


@pytest.fixture
def projects_entity(mock_client):
    """Create a ProjectsEntity instance with mocked client."""
    return ProjectsEntity(mock_client, "Projects")


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "id": 12345,
        "ProjectName": "Test Project",
        "AccountID": 1001,
        "Type": ProjectConstants.PROJECT_TYPE_TIME_MATERIALS,
        "Status": ProjectConstants.STATUS_IN_PROGRESS,
        "StartDate": "2024-01-01T00:00:00Z",
        "EndDate": "2024-06-30T00:00:00Z",
        "ProjectCost": 100000,
        "LaborCost": 75000,
        "ExpenseCost": 15000,
        "MaterialCost": 10000,
        "EstimatedTime": 1000,
        "ProjectManagerResourceID": 5001
    }


@pytest.fixture
def sample_tasks():
    """Sample tasks data for testing."""
    return [
        {
            "id": 1,
            "title": "Project Setup",
            "projectID": 12345,
            "assignedResourceID": 5001,
            "estimatedHours": 40,
            "percentComplete": 100,
            "status": 5,  # Complete
            "startDate": "2024-01-01T00:00:00Z",
            "endDate": "2024-01-10T00:00:00Z",
            "predecessors": ""
        },
        {
            "id": 2,
            "title": "Development Phase",
            "projectID": 12345,
            "assignedResourceID": 5002,
            "estimatedHours": 320,
            "percentComplete": 75,
            "status": 2,  # In Progress
            "startDate": "2024-01-11T00:00:00Z",
            "endDate": "2024-04-30T00:00:00Z",
            "predecessors": "1"
        },
        {
            "id": 3,
            "title": "Testing Phase",
            "projectID": 12345,
            "assignedResourceID": 5003,
            "estimatedHours": 160,
            "percentComplete": 25,
            "status": 2,  # In Progress
            "startDate": "2024-05-01T00:00:00Z",
            "endDate": "2024-06-15T00:00:00Z",
            "predecessors": "2"
        }
    ]


class TestProjectConstants:
    """Test ProjectConstants class."""
    
    def test_project_type_constants(self):
        """Test project type constants are defined correctly."""
        assert ProjectConstants.PROJECT_TYPE_FIXED_PRICE == 1
        assert ProjectConstants.PROJECT_TYPE_TIME_MATERIALS == 2
        assert ProjectConstants.PROJECT_TYPE_MILESTONE == 3
        assert ProjectConstants.PROJECT_TYPE_BLOCK_HOURS == 4
        assert ProjectConstants.PROJECT_TYPE_RETAINER == 5
    
    def test_status_constants(self):
        """Test status constants are defined correctly."""
        assert ProjectConstants.STATUS_NEW == 1
        assert ProjectConstants.STATUS_IN_PROGRESS == 2
        assert ProjectConstants.STATUS_ON_HOLD == 3
        assert ProjectConstants.STATUS_WAITING == 4
        assert ProjectConstants.STATUS_COMPLETE == 5
        assert ProjectConstants.STATUS_CANCELLED == 7
        assert ProjectConstants.STATUS_INACTIVE == 8
    
    def test_get_project_types(self):
        """Test get_project_types class method."""
        types = ProjectConstants.get_project_types()
        assert len(types) == 5
        assert types[1] == "Fixed Price"
        assert types[2] == "Time & Materials"
    
    def test_get_status_names(self):
        """Test get_status_names class method."""
        statuses = ProjectConstants.get_status_names()
        assert len(statuses) == 7
        assert statuses[1] == "New"
        assert statuses[2] == "In Progress"
        assert statuses[5] == "Complete"
    
    def test_get_priority_names(self):
        """Test get_priority_names class method."""
        priorities = ProjectConstants.get_priority_names()
        assert len(priorities) == 4
        assert priorities[1] == "Low"
        assert priorities[4] == "Critical"


class TestBudgetingAndCostTracking:
    """Test budgeting and cost tracking functionality."""
    
    def test_set_project_budget_success(self, projects_entity, mock_client):
        """Test successful budget setting."""
        budget_data = {
            "total_budget": 100000,
            "labor_budget": 75000,
            "expense_budget": 15000,
            "material_budget": 10000,
            "budget_hours": 1000
        }
        
        mock_client.update = Mock(return_value={"id": 12345})
        projects_entity.update_by_id = Mock(return_value={"id": 12345})
        
        result = projects_entity.set_project_budget(12345, budget_data)
        
        assert result["id"] == 12345
        projects_entity.update_by_id.assert_called_once()
    
    def test_set_project_budget_missing_required_field(self, projects_entity):
        """Test budget setting with missing required field."""
        budget_data = {"labor_budget": 75000}  # Missing total_budget
        
        with pytest.raises(AutotaskValidationError, match="Missing required budget field"):
            projects_entity.set_project_budget(12345, budget_data)
    
    def test_set_project_budget_negative_values(self, projects_entity):
        """Test budget setting with negative values."""
        budget_data = {"total_budget": -100000}
        
        with pytest.raises(AutotaskValidationError, match="cannot be negative"):
            projects_entity.set_project_budget(12345, budget_data)
    
    def test_track_project_costs(self, projects_entity, sample_project_data):
        """Test project cost tracking."""
        projects_entity.get_by_id = Mock(return_value=sample_project_data)
        
        cost_data = {
            "actual_labor": 80000,
            "actual_expenses": 12000,
            "actual_materials": 8000,
            "actual_hours": 900
        }
        
        result = projects_entity.track_project_costs(12345, cost_data)
        
        assert result["project_id"] == 12345
        assert "tracking_date" in result
        assert "actual_costs" in result
        assert "budget_comparison" in result
        assert "variances" in result
        assert "cost_performance" in result
        
        # Check variance calculations
        labor_variance = result["variances"]["labor_budget"]
        assert labor_variance["amount"] == 80000 - 75000  # actual - budget
    
    def test_get_budget_status(self, projects_entity, sample_project_data):
        """Test getting budget status."""
        projects_entity.get_by_id = Mock(return_value=sample_project_data)
        projects_entity.get_project_time_entries = Mock(return_value=[
            {"HoursWorked": 400, "BillableAmount": 32000},
            {"HoursWorked": 350, "BillableAmount": 28000}
        ])
        
        result = projects_entity.get_budget_status(12345)
        
        assert result["project_id"] == 12345
        assert result["budgets"]["total_budget"] == 100000
        assert result["actuals"]["actual_hours"] == 750  # 400 + 350
        assert result["actuals"]["actual_labor_cost"] == 60000  # 32000 + 28000
        assert "utilization" in result
        assert "alerts" in result
    
    def test_calculate_project_profitability(self, projects_entity, sample_project_data):
        """Test profitability calculation."""
        projects_entity.get_by_id = Mock(return_value=sample_project_data)
        projects_entity.get_budget_status = Mock(return_value={
            "budgets": {"total_budget": 100000},
            "actuals": {"actual_labor_cost": 60000, "actual_expenses": 12000, "actual_materials": 8000, "actual_hours": 750}
        })
        
        result = projects_entity.calculate_project_profitability(12345)
        
        assert result["project_id"] == 12345
        assert result["financial_summary"]["revenue"] == 100000
        assert result["financial_summary"]["total_costs"] == 80000  # 60k + 12k + 8k
        assert result["financial_summary"]["gross_profit"] == 20000
        assert result["financial_summary"]["gross_margin_percent"] == 20.0
        assert result["status"] == "profitable"  # 20% margin


class TestResourceAllocation:
    """Test resource allocation functionality."""
    
    def test_allocate_resource_success(self, projects_entity):
        """Test successful resource allocation."""
        allocation_data = {
            "allocation_percentage": 80,
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-06-30T00:00:00Z",
            "role": "Senior Developer",
            "hourly_rate": 100,
            "estimated_hours": 800
        }
        
        result = projects_entity.allocate_resource(12345, 5001, allocation_data)
        
        assert result["project_id"] == 12345
        assert result["resource_id"] == 5001
        assert result["allocation_percentage"] == 80
        assert result["role"] == "Senior Developer"
        assert result["status"] == "active"
    
    def test_allocate_resource_invalid_percentage(self, projects_entity):
        """Test resource allocation with invalid percentage."""
        allocation_data = {
            "allocation_percentage": 150,  # Invalid
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-06-30T00:00:00Z"
        }
        
        with pytest.raises(AutotaskValidationError, match="between 0 and 100"):
            projects_entity.allocate_resource(12345, 5001, allocation_data)
    
    def test_allocate_resource_invalid_dates(self, projects_entity):
        """Test resource allocation with invalid dates."""
        allocation_data = {
            "allocation_percentage": 80,
            "start_date": "2024-06-30T00:00:00Z",
            "end_date": "2024-01-01T00:00:00Z"  # End before start
        }
        
        with pytest.raises(AutotaskValidationError, match="End date must be after start date"):
            projects_entity.allocate_resource(12345, 5001, allocation_data)
    
    def test_get_resource_allocation(self, projects_entity, sample_project_data, sample_tasks):
        """Test getting resource allocation."""
        projects_entity.get_by_id = Mock(return_value=sample_project_data)
        projects_entity.get_project_tasks = Mock(return_value=sample_tasks)
        
        result = projects_entity.get_resource_allocation(12345)
        
        assert result["project_id"] == 12345
        assert result["total_estimated_hours"] == 520  # Sum of all task hours
        assert result["resources_allocated"] == 3  # Three different resources
        assert len(result["resource_breakdown"]) == 3
        
        # Check resource breakdown
        resource_5001 = next(r for r in result["resource_breakdown"] if r["resource_id"] == 5001)
        assert resource_5001["total_hours"] == 40
        assert resource_5001["tasks_assigned"] == 1
    
    def test_optimize_resource_allocation(self, projects_entity, sample_project_data):
        """Test resource allocation optimization."""
        projects_entity.get_by_id = Mock(return_value=sample_project_data)
        projects_entity.get_resource_allocation = Mock(return_value={
            "project_id": 12345,
            "resource_breakdown": [
                {"resource_id": 5001, "utilization": 90, "completion_percentage": 100},  # Over-allocated
                {"resource_id": 5002, "utilization": 15, "completion_percentage": 50},   # Under-allocated
                {"resource_id": 5003, "utilization": 75, "completion_percentage": 80}    # Balanced
            ]
        })
        
        result = projects_entity.optimize_resource_allocation(12345)
        
        assert result["project_id"] == 12345
        assert len(result["optimization_opportunities"]) > 0
        assert len(result["recommendations"]) > 0
        assert result["efficiency_score"] > 0
        
        # Should identify over and under allocation
        assert any("over_allocation" in opp["type"] for opp in result["risk_factors"])
        assert any("under_utilization" in opp["type"] for opp in result["optimization_opportunities"])


class TestMilestoneAndPhaseManagement:
    """Test milestone and phase management functionality."""
    
    def test_add_project_phase_success(self, projects_entity):
        """Test successful phase creation."""
        phase_data = {
            "title": "Development Phase",
            "description": "Main development work",
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-03-31T00:00:00Z",
            "estimated_hours": 400,
            "budget": 50000
        }
        
        result = projects_entity.add_project_phase(12345, phase_data)
        
        assert result["project_id"] == 12345
        assert result["title"] == "Development Phase"
        assert result["status"] == ProjectConstants.PHASE_STATUS_NEW
        assert "id" in result
        assert result["estimated_hours"] == 400
        assert result["budget"] == 50000
    
    def test_add_project_phase_missing_fields(self, projects_entity):
        """Test phase creation with missing required fields."""
        phase_data = {"title": "Development Phase"}  # Missing required fields
        
        with pytest.raises(AutotaskValidationError, match="Missing required phase field"):
            projects_entity.add_project_phase(12345, phase_data)
    
    def test_update_phase_progress(self, projects_entity):
        """Test updating phase progress."""
        result = projects_entity.update_phase_progress("phase_123", 75)
        
        assert result["phase_id"] == "phase_123"
        assert result["progress_percentage"] == 75
        assert result["status"] == ProjectConstants.PHASE_STATUS_IN_PROGRESS
        assert "updated_date" in result
    
    def test_update_phase_progress_invalid_value(self, projects_entity):
        """Test updating phase progress with invalid value."""
        with pytest.raises(AutotaskValidationError, match="between 0 and 100"):
            projects_entity.update_phase_progress("phase_123", 150)
    
    def test_get_project_milestones(self, projects_entity, sample_project_data):
        """Test getting project milestones."""
        projects_entity.get_by_id = Mock(return_value=sample_project_data)
        projects_entity.get_project_tasks = Mock(return_value=[
            {
                "id": 1,
                "title": "Project Kickoff Milestone",
                "estimatedHours": 0,  # Zero hours indicates milestone
                "endDate": "2024-01-15T00:00:00Z",
                "status": 5,  # Complete
                "percentComplete": 100,
                "predecessors": ""
            },
            {
                "id": 2,
                "title": "Development Complete Milestone",
                "estimatedHours": 0,
                "endDate": "2024-04-30T00:00:00Z",
                "status": 2,  # In Progress
                "percentComplete": 50,
                "predecessors": "1"
            }
        ])
        
        result = projects_entity.get_project_milestones(12345)
        
        assert len(result) == 2
        assert result[0]["milestone_id"] == 1
        assert result[0]["title"] == "Project Kickoff Milestone"
        assert result[0]["is_completed"] == True
        assert result[1]["is_completed"] == False
        
        # Should be sorted by due date
        assert result[0]["due_date"] <= result[1]["due_date"]
    
    def test_track_milestone_completion(self, projects_entity):
        """Test tracking milestone completion."""
        projects_entity.client.query = Mock(return_value=[{
            "id": 1,
            "title": "Project Milestone",
            "projectID": 12345,
            "status": 5,  # Complete
            "endDate": "2024-01-15T00:00:00Z",
            "completedDateTime": "2024-01-14T10:00:00Z",
            "percentComplete": 100,
            "predecessors": ""
        }])
        projects_entity.get_project_tasks = Mock(return_value=[])
        
        result = projects_entity.track_milestone_completion(1)
        
        assert result["milestone_id"] == 1
        assert result["project_id"] == 12345
        assert result["is_completed"] == True
        assert result["dependent_tasks"] == 0
        assert "impact_analysis" in result
        assert "completion_probability" in result["impact_analysis"]


class TestProfitabilityAnalysis:
    """Test profitability analysis helper methods."""
    
    def test_calculate_gross_margin(self, projects_entity):
        """Test gross margin calculation."""
        projects_entity.calculate_project_profitability = Mock(return_value={
            "financial_summary": {
                "gross_margin": 25000,
                "gross_margin_percent": 25.0,
                "revenue": 100000,
                "total_costs": 75000
            }
        })
        
        result = projects_entity.calculate_gross_margin(12345)
        
        assert result["project_id"] == 12345
        assert result["gross_margin"] == 25000
        assert result["gross_margin_percent"] == 25.0
        assert result["revenue"] == 100000
        assert result["total_costs"] == 75000
        assert "calculation_date" in result
    
    def test_get_profitability_report(self, projects_entity):
        """Test comprehensive profitability report."""
        projects_entity.calculate_project_profitability = Mock(return_value={
            "status": "profitable",
            "financial_summary": {"total_costs": 80000}
        })
        projects_entity.get_budget_status = Mock(return_value={
            "budgets": {"total_budget": 100000}
        })
        
        result = projects_entity.get_profitability_report(12345)
        
        assert "budget_analysis" in result
        assert "performance_indicators" in result
        assert "recommendations" in result
        assert result["performance_indicators"]["budget_variance"] == 20000  # 100k - 80k
    
    def test_compare_actual_vs_estimated(self, projects_entity, sample_project_data):
        """Test actual vs estimated comparison."""
        projects_entity.get_by_id = Mock(return_value=sample_project_data)
        projects_entity.get_budget_status = Mock(return_value={
            "budgets": {"total_budget": 100000, "budget_hours": 1000},
            "actuals": {"actual_labor_cost": 80000, "actual_expenses": 12000, 
                       "actual_materials": 8000, "actual_hours": 1100}
        })
        
        result = projects_entity.compare_actual_vs_estimated(12345)
        
        assert result["project_id"] == 12345
        assert result["cost_comparison"]["estimated_total"] == 100000
        assert result["cost_comparison"]["actual_total"] == 100000  # 80k + 12k + 8k
        assert result["time_comparison"]["estimated_hours"] == 1000
        assert result["time_comparison"]["actual_hours"] == 1100
        assert result["time_comparison"]["variance_hours"] == -100  # over by 100 hours
        assert "accuracy_metrics" in result


class TestProjectTemplates:
    """Test project template functionality."""
    
    def test_get_project_templates(self, projects_entity):
        """Test getting available templates."""
        templates = projects_entity.get_project_templates()
        
        assert len(templates) > 0
        assert any(t["template_id"] == "web_development" for t in templates)
        assert any(t["template_id"] == "infrastructure_upgrade" for t in templates)
        
        web_template = next(t for t in templates if t["template_id"] == "web_development")
        assert web_template["name"] == "Web Development Project"
        assert len(web_template["phases"]) == 5
    
    def test_create_from_template(self, projects_entity):
        """Test creating project from template."""
        projects_entity.create_project = Mock(return_value={"id": 12345})
        projects_entity.add_project_phase = Mock(return_value={"id": "phase_1"})
        
        project_data = {
            "project_name": "New Web Project",
            "account_id": 1001,
            "start_date": "2024-01-01T00:00:00Z",
            "end_date": "2024-06-30T00:00:00Z"
        }
        
        result = projects_entity.create_from_template("web_development", project_data)
        
        assert result["id"] == 12345
        projects_entity.create_project.assert_called_once()
    
    def test_create_from_template_not_found(self, projects_entity):
        """Test creating project from non-existent template."""
        project_data = {"project_name": "Test Project", "account_id": 1001}
        
        with pytest.raises(AutotaskValidationError, match="template .* not found"):
            projects_entity.create_from_template("nonexistent_template", project_data)
    
    def test_save_as_template(self, projects_entity, sample_project_data, sample_tasks):
        """Test saving project as template."""
        projects_entity.get_by_id = Mock(return_value=sample_project_data)
        projects_entity.get_project_tasks = Mock(return_value=sample_tasks)
        projects_entity.get_project_milestones = Mock(return_value=[])
        
        result = projects_entity.save_as_template(
            12345, 
            "Custom Template", 
            "Template based on successful project"
        )
        
        assert result["name"] == "Custom Template"
        assert result["created_from_project"] == 12345
        assert "template_id" in result
        assert len(result["task_templates"]) == len(sample_tasks)
        assert "project_defaults" in result


class TestGanttAndDependencies:
    """Test Gantt chart and dependency management."""
    
    def test_get_gantt_data(self, projects_entity, sample_project_data, sample_tasks):
        """Test getting Gantt chart data."""
        projects_entity.get_by_id = Mock(return_value=sample_project_data)
        projects_entity.get_project_tasks = Mock(return_value=sample_tasks)
        projects_entity.get_project_milestones = Mock(return_value=[])
        projects_entity.calculate_critical_path = Mock(return_value=[])
        
        result = projects_entity.get_gantt_data(12345)
        
        assert result["project_id"] == 12345
        assert result["project_name"] == "Test Project"
        assert len(result["tasks"]) == 3
        assert result["timeline_metadata"]["total_tasks"] == 3
        assert result["timeline_metadata"]["completed_tasks"] == 1  # One task 100% complete
        assert "critical_path" in result
        assert "resource_assignments" in result
    
    def test_add_task_dependency_success(self, projects_entity):
        """Test adding task dependency successfully."""
        projects_entity.client.query = Mock(side_effect=[
            [{"id": 2, "predecessors": ""}],  # Dependent task
            [{"id": 1, "predecessors": ""}]   # Predecessor task
        ])
        projects_entity.client.update = Mock(return_value={"id": 2})
        projects_entity._has_circular_dependency = Mock(return_value=False)
        
        result = projects_entity.add_task_dependency(2, 1, "finish_to_start")
        
        assert result["task_id"] == 2
        assert result["depends_on_id"] == 1
        assert result["dependency_type"] == "finish_to_start"
        assert result["status"] == "active"
        projects_entity.client.update.assert_called_once()
    
    def test_add_task_dependency_invalid_type(self, projects_entity):
        """Test adding task dependency with invalid type."""
        with pytest.raises(AutotaskValidationError, match="Invalid dependency type"):
            projects_entity.add_task_dependency(2, 1, "invalid_type")
    
    def test_add_task_dependency_circular(self, projects_entity):
        """Test adding task dependency that creates circular reference."""
        projects_entity.client.query = Mock(side_effect=[
            [{"id": 2, "predecessors": ""}],  # Dependent task
            [{"id": 1, "predecessors": ""}]   # Predecessor task
        ])
        projects_entity._has_circular_dependency = Mock(return_value=True)
        
        with pytest.raises(AutotaskValidationError, match="circular reference"):
            projects_entity.add_task_dependency(2, 1)
    
    def test_calculate_critical_path(self, projects_entity):
        """Test critical path calculation."""
        tasks = [
            {
                "id": 1,
                "title": "Task 1",
                "estimatedHours": 16,  # 2 days
                "predecessors": ""
            },
            {
                "id": 2,
                "title": "Task 2", 
                "estimatedHours": 24,  # 3 days
                "predecessors": "1"
            },
            {
                "id": 3,
                "title": "Task 3",
                "estimatedHours": 8,   # 1 day
                "predecessors": "2"
            }
        ]
        
        projects_entity.get_project_tasks = Mock(return_value=tasks)
        
        result = projects_entity.calculate_critical_path(12345)
        
        assert len(result) > 0
        # All tasks should be on critical path in this linear sequence
        assert len(result) == 3
        assert result[0]["task_id"] == 1
        assert result[0]["early_start"] == 0
        assert result[1]["task_id"] == 2
        assert result[1]["early_start"] == 2  # Starts after Task 1 finishes


class TestValidationAndHelpers:
    """Test validation and helper methods."""
    
    def test_validate_project_data_success(self, projects_entity):
        """Test successful project data validation."""
        project_data = {
            "ProjectName": "Valid Project",
            "AccountID": 1001,
            "StartDate": "2024-01-01T00:00:00Z",
            "EndDate": "2024-06-30T00:00:00Z",
            "ProjectCost": 100000,
            "Type": 2,
            "Status": 1
        }
        
        errors = projects_entity.validate_project_data(project_data)
        assert len(errors) == 0
    
    def test_validate_project_data_missing_fields(self, projects_entity):
        """Test project data validation with missing required fields."""
        project_data = {"ProjectName": "Test Project"}  # Missing AccountID
        
        errors = projects_entity.validate_project_data(project_data)
        assert len(errors) > 0
        assert any("Missing required field: AccountID" in error for error in errors)
    
    def test_validate_project_data_invalid_dates(self, projects_entity):
        """Test project data validation with invalid dates."""
        project_data = {
            "ProjectName": "Test Project",
            "AccountID": 1001,
            "StartDate": "2024-06-30T00:00:00Z",
            "EndDate": "2024-01-01T00:00:00Z"  # End before start
        }
        
        errors = projects_entity.validate_project_data(project_data)
        assert any("End date must be after start date" in error for error in errors)
    
    def test_validate_project_data_negative_budget(self, projects_entity):
        """Test project data validation with negative budget values."""
        project_data = {
            "ProjectName": "Test Project",
            "AccountID": 1001,
            "ProjectCost": -50000
        }
        
        errors = projects_entity.validate_project_data(project_data)
        assert any("must be a non-negative number" in error for error in errors)
    
    def test_get_project_health_score(self, projects_entity, sample_project_data):
        """Test project health score calculation."""
        projects_entity.get_by_id = Mock(return_value=sample_project_data)
        projects_entity.get_budget_status = Mock(return_value={
            "utilization": {"total_budget": 85}
        })
        projects_entity.get_resource_allocation = Mock(return_value={
            "resources_allocated": 3,
            "resource_breakdown": [
                {"utilization": 75},
                {"utilization": 80},
                {"utilization": 70}
            ]
        })
        projects_entity.calculate_project_profitability = Mock(return_value={
            "status": "profitable",
            "financial_summary": {"gross_margin_percent": 15}
        })
        projects_entity.get_project_tasks = Mock(return_value=[
            {"percentComplete": 80},
            {"percentComplete": 60},
            {"percentComplete": 90}
        ])
        
        result = projects_entity.get_project_health_score(12345)
        
        assert result["project_id"] == 12345
        assert 0 <= result["overall_score"] <= 100
        assert result["health_status"] in ["excellent", "good", "fair", "poor"]
        assert "factor_scores" in result
        assert "recommendations" in result
        assert len(result["factor_scores"]) == 5  # All health factors


class TestHelperMethods:
    """Test internal helper methods."""
    
    def test_calculate_task_duration(self, projects_entity):
        """Test task duration calculation."""
        start = "2024-01-01T00:00:00Z"
        end = "2024-01-10T00:00:00Z"
        
        duration = projects_entity._calculate_task_duration(start, end)
        assert duration == 9  # 9 days difference
    
    def test_calculate_task_duration_invalid_dates(self, projects_entity):
        """Test task duration calculation with invalid dates."""
        duration = projects_entity._calculate_task_duration("invalid", "dates")
        assert duration == 0
    
    def test_parse_dependencies(self, projects_entity):
        """Test parsing dependencies from string."""
        predecessors = "1,2,3"
        dependencies = projects_entity._parse_dependencies(predecessors)
        assert dependencies == [1, 2, 3]
        
        # Test with spaces and invalid values
        predecessors = "1, 2, abc, 3"
        dependencies = projects_entity._parse_dependencies(predecessors)
        assert dependencies == [1, 2, 3]  # abc should be filtered out
    
    def test_parse_dependencies_empty(self, projects_entity):
        """Test parsing empty dependencies."""
        dependencies = projects_entity._parse_dependencies("")
        assert dependencies == []
        
        dependencies = projects_entity._parse_dependencies(None)
        assert dependencies == []
    
    def test_has_circular_dependency(self, projects_entity):
        """Test circular dependency detection."""
        projects_entity.client.query = Mock(return_value=[{
            "predecessors": "1"  # Task 2 depends on task 1
        }])
        
        # Adding dependency from task 1 to task 2 would create circular reference
        # (task 1 -> task 2, but task 2 already depends on task 1)
        has_circular = projects_entity._has_circular_dependency(1, 2)
        assert has_circular == True
        
        # No circular dependency
        projects_entity.client.query = Mock(return_value=[{
            "predecessors": "3"  # Task 2 depends on task 3 (not on task 1)
        }])
        
        has_circular = projects_entity._has_circular_dependency(1, 2)
        assert has_circular == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])