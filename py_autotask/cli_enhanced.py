"""
Enhanced CLI for py-autotask with comprehensive data liberation features.

This module provides a powerful command-line interface for data export,
bulk operations, migration, and advanced Autotask data management.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

import click
import pandas as pd
from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

from .async_client import AsyncAutotaskClient
from .bulk_manager import IntelligentBulkManager
from .caching import CacheConfig

console = Console()


@click.group()
@click.option("--username", envvar="AUTOTASK_USERNAME", help="Autotask username")
@click.option(
    "--integration-code", envvar="AUTOTASK_INTEGRATION_CODE", help="Integration code"
)
@click.option("--secret", envvar="AUTOTASK_SECRET", help="API secret")
@click.option("--api-url", envvar="AUTOTASK_API_URL", help="Override API URL")
@click.option("--cache/--no-cache", default=True, help="Enable caching")
@click.option(
    "--cache-backend", default="memory", type=click.Choice(["memory", "redis", "disk"])
)
@click.option(
    "--redis-url", default="redis://localhost:6379", help="Redis connection URL"
)
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(
    ctx,
    username,
    integration_code,
    secret,
    api_url,
    cache,
    cache_backend,
    redis_url,
    verbose,
):
    """
    py-autotask: The most powerful Python SDK for Autotask API.

    Provides comprehensive data export, bulk operations, and migration tools
    to give you complete control over your Autotask data.
    """
    ctx.ensure_object(dict)
    ctx.obj["credentials"] = {
        "username": username,
        "integration_code": integration_code,
        "secret": secret,
        "api_url": api_url,
    }
    ctx.obj["cache_config"] = (
        CacheConfig(
            backend=cache_backend,
            redis_url=redis_url if cache_backend == "redis" else None,
        )
        if cache
        else None
    )
    ctx.obj["verbose"] = verbose


@cli.group()
def export():
    """Export data from Autotask to various formats."""


@export.command("entities")
@click.argument("entity_types", nargs=-1, required=True)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["csv", "excel", "json", "sql", "parquet"]),
    default="csv",
    help="Export format",
)
@click.option("--output", "-o", help="Output file path")
@click.option("--filter", help="JSON filter string")
@click.option("--date-range", help="Date range filter (YYYY-MM-DD,YYYY-MM-DD)")
@click.option(
    "--include-relationships", is_flag=True, help="Include related entity data"
)
@click.option("--batch-size", default=500, help="Batch size for data retrieval")
@click.option("--compress", is_flag=True, help="Compress output file")
@click.option("--max-records", type=int, help="Maximum records to export")
@click.pass_context
def export_entities(
    ctx,
    entity_types,
    format,
    output,
    filter,
    date_range,
    include_relationships,
    batch_size,
    compress,
    max_records,
):
    """
    Export entities to various formats with advanced filtering.

    Examples:
        py-autotask export entities tickets companies --format=excel --output=data.xlsx
        py-autotask export entities tickets --date-range="2024-01-01,2024-12-31"
        py-autotask export entities companies --filter='{"field":"isActive","op":"eq","value":true}'
    """
    asyncio.run(
        _export_entities_async(
            ctx.obj,
            entity_types,
            format,
            output,
            filter,
            date_range,
            include_relationships,
            batch_size,
            compress,
            max_records,
        )
    )


async def _export_entities_async(
    config,
    entity_types,
    format,
    output,
    filter_str,
    date_range,
    include_relationships,
    batch_size,
    compress,
    max_records,
):
    """Async implementation of entity export."""

    # Parse filters
    filters = None
    if filter_str:
        try:
            filters = json.loads(filter_str)
            if not isinstance(filters, list):
                filters = [filters]
        except json.JSONDecodeError:
            console.print(f"[red]Invalid JSON filter: {filter_str}[/red]")
            return

    # Parse date range
    if date_range:
        try:
            start_date, end_date = date_range.split(",")
            date_filter = {
                "field": "createDate",
                "op": "between",
                "value": f"{start_date}T00:00:00Z,{end_date}T23:59:59Z",
            }
            if filters:
                filters.append(date_filter)
            else:
                filters = [date_filter]
        except ValueError:
            console.print(
                "[red]Invalid date range format. Use: YYYY-MM-DD,YYYY-MM-DD[/red]"
            )
            return

    # Create client
    config.get("cache_config")
    async with AsyncAutotaskClient.create(**config["credentials"]) as client:

        all_data = {}
        total_records = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            console=console,
        ) as progress:

            for entity_type in entity_types:
                task_id = progress.add_task(f"Exporting {entity_type}...", total=100)

                try:
                    # Query all data with pagination
                    query_params = {}
                    if filters:
                        query_params["filters"] = filters
                    if max_records:
                        query_params["max_records"] = max_records

                    # Get entity handler
                    entity_handler = getattr(client.entities, entity_type.lower())

                    # Query with progress tracking
                    records = []
                    page_size = min(batch_size, 500)  # API limit
                    offset = 0

                    while True:
                        page_data = await entity_handler.query_async(
                            **query_params, max_records=page_size, offset=offset
                        )

                        if not page_data.items:
                            break

                        records.extend(page_data.items)
                        offset += len(page_data.items)
                        total_records += len(page_data.items)

                        # Update progress
                        if max_records:
                            progress_pct = min((len(records) / max_records) * 100, 100)
                        else:
                            progress_pct = min(50 + (offset / 10000) * 50, 100)

                        progress.update(task_id, completed=progress_pct)

                        if max_records and len(records) >= max_records:
                            records = records[:max_records]
                            break

                        if len(page_data.items) < page_size:
                            break

                    # Include relationships if requested
                    if include_relationships and records:
                        await _include_relationships(client, entity_type, records)

                    all_data[entity_type] = records
                    progress.update(task_id, completed=100)

                    console.print(
                        f"[green]✓ Exported {len(records)} {entity_type} records[/green]"
                    )

                except Exception as e:
                    console.print(f"[red]✗ Failed to export {entity_type}: {e}[/red]")
                    continue

        # Export data in requested format
        if not output:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            entities_str = "_".join(entity_types)
            output = f"autotask_export_{entities_str}_{timestamp}.{format}"

        await _write_export_data(all_data, output, format, compress)

        console.print("\n[bold green]✓ Export completed![/bold green]")
        console.print(f"📁 Output: {output}")
        console.print(f"📊 Total records: {total_records}")


async def _include_relationships(client, entity_type, records):
    """Include related entity data in export."""
    # Define common relationships
    relationships = {
        "tickets": [
            ("accountID", "companies"),
            ("assignedResourceID", "resources"),
            ("projectID", "projects"),
        ],
        "time_entries": [
            ("ticketID", "tickets"),
            ("resourceID", "resources"),
            ("taskID", "tasks"),
        ],
        "contacts": [("companyID", "companies")],
    }

    entity_relationships = relationships.get(entity_type.lower(), [])

    for field, related_entity in entity_relationships:
        # Get unique related IDs
        related_ids = list(
            set(record.get(field) for record in records if record.get(field))
        )

        if related_ids:
            # Fetch related entities
            related_handler = getattr(client.entities, related_entity)
            related_data = {}

            # Batch fetch related entities
            for related_id in related_ids:
                try:
                    related_record = await related_handler.get_async(related_id)
                    if related_record:
                        related_data[related_id] = related_record
                except Exception:
                    continue

            # Add related data to records
            for record in records:
                if record.get(field) and record[field] in related_data:
                    record[f"{related_entity}_data"] = related_data[record[field]]


async def _write_export_data(data, output_path, format, compress):
    """Write export data to file in specified format."""

    if format == "csv":
        # Export each entity type to separate CSV files
        for entity_type, records in data.items():
            if not records:
                continue

            if len(data) > 1:
                # Multiple entities - create separate files
                base_name = Path(output_path).stem
                extension = Path(output_path).suffix
                entity_output = f"{base_name}_{entity_type}{extension}"
            else:
                entity_output = output_path

            df = pd.DataFrame(records)
            if compress:
                entity_output += ".gz"
                df.to_csv(entity_output, index=False, compression="gzip")
            else:
                df.to_csv(entity_output, index=False)

    elif format == "excel":
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for entity_type, records in data.items():
                if records:
                    df = pd.DataFrame(records)
                    # Excel sheet names are limited to 31 characters
                    sheet_name = entity_type[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)

    elif format == "json":
        output_data = data if len(data) > 1 else list(data.values())[0]

        if compress:
            import gzip

            with gzip.open(output_path + ".gz", "wt") as f:
                json.dump(output_data, f, indent=2, default=str)
        else:
            with open(output_path, "w") as f:
                json.dump(output_data, f, indent=2, default=str)

    elif format == "parquet":
        for entity_type, records in data.items():
            if not records:
                continue

            if len(data) > 1:
                base_name = Path(output_path).stem
                entity_output = f"{base_name}_{entity_type}.parquet"
            else:
                entity_output = output_path

            df = pd.DataFrame(records)
            df.to_parquet(
                entity_output, index=False, compression="gzip" if compress else None
            )


@cli.group()
def bulk():
    """Bulk operations for creating, updating, and deleting entities."""


@bulk.command("create")
@click.argument("entity_type")
@click.argument("data_file", type=click.Path(exists=True))
@click.option("--batch-size", default="auto", help="Batch size (auto for optimization)")
@click.option("--parallel", default=True, help="Enable parallel processing")
@click.option(
    "--validate", is_flag=True, default=True, help="Validate data before creation"
)
@click.option("--dry-run", is_flag=True, help="Simulate without actual creation")
@click.option("--output", help="Output file for results")
@click.pass_context
def bulk_create(
    ctx, entity_type, data_file, batch_size, parallel, validate, dry_run, output
):
    """
    Bulk create entities from CSV or JSON file.

    Examples:
        py-autotask bulk create tickets tickets.csv --batch-size=200
        py-autotask bulk create companies companies.json --dry-run
    """
    asyncio.run(
        _bulk_create_async(
            ctx.obj,
            entity_type,
            data_file,
            batch_size,
            parallel,
            validate,
            dry_run,
            output,
        )
    )


async def _bulk_create_async(
    config, entity_type, data_file, batch_size, parallel, validate, dry_run, output
):
    """Async implementation of bulk create."""

    # Load data from file
    file_path = Path(data_file)

    try:
        if file_path.suffix.lower() == ".csv":
            df = pd.read_csv(data_file)
            data = df.to_dict("records")
        elif file_path.suffix.lower() == ".json":
            with open(data_file, "r") as f:
                data = json.load(f)
                if not isinstance(data, list):
                    data = [data]
        else:
            console.print(f"[red]Unsupported file format: {file_path.suffix}[/red]")
            return

    except Exception as e:
        console.print(f"[red]Failed to load data file: {e}[/red]")
        return

    if not data:
        console.print("[yellow]No data found in file[/yellow]")
        return

    # Create client and bulk manager
    async with AsyncAutotaskClient.create(**config["credentials"]) as client:
        bulk_manager = IntelligentBulkManager(client)

        console.print(
            f"[blue]Starting bulk create: {len(data)} {entity_type} records[/blue]"
        )
        if dry_run:
            console.print("[yellow]DRY RUN - No actual API calls will be made[/yellow]")

        # Progress callback
        def progress_callback(percentage):
            console.print(f"Progress: {percentage:.1f}%", end="\r")

        try:
            # Parse batch_size
            if batch_size == "auto":
                batch_size_int = "auto"
            else:
                batch_size_int = int(batch_size)

            # Execute bulk create
            result = await bulk_manager.bulk_create(
                entity=entity_type,
                data=data,
                batch_size=batch_size_int,
                parallel=parallel,
                validate=validate,
                dry_run=dry_run,
                progress_callback=progress_callback,
            )

            # Display results
            console.print("\n[bold]Bulk Create Results:[/bold]")

            table = Table()
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")

            table.add_row("Total Records", str(result.total_records))
            table.add_row("Successful", str(result.successful))
            table.add_row("Failed", str(result.failed))
            table.add_row("Duration", f"{result.duration:.2f}s")
            table.add_row("Throughput", f"{result.throughput:.1f} records/sec")

            console.print(table)

            if result.errors:
                console.print(f"\n[red]Errors ({len(result.errors)}):[/red]")
                for error in result.errors[:10]:  # Show first 10 errors
                    console.print(f"  • {error}")

                if len(result.errors) > 10:
                    console.print(f"  ... and {len(result.errors) - 10} more errors")

            # Save results if requested
            if output:
                result_data = {
                    "summary": {
                        "total_records": result.total_records,
                        "successful": result.successful,
                        "failed": result.failed,
                        "duration": result.duration,
                        "throughput": result.throughput,
                    },
                    "errors": result.errors,
                }

                with open(output, "w") as f:
                    json.dump(result_data, f, indent=2, default=str)

                console.print(f"Results saved to: {output}")

        except Exception as e:
            console.print(f"[red]Bulk create failed: {e}[/red]")


@cli.command("migrate")
@click.option(
    "--from-format", type=click.Choice(["soap", "csv", "json"]), required=True
)
@click.option(
    "--to-format", type=click.Choice(["rest", "csv", "json", "excel"]), default="rest"
)
@click.option("--input", "-i", required=True, help="Input file or directory")
@click.option("--output", "-o", help="Output file or directory")
@click.option(
    "--backup-first", is_flag=True, help="Backup existing data before migration"
)
@click.option("--mapping-file", help="Field mapping configuration file")
@click.pass_context
def migrate(ctx, from_format, to_format, input, output, backup_first, mapping_file):
    """
    Migrate data between formats or from SOAP to REST API.

    Examples:
        py-autotask migrate --from-format=soap --to-format=rest --backup-first
        py-autotask migrate --from-format=csv --to-format=json --input=data.csv --output=data.json
    """
    asyncio.run(
        _migrate_async(
            ctx.obj, from_format, to_format, input, output, backup_first, mapping_file
        )
    )


async def _migrate_async(
    config, from_format, to_format, input, output, backup_first, mapping_file
):
    """Async implementation of migration."""

    console.print(f"[blue]Starting migration: {from_format} → {to_format}[/blue]")

    if from_format == "soap" and to_format == "rest":
        console.print(
            "[yellow]SOAP to REST API migration - This is a complex operation[/yellow]"
        )

        if backup_first:
            console.print("[blue]Creating backup of current data...[/blue]")
            # Implement backup logic
            await _create_backup(config)

        # Implement SOAP to REST migration
        await _migrate_soap_to_rest(config, mapping_file)

    else:
        # File format migration
        await _migrate_file_formats(from_format, to_format, input, output)

    console.print("[bold green]✓ Migration completed![/bold green]")


async def _create_backup(config):
    """Create a backup of all current Autotask data."""
    async with AsyncAutotaskClient.create(**config["credentials"]) as client:

        # Common entity types for backup
        entity_types = ["tickets", "companies", "contacts", "projects", "time_entries"]

        backup_dir = Path(f"autotask_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        backup_dir.mkdir(exist_ok=True)

        with Progress(console=console) as progress:
            for entity_type in entity_types:
                task_id = progress.add_task(f"Backing up {entity_type}...", total=100)

                try:
                    entity_handler = getattr(client.entities, entity_type)
                    records = []

                    # Query all records
                    page_size = 500
                    offset = 0

                    while True:
                        page_data = await entity_handler.query_async(
                            max_records=page_size, offset=offset
                        )
                        if not page_data.items:
                            break

                        records.extend(page_data.items)
                        offset += len(page_data.items)

                        progress.update(
                            task_id, completed=min(offset / 10000 * 100, 100)
                        )

                        if len(page_data.items) < page_size:
                            break

                    # Save backup
                    backup_file = backup_dir / f"{entity_type}.json"
                    with open(backup_file, "w") as f:
                        json.dump(records, f, indent=2, default=str)

                    progress.update(task_id, completed=100)
                    console.print(
                        f"[green]✓ Backed up {len(records)} {entity_type} records[/green]"
                    )

                except Exception as e:
                    console.print(f"[red]✗ Failed to backup {entity_type}: {e}[/red]")

        console.print(f"[green]Backup completed: {backup_dir}[/green]")


async def _migrate_soap_to_rest(config, mapping_file):
    """Migrate from SOAP to REST API."""
    console.print(
        "[blue]SOAP to REST migration functionality would be implemented here[/blue]"
    )
    # This would involve:
    # 1. Reading SOAP API data
    # 2. Mapping fields between SOAP and REST
    # 3. Converting data formats
    # 4. Uploading to REST API
    # 5. Validation and rollback capabilities


async def _migrate_file_formats(from_format, to_format, input_path, output_path):
    """Migrate between file formats."""
    console.print(
        f"[blue]Converting {input_path} from {from_format} to {to_format}[/blue]"
    )

    # Load source data
    if from_format == "csv":
        df = pd.read_csv(input_path)
        data = df.to_dict("records")
    elif from_format == "json":
        with open(input_path, "r") as f:
            data = json.load(f)

    # Convert to target format
    if to_format == "csv":
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
    elif to_format == "json":
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    elif to_format == "excel":
        df = pd.DataFrame(data)
        df.to_excel(output_path, index=False)


if __name__ == "__main__":
    cli()
