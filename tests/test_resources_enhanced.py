"""
Comprehensive tests for the enhanced Resources entity functionality.

This test suite covers all the advanced PSA features including capacity planning,
skill tracking, utilization reporting, and performance metrics.
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from py_autotask.entities.resources import ResourcesEntity
from py_autotask.types import QueryFilter


class TestResourcesEntityEnhanced:
    """Test suite for enhanced Resources entity functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.resources_entity = ResourcesEntity(self.mock_client)

        # Mock resource data
        self.sample_resource = {
            "id": 123,
            "FirstName": "John",
            "LastName": "Doe",
            "DepartmentID": 10,
            "LocationID": 5,
            "Title": "Senior Developer",
            "HourlyRate": 100.0,
            "HourlyCost": 75.0,
            "ResourceType": 1,
            "IsActive": True,
        }

        # Mock utilization data
        self.sample_utilization = {
            "summary": {
                "utilization_percentage": 85.0,
                "billable_utilization_percentage": 75.0,
                "capacity_hours": 160.0,
                "total_hours": 136.0,
                "billable_hours": 120.0,
                "non_billable_hours": 16.0,
            },
            "efficiency_metrics": {
                "average_hours_per_day": 8.5,
            },
        }

        # Mock profitability data
        self.sample_profitability = {
            "total_revenue": 12000.0,
            "total_cost": 10200.0,
            "gross_profit": 1800.0,
            "gross_margin_percentage": 15.0,
            "average_hourly_rate": 100.0,
        }

        # Mock skills data
        self.sample_skills = [
            {
                "SkillName": "Python",
                "SkillLevel": 4,
                "Verified": True,
                "DateAcquired": "2023-01-01",
                "Notes": "Expert level programming",
            },
            {
                "SkillName": "JavaScript",
                "SkillLevel": 3,
                "Verified": True,
                "DateAcquired": "2023-02-01",
                "Notes": "Frontend development",
            },
        ]

    # =====================================================================================
    # CAPACITY PLANNING TESTS
    # =====================================================================================

    def test_forecast_resource_capacity_basic(self):
        """Test basic capacity forecasting functionality."""
        # Mock dependencies
        self.mock_client.get.return_value = self.sample_resource

        with patch.object(
            self.resources_entity, "get_resource_utilization"
        ) as mock_util, patch.object(
            self.resources_entity, "get_resource_time_off"
        ) as mock_time_off:

            mock_util.return_value = self.sample_utilization
            mock_time_off.return_value = []

            result = self.resources_entity.forecast_resource_capacity(
                resource_id=123, forecast_weeks=4
            )

            # Verify structure
            assert "resource_id" in result
            assert "forecast_data" in result
            assert "summary" in result
            assert len(result["forecast_data"]) == 4

            # Verify forecast data structure
            forecast_week = result["forecast_data"][0]
            assert "week" in forecast_week
            assert "forecast_capacity_hours" in forecast_week
            assert "forecast_available_hours" in forecast_week
            assert "utilization_forecast_percentage" in forecast_week

    def test_forecast_resource_capacity_with_trends(self):
        """Test capacity forecasting with historical trends."""
        self.mock_client.get.return_value = self.sample_resource

        with patch.object(
            self.resources_entity, "get_resource_utilization"
        ) as mock_util, patch.object(
            self.resources_entity, "get_resource_time_off"
        ) as mock_time_off:

            mock_util.return_value = self.sample_utilization
            mock_time_off.return_value = []

            result = self.resources_entity.forecast_resource_capacity(
                resource_id=123, forecast_weeks=4, include_historical_trends=True
            )

            assert "historical_utilization" in result
            assert len(result["historical_utilization"]) > 0

    def test_optimize_workload_distribution(self):
        """Test workload optimization algorithm."""
        resource_ids = [123, 124, 125]
        project_requirements = [
            {
                "project_id": 1001,
                "hours": 40,
                "skills": ["Python", "JavaScript"],
                "priority": "high",
            },
            {
                "project_id": 1002,
                "hours": 80,
                "skills": ["Python"],
                "priority": "medium",
            },
        ]

        # Mock resource data for optimization
        mock_resources = [
            {"id": 123, "HourlyRate": 100, "HourlyCost": 75},
            {"id": 124, "HourlyRate": 90, "HourlyCost": 70},
            {"id": 125, "HourlyRate": 110, "HourlyCost": 80},
        ]

        mock_availability = {"available_hours": 40}

        with patch.object(self.resources_entity, "get") as mock_get, patch.object(
            self.resources_entity, "get_resource_skills"
        ) as mock_skills, patch.object(
            self.resources_entity, "get_resource_availability"
        ) as mock_avail:

            mock_get.side_effect = lambda rid: next(
                (r for r in mock_resources if r["id"] == rid), None
            )
            mock_skills.return_value = self.sample_skills
            mock_avail.return_value = mock_availability

            result = self.resources_entity.optimize_workload_distribution(
                resource_ids=resource_ids,
                project_requirements=project_requirements,
                optimization_criteria="balanced",
            )

            # Verify optimization results
            assert "allocations" in result
            assert "summary" in result
            assert "resource_utilization_impact" in result
            assert result["total_resources_considered"] == 3
            assert result["total_requirements_processed"] == 2

            # Check that allocations were made
            assert len(result["allocations"]) > 0
            allocation = result["allocations"][0]
            assert "project_id" in allocation
            assert "allocated_hours" in allocation
            assert "allocations" in allocation

    def test_generate_capacity_recommendations(self):
        """Test capacity recommendations generation."""
        mock_resources = [self.sample_resource]

        with patch.object(
            self.resources_entity, "get_active_resources"
        ) as mock_active, patch.object(
            self.resources_entity, "get_resource_utilization"
        ) as mock_util, patch.object(
            self.resources_entity, "forecast_resource_capacity"
        ) as mock_forecast, patch.object(
            self.resources_entity, "get_resource_skills"
        ) as mock_skills:

            mock_active.return_value = mock_resources
            mock_util.return_value = self.sample_utilization
            mock_forecast.return_value = {
                "summary": {"average_weekly_availability": 35.0}
            }
            mock_skills.return_value = self.sample_skills

            result = self.resources_entity.generate_capacity_recommendations(
                department_id=10, utilization_threshold=80.0
            )

            # Verify recommendation structure
            assert "analysis_date" in result
            assert "resource_analysis" in result
            assert "hiring_recommendations" in result
            assert "training_recommendations" in result
            assert "summary" in result

    # =====================================================================================
    # SKILL TRACKING TESTS
    # =====================================================================================

    def test_create_skill_matrix_basic(self):
        """Test skill matrix creation."""
        resource_ids = [123, 124]

        with patch.object(self.resources_entity, "get") as mock_get, patch.object(
            self.resources_entity, "get_resource_skills"
        ) as mock_skills, patch.object(
            self.resources_entity, "get_resource_certifications"
        ) as mock_certs:

            mock_get.return_value = self.sample_resource
            mock_skills.return_value = self.sample_skills
            mock_certs.return_value = []

            result = self.resources_entity.create_skill_matrix(
                resource_ids=resource_ids,
                include_certifications=True,
                include_proficiency_gaps=True,
            )

            # Verify matrix structure
            assert "matrix_data" in result
            assert "skill_distribution" in result
            assert "competency_gaps" in result
            assert "recommendations" in result
            assert "all_skills" in result

            # Check skill distribution
            assert len(result["all_skills"]) > 0
            assert "Python" in result["skill_distribution"]

            skill_dist = result["skill_distribution"]["Python"]
            assert "total_resources_with_skill" in skill_dist
            assert "average_level" in skill_dist
            assert "level_distribution" in skill_dist

    def test_analyze_skill_gaps(self):
        """Test skill gap analysis."""
        target_skills = ["Python", "JavaScript", "React", "Docker"]
        target_levels = {"Python": 4, "JavaScript": 3, "React": 3, "Docker": 2}

        mock_resources = [self.sample_resource]

        with patch.object(
            self.resources_entity, "get_active_resources"
        ) as mock_active, patch.object(
            self.resources_entity, "get_resource_skills"
        ) as mock_skills:

            mock_active.return_value = mock_resources
            mock_skills.return_value = self.sample_skills

            result = self.resources_entity.analyze_skill_gaps(
                target_skills=target_skills,
                target_levels=target_levels,
                department_id=10,
            )

            # Verify gap analysis structure
            assert "skill_gaps" in result
            assert "training_priorities" in result
            assert "summary" in result

            # Check summary metrics
            summary = result["summary"]
            assert "total_skill_gaps" in summary
            assert "resources_meeting_all_requirements" in summary
            assert "average_skill_coverage" in summary

    def test_generate_training_plan(self):
        """Test training plan generation."""
        target_skills = ["Python", "Docker", "Kubernetes"]
        skill_priorities = {"Python": "high", "Docker": "medium", "Kubernetes": "low"}

        with patch.object(self.resources_entity, "get") as mock_get, patch.object(
            self.resources_entity, "get_resource_skills"
        ) as mock_skills, patch.object(
            self.resources_entity, "get_resource_certifications"
        ) as mock_certs:

            mock_get.return_value = self.sample_resource
            mock_skills.return_value = self.sample_skills
            mock_certs.return_value = []

            result = self.resources_entity.generate_training_plan(
                resource_id=123,
                target_skills=target_skills,
                skill_priorities=skill_priorities,
                timeline_weeks=12,
            )

            # Verify training plan structure
            assert "training_objectives" in result
            assert "learning_path" in result
            assert "milestones" in result
            assert "success_metrics" in result

            # Check training objectives
            assert len(result["training_objectives"]) > 0
            objective = result["training_objectives"][0]
            assert "skill" in objective
            assert "current_level" in objective
            assert "target_level" in objective
            assert "learning_activities" in objective

    def test_track_competency_assessments(self):
        """Test competency assessment tracking."""
        skill_assessments = [
            {
                "skill": "Python",
                "score": 85,
                "max_score": 100,
                "assessor": "John Smith",
                "notes": "Strong programming skills",
                "category": "Technical",
            },
            {
                "skill": "Communication",
                "score": 78,
                "max_score": 100,
                "assessor": "Jane Doe",
                "notes": "Good presentation skills",
                "category": "Soft Skills",
            },
        ]

        with patch.object(self.resources_entity, "get") as mock_get:
            mock_get.return_value = self.sample_resource

            result = self.resources_entity.track_competency_assessments(
                resource_id=123, skill_assessments=skill_assessments
            )

            # Verify assessment record structure
            assert "assessments" in result
            assert "overall_performance" in result
            assert "improvement_areas" in result
            assert "strengths" in result
            assert "next_assessment_date" in result

            # Check performance calculation
            overall_perf = result["overall_performance"]
            assert "average_score" in overall_perf
            assert "performance_level" in overall_perf
            assert "category_breakdown" in overall_perf

    # =====================================================================================
    # UTILIZATION REPORTING TESTS
    # =====================================================================================

    def test_generate_utilization_dashboard(self):
        """Test utilization dashboard generation."""
        resource_ids = [123, 124]

        mock_time_entries = [
            {
                "HoursWorked": 8,
                "HourlyRate": 100,
                "HourlyCost": 75,
                "BillableToAccount": True,
                "ProjectID": 1001,
            }
        ]

        with patch.object(self.resources_entity, "get") as mock_get, patch.object(
            self.resources_entity, "get_resource_utilization"
        ) as mock_util, patch.object(
            self.resources_entity, "get_resource_time_entries"
        ) as mock_entries:

            mock_get.return_value = self.sample_resource
            mock_util.return_value = self.sample_utilization
            mock_entries.return_value = mock_time_entries

            result = self.resources_entity.generate_utilization_dashboard(
                resource_ids=resource_ids, include_trends=True
            )

            # Verify dashboard structure
            assert "summary_metrics" in result
            assert "resource_details" in result
            assert "department_breakdown" in result
            assert "utilization_distribution" in result
            assert "recommendations" in result

            # Check summary metrics
            summary = result["summary_metrics"]
            assert "total_capacity_hours" in summary
            assert "overall_utilization_rate" in summary
            assert "billable_utilization_rate" in summary
            assert "total_revenue" in summary
            assert "profit_margin" in summary

    def test_generate_performance_scorecard(self):
        """Test performance scorecard generation."""
        with patch.object(self.resources_entity, "get") as mock_get, patch.object(
            self.resources_entity, "get_resource_utilization"
        ) as mock_util, patch.object(
            self.resources_entity, "get_resource_profitability"
        ) as mock_profit, patch.object(
            self.resources_entity, "get_resource_skills"
        ) as mock_skills, patch.object(
            self.resources_entity, "get_resource_certifications"
        ) as mock_certs, patch.object(
            self.resources_entity, "get_resource_time_entries"
        ) as mock_entries:

            mock_get.return_value = self.sample_resource
            mock_util.return_value = self.sample_utilization
            mock_profit.return_value = self.sample_profitability
            mock_skills.return_value = self.sample_skills
            mock_certs.return_value = []
            mock_entries.return_value = []

            result = self.resources_entity.generate_performance_scorecard(
                resource_id=123,
                evaluation_period_months=6,
                include_peer_comparison=False,
            )

            # Verify scorecard structure
            assert "overall_score" in result
            assert "performance_metrics" in result
            assert "skill_assessment" in result
            assert "utilization_analysis" in result
            assert "financial_impact" in result
            assert "strengths" in result
            assert "improvement_areas" in result

            # Check performance metrics
            metrics = result["performance_metrics"]
            assert "utilization_score" in metrics
            assert "billability_score" in metrics
            assert "profitability_score" in metrics
            assert "skill_development_score" in metrics

    def test_analyze_resource_efficiency_trends(self):
        """Test resource efficiency trend analysis."""
        resource_ids = [123, 124]

        with patch.object(
            self.resources_entity, "get_resource_utilization"
        ) as mock_util, patch.object(
            self.resources_entity, "get_resource_profitability"
        ) as mock_profit:

            mock_util.return_value = self.sample_utilization
            mock_profit.return_value = self.sample_profitability

            result = self.resources_entity.analyze_resource_efficiency_trends(
                resource_ids=resource_ids, analysis_months=6
            )

            # Verify trend analysis structure
            assert "monthly_data" in result
            assert "summary_trends" in result
            assert "insights" in result
            assert "analysis_period_months" in result

            # Check if trends are calculated
            if result["summary_trends"]:
                trend = list(result["summary_trends"].values())[0]
                assert "trend_direction" in trend
                assert "trend_magnitude" in trend
                assert "start_value" in trend
                assert "end_value" in trend

    # =====================================================================================
    # HELPER METHODS TESTS
    # =====================================================================================

    def test_get_skill_level_name(self):
        """Test skill level name conversion."""
        assert self.resources_entity._get_skill_level_name(1) == "Beginner"
        assert self.resources_entity._get_skill_level_name(3) == "Advanced"
        assert self.resources_entity._get_skill_level_name(5) == "Master"
        assert self.resources_entity._get_skill_level_name(99) == "Unknown"

    def test_determine_performance_level(self):
        """Test performance level determination."""
        assert self.resources_entity._determine_performance_level(95) == "Exceptional"
        assert self.resources_entity._determine_performance_level(85) == "Proficient"
        assert self.resources_entity._determine_performance_level(75) == "Developing"
        assert (
            self.resources_entity._determine_performance_level(65)
            == "Needs Improvement"
        )
        assert (
            self.resources_entity._determine_performance_level(55)
            == "Below Expectations"
        )

    def test_calculate_percentile(self):
        """Test percentile calculation."""
        peer_values = [60, 70, 80, 90]
        assert (
            self.resources_entity._calculate_percentile(75, peer_values) == 60.0
        )  # 3rd out of 5
        assert (
            self.resources_entity._calculate_percentile(95, peer_values) == 100.0
        )  # Top
        assert (
            self.resources_entity._calculate_percentile(50, peer_values) == 20.0
        )  # Bottom

    def test_is_certification_expiring_soon(self):
        """Test certification expiration checking."""
        future_date = (datetime.now() + timedelta(days=60)).isoformat()
        far_future_date = (datetime.now() + timedelta(days=180)).isoformat()

        cert_expiring = {"ExpirationDate": future_date}
        cert_valid = {"ExpirationDate": far_future_date}
        cert_no_date = {}

        assert (
            self.resources_entity._is_certification_expiring_soon(cert_expiring) is True
        )
        assert (
            self.resources_entity._is_certification_expiring_soon(cert_valid) is False
        )
        assert (
            self.resources_entity._is_certification_expiring_soon(cert_no_date) is False
        )

    # =====================================================================================
    # INTEGRATION TESTS
    # =====================================================================================

    def test_capacity_planning_workflow(self):
        """Test complete capacity planning workflow."""
        # This test simulates a complete capacity planning scenario
        resource_ids = [123, 124, 125]
        project_requirements = [
            {
                "project_id": 1001,
                "hours": 120,
                "skills": ["Python", "React"],
                "priority": "high",
            }
        ]

        # Mock all dependencies
        mock_resources = [
            {
                "id": 123,
                "FirstName": "John",
                "LastName": "Doe",
                "HourlyRate": 100,
                "HourlyCost": 75,
            },
            {
                "id": 124,
                "FirstName": "Jane",
                "LastName": "Smith",
                "HourlyRate": 90,
                "HourlyCost": 70,
            },
            {
                "id": 125,
                "FirstName": "Bob",
                "LastName": "Johnson",
                "HourlyRate": 110,
                "HourlyCost": 80,
            },
        ]

        with patch.object(self.resources_entity, "get") as mock_get, patch.object(
            self.resources_entity, "get_resource_skills"
        ) as mock_skills, patch.object(
            self.resources_entity, "get_resource_availability"
        ) as mock_avail, patch.object(
            self.resources_entity, "get_resource_utilization"
        ) as mock_util, patch.object(
            self.resources_entity, "get_resource_time_off"
        ) as mock_time_off, patch.object(
            self.resources_entity, "get_active_resources"
        ) as mock_active:

            mock_get.side_effect = lambda rid: next(
                (r for r in mock_resources if r["id"] == rid), None
            )
            mock_skills.return_value = self.sample_skills
            mock_avail.return_value = {"available_hours": 40}
            mock_util.return_value = self.sample_utilization
            mock_time_off.return_value = []
            mock_active.return_value = mock_resources

            # 1. Generate capacity forecast
            forecast = self.resources_entity.forecast_resource_capacity(
                123, forecast_weeks=12
            )
            assert forecast["resource_id"] == 123

            # 2. Optimize workload distribution
            optimization = self.resources_entity.optimize_workload_distribution(
                resource_ids=resource_ids, project_requirements=project_requirements
            )
            assert len(optimization["allocations"]) > 0

            # 3. Generate capacity recommendations
            recommendations = self.resources_entity.generate_capacity_recommendations()
            assert "resource_analysis" in recommendations

    def test_skill_development_workflow(self):
        """Test complete skill development workflow."""
        # Simulate a skill development scenario
        with patch.object(self.resources_entity, "get") as mock_get, patch.object(
            self.resources_entity, "get_resource_skills"
        ) as mock_skills, patch.object(
            self.resources_entity, "get_resource_certifications"
        ) as mock_certs:

            mock_get.return_value = self.sample_resource
            mock_skills.return_value = self.sample_skills
            mock_certs.return_value = []

            # 1. Create skill matrix
            matrix = self.resources_entity.create_skill_matrix([123])
            assert 123 in matrix["matrix_data"]

            # 2. Analyze skill gaps
            gaps = self.resources_entity.analyze_skill_gaps(
                target_skills=["Python", "Docker", "Kubernetes"]
            )
            assert "skill_gaps" in gaps

            # 3. Generate training plan
            training_plan = self.resources_entity.generate_training_plan(
                resource_id=123, target_skills=["Docker", "Kubernetes"]
            )
            assert len(training_plan["training_objectives"]) > 0

            # 4. Track assessments
            assessments = [
                {
                    "skill": "Python",
                    "score": 90,
                    "max_score": 100,
                    "assessor": "Manager",
                }
            ]
            assessment_record = self.resources_entity.track_competency_assessments(
                resource_id=123, skill_assessments=assessments
            )
            assert len(assessment_record["assessments"]) == 1

    # =====================================================================================
    # ERROR HANDLING TESTS
    # =====================================================================================

    def test_forecast_capacity_invalid_resource(self):
        """Test capacity forecasting with invalid resource ID."""
        self.mock_client.get.return_value = None

        with pytest.raises(ValueError, match="Resource 999 not found"):
            self.resources_entity.forecast_resource_capacity(999)

    def test_generate_training_plan_invalid_resource(self):
        """Test training plan generation with invalid resource ID."""
        self.mock_client.get.return_value = None

        with pytest.raises(ValueError, match="Resource 999 not found"):
            self.resources_entity.generate_training_plan(999)

    def test_generate_performance_scorecard_invalid_resource(self):
        """Test performance scorecard with invalid resource ID."""
        self.mock_client.get.return_value = None

        with pytest.raises(ValueError, match="Resource 999 not found"):
            self.resources_entity.generate_performance_scorecard(999)

    def test_track_competency_assessments_invalid_resource(self):
        """Test competency assessment tracking with invalid resource ID."""
        self.mock_client.get.return_value = None

        with pytest.raises(ValueError, match="Resource 999 not found"):
            self.resources_entity.track_competency_assessments(999, [])

    # =====================================================================================
    # EDGE CASES
    # =====================================================================================

    def test_empty_skill_matrix(self):
        """Test skill matrix creation with no resources."""
        result = self.resources_entity.create_skill_matrix(resource_ids=[])
        assert result["resources_analyzed"] == 0
        assert len(result["matrix_data"]) == 0

    def test_optimization_no_suitable_resources(self):
        """Test workload optimization when no resources match requirements."""
        project_requirements = [
            {"project_id": 1001, "hours": 40, "skills": ["SuperRareSkill"]}
        ]

        with patch.object(self.resources_entity, "get") as mock_get, patch.object(
            self.resources_entity, "get_resource_skills"
        ) as mock_skills, patch.object(
            self.resources_entity, "get_resource_availability"
        ) as mock_avail:

            mock_get.return_value = self.sample_resource
            mock_skills.return_value = []  # No skills
            mock_avail.return_value = {"available_hours": 40}

            result = self.resources_entity.optimize_workload_distribution(
                resource_ids=[123], project_requirements=project_requirements
            )

            # Should have unallocated requirements
            assert len(result["unallocated_requirements"]) == 1

    def test_utilization_dashboard_no_data(self):
        """Test utilization dashboard with no data."""
        with patch.object(self.resources_entity, "get") as mock_get, patch.object(
            self.resources_entity, "get_resource_utilization"
        ) as mock_util, patch.object(
            self.resources_entity, "get_resource_time_entries"
        ) as mock_entries:

            mock_get.return_value = None  # No resource found

            result = self.resources_entity.generate_utilization_dashboard(
                resource_ids=[999]  # Non-existent resource
            )

            # Should return empty dashboard
            assert result["resources_analyzed"] == 1
            assert len(result["resource_details"]) == 0
