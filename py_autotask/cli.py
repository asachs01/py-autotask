#!/usr/bin/env python3
"""
py-autotask CLI: Command-line interface for Autotask data liberation.

This module provides a comprehensive CLI for data extraction, manipulation,
and export from Autotask. Designed to liberate users from platform limitations
and enable complete control over their Autotask data.
"""

import asyncio
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from .async_client import AsyncAutotaskClient
from .bulk_manager import BulkConfig, IntelligentBulkManager
from .client import AutotaskClient
from .exceptions import AutotaskError
from .types import AuthCredentials

console = Console()


class CLIConfig:
    """CLI configuration and state management."""

    def __init__(self):
        self.credentials: Optional[AuthCredentials] = None
        self.client: Optional[Union[AutotaskClient, AsyncAutotaskClient]] = None
        self.verbose: bool = False
        self.output_format: str = "table"
        self.output_file: Optional[str] = None

    @classmethod
    def from_env(cls) -> "CLIConfig":
        """Create CLI config from environment variables.

        Prioritizes local .env file over shell environment variables.
        """
        config = cls()

        # First try to load from local .env file if it exists
        # override=True ensures local .env takes precedence over shell env
        env_path = Path.cwd() / ".env"
        if env_path.exists():
            load_dotenv(env_path, override=True)
            console.print("[dim]Loaded credentials from local .env file[/dim]")

        username = os.environ.get("AUTOTASK_USERNAME")
        integration_code = os.environ.get("AUTOTASK_INTEGRATION_CODE")
        secret = os.environ.get("AUTOTASK_SECRET")
        api_url = os.environ.get("AUTOTASK_API_URL")

        if username and integration_code and secret:
            config.credentials = AuthCredentials(
                username=username,
                integration_code=integration_code,
                secret=secret,
                api_url=api_url,
            )

        return config


# Global CLI configuration
cli_config = CLIConfig()


@click.group()
@click.option("--username", envvar="AUTOTASK_USERNAME", help="Autotask username")
@click.option(
    "--integration-code",
    envvar="AUTOTASK_INTEGRATION_CODE",
    help="Autotask integration code",
)
@click.option("--secret", envvar="AUTOTASK_SECRET", help="Autotask secret")
@click.option("--api-url", envvar="AUTOTASK_API_URL", help="Override API URL")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option(
    "--output-format",
    type=click.Choice(["table", "json", "csv"]),
    default="table",
    help="Output format",
)
@click.option("--output-file", "-o", help="Output file (default: stdout)")
def main(
    username, integration_code, secret, api_url, verbose, output_format, output_file
):
    """
    py-autotask CLI: The ultimate tool for Autotask data liberation.

    Liberate your Autotask data with powerful export, analysis, and manipulation capabilities.
    Break free from platform limitations and own your data completely.
    """
    global cli_config

    if username and integration_code and secret:
        cli_config.credentials = AuthCredentials(
            username=username,
            integration_code=integration_code,
            secret=secret,
            api_url=api_url,
        )
    elif not cli_config.credentials:
        cli_config = CLIConfig.from_env()

    cli_config.verbose = verbose
    cli_config.output_format = output_format
    cli_config.output_file = output_file

    if verbose:
        console.print("[dim]Verbose mode enabled[/dim]")


@main.command()
@click.argument("entities", nargs=-1, required=True)
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["csv", "json", "excel", "parquet"]),
    default="csv",
    help="Export format",
)
@click.option("--output", "-o", help="Output file path")
@click.option("--date-range", help="Date range filter (YYYY-MM-DD,YYYY-MM-DD)")
@click.option("--filters", help="JSON string of additional filters")
@click.option(
    "--include-relationships", is_flag=True, help="Include related entity data"
)
@click.option("--compress", is_flag=True, help="Compress output file")
@click.option("--batch-size", type=int, default=1000, help="Records per batch")
@click.option("--parallel", is_flag=True, help="Use parallel processing")
def export(
    entities,
    export_format,
    output,
    date_range,
    filters,
    include_relationships,
    compress,
    batch_size,
    parallel,
):
    """
    Export Autotask entities to various formats for complete data liberation.

    ENTITIES: Space-separated list of entities to export (e.g., tickets companies contacts)

    Examples:
        py-autotask export tickets --format=excel --output=tickets.xlsx
        py-autotask export companies contacts --date-range=2024-01-01,2024-12-31
        py-autotask export tickets --filters='[{"field":"status","op":"eq","value":"1"}]'
    """
    if not cli_config.credentials:
        console.print(
            "[red]❌ No credentials provided. Set environment variables or use command options.[/red]"
        )
        sys.exit(1)

    asyncio.run(
        _export_data(
            entities,
            export_format,
            output,
            date_range,
            filters,
            include_relationships,
            compress,
            batch_size,
            parallel,
        )
    )


async def _export_data(
    entities,
    export_format,
    output,
    date_range,
    filters,
    include_relationships,
    compress,
    batch_size,
    parallel,
):
    """Execute the data export operation."""
    console.print(
        Panel.fit(
            f"[bold blue]🚀 Autotask Data Liberation[/bold blue]\n"
            f"[green]Exporting {len(entities)} entities: {', '.join(entities)}[/green]",
            border_style="blue",
        )
    )

    try:
        # Create async client for maximum performance
        client = await AsyncAutotaskClient.create(credentials=cli_config.credentials)
        async with client:

            # Test connection first
            console.print("🔗 Testing connection to Autotask API...")
            if not await client.test_connection_async():
                console.print("[red]❌ Failed to connect to Autotask API[/red]")
                return

            console.print("✅ Connected successfully!")

            # Parse date range if provided
            date_filters = []
            if date_range:
                try:
                    start_date, end_date = date_range.split(",")
                    date_filters = [
                        {
                            "field": "createDate",
                            "op": "gte",
                            "value": f"{start_date}T00:00:00Z",
                        },
                        {
                            "field": "createDate",
                            "op": "lte",
                            "value": f"{end_date}T23:59:59Z",
                        },
                    ]
                    console.print(f"📅 Date range: {start_date} to {end_date}")
                except ValueError:
                    console.print(
                        "[red]❌ Invalid date range format. Use YYYY-MM-DD,YYYY-MM-DD[/red]"
                    )
                    return

            # Parse additional filters
            additional_filters = []
            if filters:
                try:
                    additional_filters = json.loads(filters)
                    console.print(
                        f"🔍 Additional filters: {len(additional_filters)} conditions"
                    )
                except json.JSONDecodeError:
                    console.print("[red]❌ Invalid filters JSON format[/red]")
                    return

            # Export each entity
            exported_data = {}

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
            ) as progress:

                for entity in entities:
                    task = progress.add_task(f"Exporting {entity}...", total=100)

                    # Build query filters
                    entity_filters = date_filters + additional_filters

                    # Query entity data
                    console.print(f"📊 Querying {entity} data...")

                    if parallel and len(entities) > 1:
                        # Use bulk query for multiple entities
                        bulk_manager = IntelligentBulkManager(client)
                        query_config = {"entity": entity, "filters": entity_filters}

                        if batch_size:
                            query_config["maxRecords"] = batch_size

                        entity_data = await bulk_manager.bulk_query([query_config])
                        entity_data = entity_data[0].items if entity_data else []
                    else:
                        # Single entity query
                        entity_proxy = getattr(client, entity.lower(), None)
                        if entity_proxy:
                            response = await entity_proxy.query_async(
                                filters=entity_filters
                            )
                            entity_data = response.items
                        else:
                            response = await client.query_async(
                                entity, filters=entity_filters
                            )
                            entity_data = response.items

                    progress.update(task, advance=50)

                    console.print(f"✅ Retrieved {len(entity_data)} {entity} records")
                    exported_data[entity] = entity_data

                    # Handle relationship inclusion
                    if include_relationships and entity_data:
                        console.print(f"🔗 Loading relationships for {entity}...")
                        await _load_relationships(client, entity, entity_data)

                    progress.update(task, advance=50)

            # Export data to specified format
            await _save_exported_data(exported_data, export_format, output, compress)

    except AutotaskError as e:
        console.print(f"[red]❌ Autotask API error: {e}[/red]")
    except Exception as e:
        console.print(f"[red]❌ Export failed: {e}[/red]")
        if cli_config.verbose:
            import traceback

            console.print(f"[dim]{traceback.format_exc()}[/dim]")


async def _load_relationships(client, entity: str, entity_data: List[Dict]) -> None:
    """Load related entity data for relationship inclusion."""
    # This is a simplified relationship loader
    # In a full implementation, this would be more sophisticated

    relationship_mappings = {
        "Tickets": [
            {"field": "AccountID", "entity": "Companies"},
            {"field": "AssignedResourceID", "entity": "Resources"},
            {"field": "ContactID", "entity": "Contacts"},
        ],
        "Projects": [
            {"field": "AccountID", "entity": "Companies"},
            {"field": "ProjectManagerResourceID", "entity": "Resources"},
        ],
        "TimeEntries": [
            {"field": "TicketID", "entity": "Tickets"},
            {"field": "ResourceID", "entity": "Resources"},
            {"field": "ProjectID", "entity": "Projects"},
        ],
    }

    relationships = relationship_mappings.get(entity, [])

    for relationship in relationships:
        field = relationship["field"]
        related_entity = relationship["entity"]

        # Get unique IDs for related entities
        related_ids = list(
            set(item.get(field) for item in entity_data if item.get(field) is not None)
        )

        if related_ids:
            console.print(
                f"   Loading {len(related_ids)} {related_entity} relationships..."
            )

            # Query related entities
            related_filters = [
                {"field": "id", "op": "in", "value": ",".join(map(str, related_ids))}
            ]

            related_proxy = getattr(client, related_entity.lower(), None)
            if related_proxy:
                related_response = await related_proxy.query_async(
                    filters=related_filters
                )
                related_data = {item["id"]: item for item in related_response.items}

                # Embed related data
                for item in entity_data:
                    related_id = item.get(field)
                    if related_id and related_id in related_data:
                        item[f"_{related_entity.lower()}_data"] = related_data[
                            related_id
                        ]


async def _save_exported_data(
    data: Dict[str, List], export_format: str, output: Optional[str], compress: bool
) -> None:
    """Save exported data in the specified format."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    for entity_name, entity_data in data.items():
        if not entity_data:
            console.print(f"[yellow]⚠️  No data to export for {entity_name}[/yellow]")
            continue

        # Determine output filename
        if output:
            base_path = Path(output)
            if len(data) > 1:
                # Multiple entities - add entity name to filename
                output_file = (
                    base_path.parent
                    / f"{base_path.stem}_{entity_name.lower()}{base_path.suffix}"
                )
            else:
                output_file = base_path
        else:
            # Default filename
            output_file = Path(
                f"autotask_{entity_name.lower()}_{timestamp}.{export_format}"
            )

        console.print(
            f"💾 Saving {len(entity_data)} {entity_name} records to {output_file}"
        )

        try:
            if export_format == "csv":
                await _save_csv(entity_data, output_file)
            elif export_format == "json":
                await _save_json(entity_data, output_file)
            elif export_format == "excel":
                await _save_excel(entity_data, output_file)
            elif export_format == "parquet":
                await _save_parquet(entity_data, output_file)

            # Compress if requested
            if compress:
                await _compress_file(output_file)

            console.print(f"✅ Successfully exported {entity_name} to {output_file}")

        except Exception as e:
            console.print(f"[red]❌ Failed to save {entity_name}: {e}[/red]")


async def _save_csv(data: List[Dict], output_file: Path) -> None:
    """Save data as CSV."""
    if not data:
        return

    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = list(data[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


async def _save_json(data: List[Dict], output_file: Path) -> None:
    """Save data as JSON."""
    with open(output_file, "w", encoding="utf-8") as jsonfile:
        json.dump(data, jsonfile, indent=2, default=str)


async def _save_excel(data: List[Dict], output_file: Path) -> None:
    """Save data as Excel."""
    try:
        import pandas as pd

        df = pd.DataFrame(data)
        df.to_excel(output_file, index=False, engine="openpyxl")
    except ImportError:
        console.print(
            "[red]❌ pandas and openpyxl required for Excel export. Install with: pip install pandas openpyxl[/red]"
        )
        raise


async def _save_parquet(data: List[Dict], output_file: Path) -> None:
    """Save data as Parquet."""
    try:
        import pandas as pd

        df = pd.DataFrame(data)
        df.to_parquet(output_file, index=False)
    except ImportError:
        console.print(
            "[red]❌ pandas and pyarrow required for Parquet export. Install with: pip install pandas pyarrow[/red]"
        )
        raise


async def _compress_file(file_path: Path) -> None:
    """Compress a file using gzip."""
    import gzip
    import shutil

    compressed_path = file_path.with_suffix(file_path.suffix + ".gz")

    with open(file_path, "rb") as f_in:
        with gzip.open(compressed_path, "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Remove original file
    file_path.unlink()
    console.print(f"🗜️  Compressed to {compressed_path}")


@main.command()
@click.argument("entity")
@click.option("--filters", help="JSON string of filters")
@click.option("--limit", type=int, default=100, help="Maximum records to display")
@click.option("--fields", help="Comma-separated list of fields to display")
def query(entity, filters, limit, fields):
    """
    Query Autotask entities and display results.

    ENTITY: Entity name to query (e.g., tickets, companies, contacts)

    Examples:
        py-autotask query tickets --filters='[{"field":"status","op":"eq","value":"1"}]'
        py-autotask query companies --limit=50 --fields=id,companyName,isActive
    """
    if not cli_config.credentials:
        console.print("[red]❌ No credentials provided[/red]")
        sys.exit(1)

    asyncio.run(_execute_query(entity, filters, limit, fields))


async def _execute_query(
    entity: str, filters: Optional[str], limit: int, fields: Optional[str]
) -> None:
    """Execute a query operation."""
    try:
        client = await AsyncAutotaskClient.create(credentials=cli_config.credentials)
        async with client:

            # Parse filters
            query_filters = []
            if filters:
                try:
                    query_filters = json.loads(filters)
                except json.JSONDecodeError:
                    console.print("[red]❌ Invalid filters JSON format[/red]")
                    return

            # Parse fields
            include_fields = None
            if fields:
                include_fields = [field.strip() for field in fields.split(",")]

            # Execute query
            console.print(f"🔍 Querying {entity} (limit: {limit})...")

            entity_proxy = getattr(client, entity.lower(), None)
            if entity_proxy:
                response = await entity_proxy.query_async(
                    filters=query_filters,
                    max_records=limit,
                    include_fields=include_fields,
                )
            else:
                response = await client.query_async(
                    entity,
                    filters=query_filters,
                    max_records=limit,
                    include_fields=include_fields,
                )

            # Display results
            if response.items:
                _display_query_results(entity, response.items, include_fields)
            else:
                console.print(
                    f"[yellow]📭 No {entity} records found matching criteria[/yellow]"
                )

    except Exception as e:
        console.print(f"[red]❌ Query failed: {e}[/red]")


def _display_query_results(
    entity: str, items: List[Dict], fields: Optional[List[str]]
) -> None:
    """Display query results in a formatted table."""
    if not items:
        return

    # Determine fields to display
    if fields:
        display_fields = fields
    else:
        # Use common fields or first few fields from first item
        common_fields = [
            "id",
            "name",
            "title",
            "companyName",
            "status",
            "priority",
            "createDate",
        ]
        available_fields = list(items[0].keys())
        display_fields = [field for field in common_fields if field in available_fields]

        # Add remaining fields up to a reasonable limit
        remaining_fields = [
            field for field in available_fields if field not in display_fields
        ]
        display_fields.extend(remaining_fields[:5])  # Limit to prevent wide tables

    # Create table
    table = Table(title=f"{entity} Query Results ({len(items)} records)")

    for field in display_fields:
        table.add_column(field, style="cyan", no_wrap=True)

    # Add rows
    for item in items[:20]:  # Limit displayed rows
        row = []
        for field in display_fields:
            value = item.get(field, "")
            # Truncate long values
            if isinstance(value, str) and len(value) > 50:
                value = value[:47] + "..."
            row.append(str(value))
        table.add_row(*row)

    console.print(table)

    if len(items) > 20:
        console.print(f"[dim]... and {len(items) - 20} more records[/dim]")


@main.command()
@click.argument("entity")
@click.argument("data_file")
@click.option("--batch-size", type=int, default=100, help="Records per batch")
@click.option("--parallel", is_flag=True, help="Use parallel processing")
@click.option("--validate", is_flag=True, help="Validate data before upload")
@click.option(
    "--dry-run", is_flag=True, help="Simulate operation without actual changes"
)
def bulk(entity, data_file, batch_size, parallel, validate, dry_run):
    """
    Perform bulk operations on Autotask entities from CSV/JSON files.

    ENTITY: Entity name (e.g., tickets, companies)
    DATA_FILE: Path to CSV or JSON file containing entity data

    Examples:
        py-autotask bulk tickets tickets.csv --batch-size=200 --parallel
        py-autotask bulk companies companies.json --validate --dry-run
    """
    if not cli_config.credentials:
        console.print("[red]❌ No credentials provided[/red]")
        sys.exit(1)

    asyncio.run(
        _execute_bulk_operation(
            entity, data_file, batch_size, parallel, validate, dry_run
        )
    )


async def _execute_bulk_operation(
    entity: str,
    data_file: str,
    batch_size: int,
    parallel: bool,
    validate: bool,
    dry_run: bool,
) -> None:
    """Execute bulk operation."""
    try:
        # Load data from file
        data_path = Path(data_file)
        if not data_path.exists():
            console.print(f"[red]❌ File not found: {data_file}[/red]")
            return

        console.print(f"📂 Loading data from {data_file}...")

        if data_path.suffix.lower() == ".csv":
            data = _load_csv_data(data_path)
        elif data_path.suffix.lower() == ".json":
            data = _load_json_data(data_path)
        else:
            console.print("[red]❌ Unsupported file format. Use CSV or JSON.[/red]")
            return

        console.print(f"✅ Loaded {len(data)} records")

        # Create async client and bulk manager
        client = await AsyncAutotaskClient.create(credentials=cli_config.credentials)
        async with client:
            bulk_manager = IntelligentBulkManager(client)

            # Configure bulk operation
            config = BulkConfig(
                batch_size=batch_size,
                parallel=parallel,
                validate_data=validate,
                dry_run=dry_run,
                progress_callback=lambda p: console.print(
                    f"   Progress: {p:.1f}%", end="\r"
                ),
            )

            console.print(f"🚀 Starting bulk create for {entity}...")
            if dry_run:
                console.print(
                    "[yellow]🧪 DRY RUN MODE - No actual changes will be made[/yellow]"
                )

            # Execute bulk operation
            result = await bulk_manager.bulk_create(entity, data, config)

            # Display results
            _display_bulk_results(result)

    except Exception as e:
        console.print(f"[red]❌ Bulk operation failed: {e}[/red]")


def _load_csv_data(file_path: Path) -> List[Dict]:
    """Load data from CSV file."""
    data = []
    with open(file_path, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        data = list(reader)
    return data


def _load_json_data(file_path: Path) -> List[Dict]:
    """Load data from JSON file."""
    with open(file_path, "r", encoding="utf-8") as jsonfile:
        data = json.load(jsonfile)

    if not isinstance(data, list):
        raise ValueError("JSON file must contain a list of objects")

    return data


def _display_bulk_results(result) -> None:
    """Display bulk operation results."""
    # Create results table
    table = Table(title="Bulk Operation Results")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Operation", result.operation_type.value.title())
    table.add_row("Entity", result.entity_name)
    table.add_row("Total Records", str(result.total_records))
    table.add_row("Successful", str(result.successful))
    table.add_row("Failed", str(result.failed))
    table.add_row("Duration", f"{result.duration:.2f}s")
    table.add_row("Throughput", f"{result.throughput:.1f} records/min")
    table.add_row("Batch Size", str(result.batch_size_used))
    table.add_row("Parallel Workers", str(result.parallel_workers))

    console.print(table)

    # Display errors if any
    if result.errors:
        console.print(f"\n[red]❌ Errors ({len(result.errors)}):[/red]")
        for i, error in enumerate(result.errors[:5]):  # Show first 5 errors
            console.print(f"   {i+1}. {error.get('error', 'Unknown error')}")

        if len(result.errors) > 5:
            console.print(f"   ... and {len(result.errors) - 5} more errors")


@main.command()
def auth():
    """Authenticate with Autotask API and display zone information."""
    if not cli_config.credentials:
        console.print("[red]❌ No credentials provided[/red]")
        sys.exit(1)

    asyncio.run(_test_connection())


@main.command()
def test():
    """Test connection to Autotask API and display zone information."""
    if not cli_config.credentials:
        console.print("[red]❌ No credentials provided[/red]")
        sys.exit(1)

    asyncio.run(_test_connection())


async def _test_connection() -> None:
    """Test connection and display connection info."""
    try:
        # Enable debug logging
        if cli_config.verbose:
            import logging

            logging.basicConfig(
                level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s"
            )

        console.print("🔗 Testing Autotask API connection...")

        # Debug: Show if credentials are loaded
        if cli_config.credentials:
            console.print(
                f"[dim]📧 Using username: {cli_config.credentials.username}[/dim]"
            )
            console.print(
                f"[dim]🔑 Integration code: {'*' * len(cli_config.credentials.integration_code) if cli_config.credentials.integration_code else 'NOT SET'}[/dim]"
            )
            console.print(
                f"[dim]🔐 Secret: {'SET' if cli_config.credentials.secret else 'NOT SET'}[/dim]"
            )
        else:
            console.print(
                "[yellow]⚠️  No credentials found in environment or command line[/yellow]"
            )
            console.print("[dim]Expected environment variables:[/dim]")
            console.print("[dim]  AUTOTASK_USERNAME[/dim]")
            console.print("[dim]  AUTOTASK_INTEGRATION_CODE[/dim]")
            console.print("[dim]  AUTOTASK_SECRET[/dim]")
            return

        # Test sync auth first
        from .auth import AutotaskAuth
        from .client import AutotaskClient

        console.print("[dim]Testing sync client first...[/dim]")
        try:
            sync_auth = AutotaskAuth(cli_config.credentials)
            sync_client = AutotaskClient(sync_auth)
            sync_success = sync_client.auth.test_connection()
            console.print(
                f"[dim]Sync test result: {'✅ SUCCESS' if sync_success else '❌ FAILED'}[/dim]"
            )
        except Exception as e:
            console.print(f"[dim]Sync test failed: {e}[/dim]")
            sync_success = False

        client = await AsyncAutotaskClient.create(credentials=cli_config.credentials)
        async with client:
            # Show zone detection result
            zone_info = client.auth.zone_info
            if zone_info:
                console.print(f"[dim]🌍 Detected zone: {zone_info.zone_name}[/dim]")
                console.print(f"[dim]📍 Using API URL: {zone_info.url}[/dim]")

            # Test connection
            success = await client.test_connection_async()

            if success:
                console.print("✅ Connection successful!")

                # Display zone info
                zone_info = client.auth.zone_info
                if zone_info:
                    if zone_info.zone_name:
                        console.print(f"🌍 Zone: {zone_info.zone_name}")
                    console.print(f"📍 API URL: {zone_info.url}")
                    if zone_info.web_url:
                        console.print(f"🌐 Web URL: {zone_info.web_url}")
                    if zone_info.ci is not None:
                        console.print(f"🔢 CI: {zone_info.ci}")

                # Get rate limit info
                rate_info = await client.get_rate_limit_info()
                if rate_info:
                    table = Table(title="Rate Limit Information")
                    table.add_column("Metric", style="cyan")
                    table.add_column("Value", style="green")

                    for key, value in rate_info.items():
                        if value is not None:
                            table.add_row(key.replace("_", " ").title(), str(value))

                    console.print(table)
            else:
                console.print("[red]❌ Connection failed[/red]")

                # Check if zone detection worked but API calls fail (401)
                if zone_info:
                    console.print(
                        "\n[yellow]⚠️  Zone detection succeeded but API authentication failed.[/yellow]"
                    )
                    console.print("\n[bold]This typically means:[/bold]")
                    console.print(
                        "• Your credentials are valid (zone detection worked)"
                    )
                    console.print("• But the API user lacks proper permissions")
                    console.print("\n[bold]To fix this issue:[/bold]")
                    console.print("1. Log into Autotask admin panel")
                    console.print("2. Navigate to Admin → Resources → Security Levels")
                    console.print(
                        "3. Ensure your API user has 'API User (API-only)' security level"
                    )
                    console.print("4. The API user should NOT have regular user access")
                    console.print(
                        "\n[dim]Note: API users require a special security level that's different from regular user accounts.[/dim]"
                    )

    except Exception as e:
        console.print(f"[red]❌ Connection test failed: {e}[/red]")


@main.command()
@click.argument("entity")
@click.option("--count", is_flag=True, help="Show record count only")
@click.option("--fields", is_flag=True, help="Show available fields")
@click.option("--sample", type=int, help="Show sample records")
def inspect(entity, count, fields, sample):
    """
    Inspect Autotask entities to understand data structure and availability.

    ENTITY: Entity name to inspect

    Examples:
        py-autotask inspect tickets --count
        py-autotask inspect companies --fields
        py-autotask inspect contacts --sample=5
    """
    if not cli_config.credentials:
        console.print("[red]❌ No credentials provided[/red]")
        sys.exit(1)

    asyncio.run(_inspect_entity(entity, count, fields, sample))


async def _inspect_entity(
    entity: str, show_count: bool, show_fields: bool, sample_size: Optional[int]
) -> None:
    """Inspect an entity."""
    try:
        client = await AsyncAutotaskClient.create(credentials=cli_config.credentials)
        async with client:

            if show_count:
                console.print(f"📊 Counting {entity} records...")

                # Get total count (limit to reasonable number for counting)
                response = await client.query_async(entity, max_records=10000)
                count = len(response.items)

                console.print(f"✅ Total {entity} records: {count}")

                if count >= 10000:
                    console.print(
                        "[yellow]⚠️  Showing count up to 10,000 records limit[/yellow]"
                    )

            if show_fields or sample_size:
                console.print(f"🔍 Analyzing {entity} structure...")

                # Get sample records
                sample_response = await client.query_async(
                    entity, max_records=sample_size or 5
                )

                if sample_response.items:
                    sample_item = sample_response.items[0]

                    if show_fields:
                        table = Table(title=f"{entity} Available Fields")
                        table.add_column("Field Name", style="cyan")
                        table.add_column("Sample Value", style="green")
                        table.add_column("Type", style="yellow")

                        for field_name, value in sample_item.items():
                            sample_value = (
                                str(value)[:50] if value is not None else "NULL"
                            )
                            value_type = type(value).__name__
                            table.add_row(field_name, sample_value, value_type)

                        console.print(table)

                    if sample_size:
                        console.print(f"\n📋 Sample {entity} records:")
                        for i, item in enumerate(sample_response.items[:sample_size]):
                            console.print(f"\n[bold]Record {i+1}:[/bold]")
                            for key, value in list(item.items())[
                                :10
                            ]:  # Limit fields shown
                                console.print(f"  {key}: {value}")

                            if len(item) > 10:
                                console.print(f"  ... and {len(item) - 10} more fields")
                else:
                    console.print(f"[yellow]📭 No {entity} records found[/yellow]")

    except Exception as e:
        console.print(f"[red]❌ Inspection failed: {e}[/red]")


@main.command()
def entities():
    """List all available Autotask entities that can be queried."""
    # This would ideally query the API for available entities
    # For now, showing common entities

    common_entities = [
        "Tickets",
        "Companies",
        "Contacts",
        "Resources",
        "Projects",
        "TimeEntries",
        "Invoices",
        "Contracts",
        "Tasks",
        "Notes",
        "Attachments",
        "Products",
        "Services",
        "Expenses",
        "Quotes",
    ]

    table = Table(title="Available Autotask Entities")
    table.add_column("Entity Name", style="cyan")
    table.add_column("Description", style="green")

    entity_descriptions = {
        "Tickets": "Support tickets and service requests",
        "Companies": "Customer and prospect company records",
        "Contacts": "Individual contact records",
        "Resources": "Internal staff and technician records",
        "Projects": "Project management records",
        "TimeEntries": "Time tracking and billing records",
        "Invoices": "Billing and invoice records",
        "Contracts": "Service contracts and agreements",
        "Tasks": "Task management records",
        "Notes": "Notes and documentation",
        "Attachments": "File attachments",
        "Products": "Product catalog items",
        "Services": "Service offerings",
        "Expenses": "Expense tracking records",
        "Quotes": "Sales quotes and proposals",
    }

    for entity in common_entities:
        description = entity_descriptions.get(entity, "Entity description")
        table.add_row(entity, description)

    console.print(table)
    console.print(
        "\n[dim]💡 Use 'py-autotask inspect <entity>' to explore any entity structure[/dim]"
    )


if __name__ == "__main__":
    main()
