#!/usr/bin/env python3
"""
Comprehensive tests for enhanced Projects entity functionality.

Tests cover:
- Enhanced milestone management
- Gantt chart data generation  
- Project template management
- Critical path calculation
- Resource allocation analysis
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, MagicMock, patch

# Import the enhanced projects entity
from py_autotask.entities.projects import Projects


class TestEnhancedMilestoneManagement:
    """Test enhanced milestone management functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_entity = Mock()
        self.projects = Projects(self.mock_entity)
        
    def test_create_milestone_basic(self):
        """Test creating a basic milestone."""
        # Mock entity create response
        self.mock_entity.create.return_value = {
            "id": 123,
            "ProjectID": 1,
            "Title": "Test Milestone",
            "TargetDate": "2024-12-31",
            "Status": "Planned"
        }
        
        # Create milestone
        result = self.projects.create_milestone(
            project_id=1,
            title="Test Milestone",
            target_date="2024-12-31",
            description="A test milestone"
        )
        
        # Verify creation
        assert result["id"] == 123
        assert result["ProjectID"] == 1
        assert result["Title"] == "Test Milestone"
        
        # Verify create was called with correct data
        create_call = self.mock_entity.create.call_args[0][0]
        assert create_call["ProjectID"] == 1
        assert create_call["Title"] == "Test Milestone"
        assert create_call["TargetDate"] == "2024-12-31"
        assert create_call["Status"] == "Planned"
        assert create_call["IsActive"] is True
        
    def test_create_milestone_with_deliverables(self):
        """Test creating milestone with deliverables."""
        self.mock_entity.create.return_value = {"id": 124}
        
        deliverables = ["Design Document", "Prototype", "Test Results"]
        
        self.projects.create_milestone(
            project_id=1,
            title="Design Review",
            target_date="2024-06-15",
            deliverables=deliverables
        )
        
        create_call = self.mock_entity.create.call_args[0][0]
        assert create_call["Deliverables"] == "Design Document,Prototype,Test Results"
        
    def test_update_milestone_completion(self):
        """Test updating milestone to completed status."""
        # Mock existing milestone
        existing_milestone = {
            "id": 123,
            "ProjectID": 1,
            "Title": "Test Milestone",
            "Status": "In Progress"
        }
        self.mock_entity.get_by_id.return_value = existing_milestone
        self.mock_entity.update.return_value = {**existing_milestone, "Status": "Completed"}
        
        # Mock add_project_note method
        self.projects.add_project_note = Mock()
        
        # Update milestone to completed
        result = self.projects.update_milestone(
            milestone_id=123,
            updates={"Status": "Completed"},
            completion_notes="Successfully delivered all components"
        )
        
        # Verify update call
        update_call = self.mock_entity.update.call_args
        milestone_id = update_call[0][0]
        update_data = update_call[0][1]
        
        assert milestone_id == 123
        assert update_data["Status"] == "Completed"
        assert update_data["CompletionPercentage"] == 100
        assert update_data["CompletionNotes"] == "Successfully delivered all components"
        assert "CompletionDate" in update_data
        assert "LastModifiedDate" in update_data
        
    def test_get_milestone_progress_summary(self):
        """Test getting milestone progress summary."""
        # Mock milestones data
        mock_milestones = [
            {
                "id": 1,
                "Title": "Design Complete",
                "Status": "Completed",
                "TargetDate": "2024-01-15",
                "Priority": "High"
            },
            {
                "id": 2,
                "Title": "Development Phase 1",
                "Status": "In Progress",
                "TargetDate": "2024-02-01",
                "Priority": "Medium"
            },
            {
                "id": 3,
                "Title": "Testing Complete",
                "Status": "Planned",
                "TargetDate": "2024-01-01",  # Overdue
                "Priority": "Critical"
            }
        ]
        
        # Mock the get_project_milestones method
        self.projects.get_project_milestones = Mock(return_value=mock_milestones)
        
        # Get progress summary
        progress = self.projects.get_milestone_progress(project_id=1)
        
        # Verify summary calculations
        assert progress["project_id"] == 1
        assert progress["total_milestones"] == 3
        assert progress["completed"] == 1
        assert progress["in_progress"] == 1
        assert progress["planned"] == 1
        assert progress["overdue"] == 1
        assert progress["completion_percentage"] == 33.333333333333336
        
        # Verify critical milestones
        assert len(progress["critical_milestones"]) == 2  # High and Critical
        
        # Verify overdue milestones
        assert len(progress["overdue_milestones"]) == 1
        assert progress["overdue_milestones"][0]["id"] == 3
        
        # Verify next milestone
        assert progress["next_milestone"]["id"] == 2
        
    def test_delete_milestone_soft_delete(self):
        """Test soft delete of milestone."""
        # Mock existing milestone
        existing_milestone = {
            "id": 123,
            "ProjectID": 1,
            "Title": "Test Milestone"
        }
        self.mock_entity.get_by_id.return_value = existing_milestone
        self.projects.add_project_note = Mock()
        
        # Delete milestone
        result = self.projects.delete_milestone(123)
        
        # Verify soft delete
        assert result is True
        
        update_call = self.mock_entity.update.call_args[0]
        milestone_id = update_call[0]
        update_data = update_call[1]
        
        assert milestone_id == 123
        assert update_data["IsActive"] is False
        assert update_data["Status"] == "Cancelled"
        assert "LastModifiedDate" in update_data


class TestGanttChartDataGeneration:
    """Test Gantt chart data generation functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_entity = Mock()
        self.projects = Projects(self.mock_entity)
        
        # Mock project details
        self.mock_project = {
            "id": 1,
            "ProjectName": "Test Project",
            "StartDateTime": "2024-01-01T00:00:00Z",
            "EndDateTime": "2024-03-31T23:59:59Z",
            "Status": "In Progress",
            "PercentComplete": 45
        }
        
        # Mock tasks
        self.mock_tasks = [
            {
                "id": 101,
                "Title": "Design Phase",
                "StartDateTime": "2024-01-01T00:00:00Z",
                "EndDateTime": "2024-01-15T23:59:59Z",
                "PercentComplete": 100,
                "Status": "Complete",
                "Priority": "High",
                "EstimatedHours": 120,
                "AssignedResourceID": "user1"
            },
            {
                "id": 102,
                "Title": "Development Phase",
                "StartDateTime": "2024-01-16T00:00:00Z",
                "EndDateTime": "2024-03-15T23:59:59Z",
                "PercentComplete": 60,
                "Status": "In Progress",
                "Priority": "High",
                "EstimatedHours": 320,
                "AssignedResourceID": "user2"
            }
        ]
        
        # Mock milestones
        self.mock_milestones = [
            {
                "id": 201,
                "Title": "Design Review",
                "TargetDate": "2024-01-20T00:00:00Z",
                "Status": "Completed",
                "Priority": "High",
                "MilestoneType": "Review"
            }
        ]
        
    def test_get_gantt_chart_data_complete(self):
        """Test getting complete Gantt chart data."""
        # Set up mocks
        self.projects.get_project_details = Mock(return_value=self.mock_project)
        self.projects.get_project_tasks = Mock(return_value=self.mock_tasks)
        self.projects.get_project_milestones = Mock(return_value=self.mock_milestones)
        
        # Get Gantt chart data
        gantt_data = self.projects.get_gantt_chart_data(
            project_id=1,
            include_tasks=True,
            include_milestones=True,
            include_dependencies=True
        )
        
        # Verify project data
        assert gantt_data["project"]["id"] == 1
        assert gantt_data["project"]["name"] == "Test Project"
        assert gantt_data["project"]["completion_percentage"] == 45
        
        # Verify tasks formatting
        assert len(gantt_data["tasks"]) == 2
        task1 = gantt_data["tasks"][0]
        assert task1["id"] == 101
        assert task1["title"] == "Design Phase"
        assert task1["completion_percentage"] == 100
        assert task1["duration"] > 0  # Should calculate hours between dates
        assert task1["is_critical"] is False  # Will be set by critical path calculation
        
        # Verify milestones formatting
        assert len(gantt_data["milestones"]) == 1
        milestone1 = gantt_data["milestones"][0]
        assert milestone1["id"] == 201
        assert milestone1["title"] == "Design Review"
        assert milestone1["is_critical"] is True  # High priority
        
        # Verify timeline calculation
        timeline = gantt_data["timeline"]
        assert timeline["earliest_start"] is not None
        assert timeline["latest_end"] is not None
        assert timeline["duration_days"] > 0
        
        # Verify resource allocation
        assert "by_resource" in gantt_data["resource_allocation"]
        assert "total_allocated_hours" in gantt_data["resource_allocation"]
        
    def test_calculate_duration_hours(self):
        """Test duration calculation between dates."""
        start_date = "2024-01-01T00:00:00Z"
        end_date = "2024-01-02T00:00:00Z"
        
        duration = self.projects._calculate_duration_hours(start_date, end_date)
        assert duration == 24.0  # 24 hours in a day
        
        # Test invalid dates
        duration_invalid = self.projects._calculate_duration_hours("", "")
        assert duration_invalid == 0.0
        
    def test_critical_path_calculation_basic(self):
        """Test basic critical path calculation."""
        # Create test Gantt data with tasks
        gantt_data = {
            "project": {"start_date": "2024-01-01T00:00:00Z", "end_date": "2024-01-31T23:59:59Z"},
            "tasks": [
                {
                    "id": 1,
                    "title": "Task A",
                    "duration": 40,  # 40 hours = 5 days
                    "early_start": None,
                    "early_finish": None,
                    "late_start": None,
                    "late_finish": None,
                    "slack": 0,
                    "is_critical": False
                },
                {
                    "id": 2,
                    "title": "Task B", 
                    "duration": 32,  # 32 hours = 4 days
                    "early_start": None,
                    "early_finish": None,
                    "late_start": None,
                    "late_finish": None,
                    "slack": 0,
                    "is_critical": False
                }
            ]
        }
        
        dependencies = []  # No dependencies for simple test
        
        critical_path = self.projects._calculate_critical_path(gantt_data)
        
        # Should return tasks (exact logic depends on implementation)
        assert isinstance(critical_path, list)
        
        # Verify that early/late start/finish are calculated
        for task in gantt_data["tasks"]:
            assert task.get("early_start") is not None
            assert task.get("early_finish") is not None
            
    def test_resource_allocation_calculation(self):
        """Test resource allocation calculation."""
        # Mock project tasks
        self.projects.get_project_tasks = Mock(return_value=[
            {
                "id": 1,
                "Title": "Task 1",
                "AssignedResourceID": "user1",
                "AssignedResourceName": "John Doe",
                "EstimatedHours": 40,
                "DepartmentID": "dev"
            },
            {
                "id": 2,
                "Title": "Task 2", 
                "AssignedResourceID": "user1",
                "AssignedResourceName": "John Doe",
                "EstimatedHours": 20,
                "DepartmentID": "dev"
            },
            {
                "id": 3,
                "Title": "Task 3",
                "AssignedResourceID": "user2",
                "AssignedResourceName": "Jane Smith",
                "EstimatedHours": 30,
                "DepartmentID": "qa"
            }
        ])
        
        allocation = self.projects._get_resource_allocation(project_id=1)
        
        # Verify by resource calculations
        assert "user1" in allocation["by_resource"]
        assert allocation["by_resource"]["user1"]["allocated_hours"] == 60  # 40 + 20
        assert len(allocation["by_resource"]["user1"]["tasks"]) == 2
        
        assert "user2" in allocation["by_resource"]
        assert allocation["by_resource"]["user2"]["allocated_hours"] == 30
        
        # Verify by department calculations
        assert "dev" in allocation["by_department"]
        assert allocation["by_department"]["dev"]["allocated_hours"] == 60
        assert allocation["by_department"]["dev"]["task_count"] == 2
        
        assert "qa" in allocation["by_department"]
        assert allocation["by_department"]["qa"]["allocated_hours"] == 30
        assert allocation["by_department"]["qa"]["task_count"] == 1
        
        # Verify totals
        assert allocation["total_allocated_hours"] == 90
        assert allocation["utilization_percentage"] > 0


class TestProjectTemplateManagement:
    """Test project template management functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_entity = Mock()
        self.projects = Projects(self.mock_entity)
        
    def test_create_project_template_basic(self):
        """Test creating a basic project template."""
        template_data = {
            "description": "Standard web development project template",
            "template_type": "Web Development",
            "industry": "Technology",
            "default_duration_days": 60,
            "default_priority": "High",
            "billing_type": "Fixed Fee",
            "tasks": [
                {
                    "title": "Requirements Gathering",
                    "description": "Collect and document project requirements",
                    "estimated_hours": 40,
                    "priority": "High",
                    "phase": "Planning"
                },
                {
                    "title": "UI/UX Design", 
                    "description": "Create user interface designs",
                    "estimated_hours": 80,
                    "priority": "Medium",
                    "phase": "Design"
                }
            ],
            "milestones": [
                {
                    "title": "Requirements Approval",
                    "description": "Client approves all requirements",
                    "milestone_type": "Client Review",
                    "days_from_start": 10,
                    "deliverables": ["Requirements Document", "Approval Email"]
                }
            ]
        }
        
        # Mock template saving
        self.projects._save_project_template = Mock(return_value="template_12345")
        
        # Create template
        template = self.projects.create_project_template(
            template_name="Web Development Standard",
            template_data=template_data,
            include_tasks=True,
            include_milestones=True
        )
        
        # Verify template structure
        assert template["name"] == "Web Development Standard"
        assert template["template_type"] == "Web Development"
        assert template["industry"] == "Technology"
        assert template["is_active"] is True
        assert template["version"] == "1.0"
        
        # Verify project settings
        settings = template["project_settings"]
        assert settings["default_duration_days"] == 60
        assert settings["default_priority"] == "High"
        assert settings["billing_type"] == "Fixed Fee"
        
        # Verify tasks
        assert len(template["tasks"]) == 2
        task1 = template["tasks"][0]
        assert task1["title"] == "Requirements Gathering"
        assert task1["estimated_hours"] == 40
        assert task1["phase"] == "Planning"
        
        # Verify milestones
        assert len(template["milestones"]) == 1
        milestone1 = template["milestones"][0]
        assert milestone1["title"] == "Requirements Approval"
        assert milestone1["days_from_start"] == 10
        assert milestone1["deliverables"] == ["Requirements Document", "Approval Email"]
        
    def test_apply_project_template(self):
        """Test applying a template to create a new project."""
        # Mock template data
        template_data = {
            "name": "Test Template",
            "description": "A test template",
            "project_settings": {
                "default_duration_days": 30,
                "default_priority": "Medium",
                "default_status": "New",
                "billing_type": "Time and Materials"
            },
            "tasks": [
                {
                    "title": "Setup Task",
                    "estimated_hours": 8,
                    "priority": "High"
                }
            ],
            "milestones": [
                {
                    "title": "Project Kickoff",
                    "days_from_start": 1,
                    "priority": "High"
                }
            ]
        }
        
        # Mock template retrieval
        self.projects._get_project_template = Mock(return_value=template_data)
        
        # Mock project creation
        created_project = {"id": 456, "ProjectName": "New Test Project"}
        self.mock_entity.create.return_value = created_project
        
        # Mock milestone creation
        self.projects.create_milestone = Mock(return_value={"id": 789})
        
        # Apply template
        project_data = {
            "name": "New Test Project",
            "description": "Project created from template",
            "account_id": 123,
            "start_date": "2024-06-01T00:00:00Z"
        }
        
        result = self.projects.apply_project_template(
            template_id="template_12345",
            project_data=project_data
        )
        
        # Verify project creation
        create_call = self.mock_entity.create.call_args[0][0]
        assert create_call["ProjectName"] == "New Test Project"
        assert create_call["Type"] == "Time and Materials"
        assert create_call["Status"] == "New"
        assert create_call["Priority"] == "Medium"
        assert create_call["StartDateTime"] == "2024-06-01T00:00:00Z"
        assert create_call["EndDateTime"] is not None  # Should calculate end date
        
        # Verify result summary
        assert result["project"]["id"] == 456
        assert result["template_applied"] == "template_12345"
        assert result["tasks_created"] == 1
        assert result["milestones_created"] == 1
        
        # Verify milestone creation was called
        self.projects.create_milestone.assert_called_once()
        milestone_call = self.projects.create_milestone.call_args
        assert milestone_call[1]["title"] == "Project Kickoff"
        
    def test_get_project_templates_with_filters(self):
        """Test getting project templates with filters."""
        # Mock template list
        mock_templates = [
            {
                "id": "template_1",
                "name": "Web Development",
                "template_type": "Web Development",
                "industry": "Technology",
                "is_active": True
            },
            {
                "id": "template_2",
                "name": "Mobile App",
                "template_type": "Mobile Development", 
                "industry": "Technology",
                "is_active": True
            },
            {
                "id": "template_3",
                "name": "Marketing Campaign",
                "template_type": "Marketing",
                "industry": "Retail",
                "is_active": False  # Inactive
            }
        ]
        
        self.projects._list_project_templates = Mock(return_value=mock_templates)
        
        # Test no filters
        all_templates = self.projects.get_project_templates(active_only=False)
        assert len(all_templates) == 3
        
        # Test active only filter
        active_templates = self.projects.get_project_templates(active_only=True)
        assert len(active_templates) == 2
        
        # Test template type filter
        web_templates = self.projects.get_project_templates(
            template_type="Web Development",
            active_only=True
        )
        assert len(web_templates) == 1
        assert web_templates[0]["name"] == "Web Development"
        
        # Test industry filter
        tech_templates = self.projects.get_project_templates(
            industry="Technology",
            active_only=True
        )
        assert len(tech_templates) == 2
        
    def test_update_project_template_with_versioning(self):
        """Test updating a template with version increment."""
        # Mock existing template
        existing_template = {
            "id": "template_123",
            "name": "Old Name",
            "version": "1.5",
            "description": "Old description"
        }
        
        self.projects._get_project_template = Mock(return_value=existing_template)
        self.projects._save_project_template = Mock()
        
        # Update template
        updates = {
            "name": "New Name",
            "description": "Updated description"
        }
        
        updated_template = self.projects.update_project_template(
            template_id="template_123",
            updates=updates,
            increment_version=True
        )
        
        # Verify updates applied
        assert updated_template["name"] == "New Name"
        assert updated_template["description"] == "Updated description"
        assert updated_template["version"] == "1.6"  # Incremented
        assert "last_modified_date" in updated_template
        
        # Verify save was called
        self.projects._save_project_template.assert_called_once()
        
    def test_delete_project_template_soft_delete(self):
        """Test soft delete of project template."""
        # Mock existing template
        existing_template = {
            "id": "template_123",
            "name": "Template to Delete",
            "is_active": True
        }
        
        self.projects._get_project_template = Mock(return_value=existing_template)
        self.projects._save_project_template = Mock()
        
        # Delete template
        result = self.projects.delete_project_template("template_123")
        
        # Verify soft delete
        assert result is True
        
        # Verify save was called with updated template
        save_call = self.projects._save_project_template.call_args[0][0]
        assert save_call["is_active"] is False
        assert "deleted_date" in save_call


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple features."""
    
    def setup_method(self):
        """Set up test fixtures.""" 
        self.mock_entity = Mock()
        self.projects = Projects(self.mock_entity)
        
    def test_complete_project_workflow(self):
        """Test complete workflow from template to Gantt chart."""
        # 1. Create project from template
        template_data = {
            "name": "Standard Project",
            "project_settings": {"default_duration_days": 30},
            "tasks": [{"title": "Task 1", "estimated_hours": 40}],
            "milestones": [{"title": "Milestone 1", "days_from_start": 15}]
        }
        
        self.projects._get_project_template = Mock(return_value=template_data)
        self.mock_entity.create.return_value = {"id": 100}
        self.projects.create_milestone = Mock()
        
        # Apply template
        project_result = self.projects.apply_project_template(
            "template_1",
            {"name": "Test Project", "start_date": "2024-01-01T00:00:00Z"}
        )
        
        assert project_result["project"]["id"] == 100
        
        # 2. Add additional milestones
        self.mock_entity.create.return_value = {"id": 201}
        milestone = self.projects.create_milestone(
            project_id=100,
            title="Custom Milestone",
            target_date="2024-01-20T00:00:00Z"
        )
        
        assert milestone["id"] == 201
        
        # 3. Generate Gantt chart data
        mock_project = {"id": 100, "ProjectName": "Test Project"}
        mock_tasks = [{"id": 1, "Title": "Task 1", "EstimatedHours": 40}]
        mock_milestones = [{"id": 201, "Title": "Custom Milestone"}]
        
        self.projects.get_project_details = Mock(return_value=mock_project)
        self.projects.get_project_tasks = Mock(return_value=mock_tasks)
        self.projects.get_project_milestones = Mock(return_value=mock_milestones)
        
        gantt_data = self.projects.get_gantt_chart_data(project_id=100)
        
        # Verify complete workflow
        assert gantt_data["project"]["id"] == 100
        assert len(gantt_data["tasks"]) == 1
        assert len(gantt_data["milestones"]) == 1
        assert "resource_allocation" in gantt_data
        assert "timeline" in gantt_data


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])