#!/usr/bin/env python3
"""
py-autotask Data Liberation Example

This example demonstrates the power of the transformed py-autotask SDK,
showing how to completely own and control your Autotask data with advanced
analytics, bulk operations, and seamless data export capabilities.

Run this script to see py-autotask in action as the ultimate Python tool
for Autotask API mastery.
"""

import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path

# Import the enhanced py-autotask components
from py_autotask import AsyncAutotaskClient
from py_autotask.caching import CacheConfig
from py_autotask.bulk_manager import IntelligentBulkManager
from py_autotask.pandas_integration import PandasIntegration
from py_autotask.types import RequestConfig

# Rich console for beautiful output
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

console = Console()


async def main():
    """Demonstrate the full power of py-autotask data liberation."""

    console.print(
        Panel.fit(
            "[bold blue]🚀 py-autotask Data Liberation Demo[/bold blue]\n"
            "[green]The most powerful Python SDK for Autotask API[/green]",
            border_style="blue",
        )
    )

    # Configuration for maximum performance
    cache_config = CacheConfig(
        backend="redis",  # Use Redis for enterprise-grade caching
        redis_url="redis://localhost:6379",
        default_ttl=300,
        cache_patterns={
            "companies": 1800,  # 30 minutes
            "tickets": 60,  # 1 minute
            "time_entries": 3600,  # 1 hour
        },
    )

    request_config = RequestConfig(timeout=30, max_retries=5, retry_backoff=2.0)

    # Create the async client with all advanced features
    async with AsyncAutotaskClient.create(
        username=os.environ.get("AUTOTASK_USERNAME"),
        integration_code=os.environ.get("AUTOTASK_INTEGRATION_CODE"),
        secret=os.environ.get("AUTOTASK_SECRET"),
        config=request_config,
        # cache_config=cache_config  # Uncomment if Redis is available
    ) as client:

        await demo_basic_operations(client)
        await demo_concurrent_operations(client)
        await demo_bulk_operations(client)
        await demo_pandas_integration(client)
        await demo_advanced_analytics(client)
        await demo_data_export(client)

    console.print(
        "\n[bold green]🎉 Demo completed! py-autotask has liberated your data![/bold green]"
    )


async def demo_basic_operations(client):
    """Demonstrate basic operations with enhanced error handling."""
    console.print("\n[bold yellow]📋 Basic Operations Demo[/bold yellow]")

    try:
        # Get recent tickets with intelligent caching
        recent_tickets = await client.tickets.query_async(
            {
                "filters": [
                    {
                        "field": "createDate",
                        "op": "gte",
                        "value": "2024-01-01T00:00:00Z",
                    },
                    {"field": "status", "op": "ne", "value": "5"},  # Not completed
                ]
            }
        )

        console.print(
            f"✅ Found {len(recent_tickets.items)} active tickets (cached for performance)"
        )

        # Display sample data
        if recent_tickets.items:
            table = Table(title="Recent Tickets Sample")
            table.add_column("ID", style="cyan")
            table.add_column("Title", style="green")
            table.add_column("Priority", style="red")
            table.add_column("Status", style="blue")

            for ticket in recent_tickets.items[:5]:
                table.add_row(
                    str(ticket.get("id", "N/A")),
                    str(ticket.get("title", "N/A"))[:40],
                    str(ticket.get("priority", "N/A")),
                    str(ticket.get("status", "N/A")),
                )

            console.print(table)

    except Exception as e:
        console.print(f"[red]❌ Basic operations failed: {e}[/red]")


async def demo_concurrent_operations(client):
    """Demonstrate concurrent operations for maximum performance."""
    console.print("\n[bold yellow]⚡ Concurrent Operations Demo[/bold yellow]")

    try:
        start_time = datetime.now()

        # Execute multiple queries concurrently
        companies_task = client.companies.query_async(
            {"filters": [{"field": "isActive", "op": "eq", "value": "true"}]}
        )
        resources_task = client.resources.query_async({"max_records": 50})
        projects_task = client.projects.query_async({"max_records": 30})

        # Wait for all operations to complete
        companies, resources, projects = await asyncio.gather(
            companies_task, resources_task, projects_task
        )

        duration = datetime.now() - start_time

        console.print(
            f"✅ Concurrent operations completed in {duration.total_seconds():.2f}s"
        )
        console.print(f"   📊 Companies: {len(companies.items)}")
        console.print(f"   👥 Resources: {len(resources.items)}")
        console.print(f"   🎯 Projects: {len(projects.items)}")

    except Exception as e:
        console.print(f"[red]❌ Concurrent operations failed: {e}[/red]")


async def demo_bulk_operations(client):
    """Demonstrate intelligent bulk operations."""
    console.print("\n[bold yellow]🔄 Bulk Operations Demo[/bold yellow]")

    try:
        # Create bulk manager
        bulk_manager = IntelligentBulkManager(client)

        # Simulate bulk ticket creation (dry run)
        sample_tickets = [
            {
                "title": f"Demo Ticket {i}",
                "description": f"This is demo ticket number {i} created by py-autotask",
                "accountID": 12345,  # Replace with valid account ID
                "priority": (i % 4) + 1,
                "status": 1,
            }
            for i in range(1, 101)  # 100 sample tickets
        ]

        console.print("🚀 Starting bulk create simulation (dry run)...")

        # Progress callback for live updates
        def progress_callback(percentage):
            console.print(f"   Progress: {percentage:.1f}%", end="\r")

        result = await bulk_manager.bulk_create(
            entity="tickets",
            data=sample_tickets,
            batch_size="auto",  # Automatically optimized
            parallel=True,  # Intelligent parallelization
            validate=True,  # Data validation
            dry_run=True,  # Simulation only
            progress_callback=progress_callback,
        )

        console.print("\n✅ Bulk operation simulation completed!")
        console.print(f"   📊 Total Records: {result.total_records}")
        console.print(f"   ✅ Successful: {result.successful}")
        console.print(f"   ❌ Failed: {result.failed}")
        console.print(f"   ⏱️  Duration: {result.duration:.2f}s")
        console.print(f"   🚀 Throughput: {result.throughput:.1f} records/sec")

    except Exception as e:
        console.print(f"[red]❌ Bulk operations demo failed: {e}[/red]")


async def demo_pandas_integration(client):
    """Demonstrate seamless pandas integration."""
    console.print("\n[bold yellow]🐼 Pandas Integration Demo[/bold yellow]")

    try:
        # Create pandas integration
        pandas_integration = PandasIntegration(client)

        # Convert Autotask data to DataFrame
        console.print("📊 Converting Autotask data to pandas DataFrame...")

        df_tickets = await pandas_integration.to_dataframe(
            entity_type="tickets",
            filters=[
                {"field": "createDate", "op": "gte", "value": "2024-01-01T00:00:00Z"}
            ],
            max_records=100,
            include_relationships=["accountID:companies"],
        )

        if not df_tickets.empty:
            console.print(f"✅ Created DataFrame with {len(df_tickets)} records")

            # Perform data analysis
            console.print("\n📈 Performing ticket analytics...")
            analytics = df_tickets.ticket_analytics()

            # Display analytics
            analytics_table = Table(title="Ticket Analytics")
            analytics_table.add_column("Metric", style="cyan")
            analytics_table.add_column("Value", style="green")

            analytics_table.add_row(
                "Total Tickets", str(analytics.get("total_tickets", "N/A"))
            )
            analytics_table.add_row(
                "Priority Distribution",
                str(len(analytics.get("priority_distribution", {}))) + " categories",
            )
            analytics_table.add_row(
                "Status Distribution",
                str(len(analytics.get("status_distribution", {}))) + " statuses",
            )

            if "avg_resolution_time_hours" in analytics:
                analytics_table.add_row(
                    "Avg Resolution Time",
                    f"{analytics['avg_resolution_time_hours']:.1f} hours",
                )

            console.print(analytics_table)

            # Trend analysis
            trends = df_tickets.analyze_trends(period="W")  # Weekly trends
            if not trends.empty:
                console.print(f"📊 Trend analysis: {len(trends)} data points over time")

        else:
            console.print("[yellow]⚠️  No ticket data available for analysis[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Pandas integration demo failed: {e}[/red]")


async def demo_advanced_analytics(client):
    """Demonstrate advanced analytics capabilities."""
    console.print("\n[bold yellow]📊 Advanced Analytics Demo[/bold yellow]")

    try:
        # Generate comprehensive report
        pandas_integration = PandasIntegration(client)

        report = await pandas_integration.generate_report(
            entity_type="tickets",
            date_range=("2024-01-01", "2024-12-31"),
            report_type="detailed",
        )

        console.print("📋 Generated comprehensive analytics report:")
        console.print(f"   📅 Date Range: {report.get('date_range', 'N/A')}")
        console.print(f"   📊 Total Records: {report.get('total_records', 'N/A')}")
        console.print(f"   🕐 Generated At: {report.get('generated_at', 'N/A')}")

        if "analytics" in report:
            analytics = report["analytics"]
            console.print(f"   🎯 Analytics Available: {len(analytics)} metrics")

        if "trends" in report:
            trends = report["trends"]
            console.print(f"   📈 Trend Data Points: {len(trends) if trends else 0}")

    except Exception as e:
        console.print(f"[red]❌ Advanced analytics demo failed: {e}[/red]")


async def demo_data_export(client):
    """Demonstrate comprehensive data export capabilities."""
    console.print("\n[bold yellow]💾 Data Export Demo[/bold yellow]")

    try:
        # Create export directory
        export_dir = Path("autotask_exports")
        export_dir.mkdir(exist_ok=True)

        console.print("🔄 Exporting sample data to multiple formats...")

        # Export tickets to different formats
        pandas_integration = PandasIntegration(client)

        df_tickets = await pandas_integration.to_dataframe(
            entity_type="tickets",
            max_records=50,  # Limit for demo
            include_relationships=["accountID:companies"],
        )

        if not df_tickets.empty:
            # Export to CSV
            csv_file = export_dir / "tickets_export.csv"
            df_tickets.to_csv(csv_file, index=False)
            console.print(f"✅ Exported to CSV: {csv_file}")

            # Export to Excel
            excel_file = export_dir / "tickets_export.xlsx"
            df_tickets.to_excel(excel_file, index=False, sheet_name="Tickets")
            console.print(f"✅ Exported to Excel: {excel_file}")

            # Export to JSON
            json_file = export_dir / "tickets_export.json"
            df_tickets.to_json(json_file, orient="records", indent=2)
            console.print(f"✅ Exported to JSON: {json_file}")

            console.print(f"\n📁 All exports saved to: {export_dir.absolute()}")

        else:
            console.print("[yellow]⚠️  No data available for export[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Data export demo failed: {e}[/red]")


if __name__ == "__main__":
    # Check for required environment variables
    required_env_vars = [
        "AUTOTASK_USERNAME",
        "AUTOTASK_INTEGRATION_CODE",
        "AUTOTASK_SECRET",
    ]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]

    if missing_vars:
        console.print(
            Panel(
                f"[red]❌ Missing required environment variables:[/red]\n"
                + "\n".join(f"   • {var}" for var in missing_vars)
                + "\n\n[yellow]Please set these variables before running the demo.[/yellow]",
                title="Configuration Error",
                border_style="red",
            )
        )
    else:
        asyncio.run(main())
