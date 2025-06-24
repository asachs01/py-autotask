"""
Command-line interface for py-autotask.

This module provides a CLI for common Autotask API operations,
allowing users to interact with the API from the command line.
"""

import json
import logging
import os
import sys
from typing import Optional

import click
from dotenv import load_dotenv

from . import AutotaskClient
from .exceptions import AutotaskError

# Load environment variables
load_dotenv()


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def get_client_from_env() -> AutotaskClient:
    """Create client from environment variables."""
    username = os.getenv("AUTOTASK_USERNAME")
    integration_code = os.getenv("AUTOTASK_INTEGRATION_CODE")
    secret = os.getenv("AUTOTASK_SECRET")
    api_url = os.getenv("AUTOTASK_API_URL")

    if not all([username, integration_code, secret]):
        click.echo("Error: Missing required environment variables.")
        click.echo(
            "Please set: AUTOTASK_USERNAME, AUTOTASK_INTEGRATION_CODE, AUTOTASK_SECRET"
        )
        sys.exit(1)

    return AutotaskClient.create(
        username=username,
        integration_code=integration_code,
        secret=secret,
        api_url=api_url,
    )


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """py-autotask: Python client for Autotask REST API."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    setup_logging(verbose)


@main.command()
@click.option("--username", "-u", help="API username")
@click.option("--integration-code", "-i", help="Integration code")
@click.option("--secret", "-s", help="API secret")
@click.option("--api-url", help="Override API URL")
@click.pass_context
def auth(
    ctx: click.Context,
    username: Optional[str],
    integration_code: Optional[str],
    secret: Optional[str],
    api_url: Optional[str],
) -> None:
    """Test authentication and zone detection."""
    try:
        if username and integration_code and secret:
            client = AutotaskClient.create(
                username=username,
                integration_code=integration_code,
                secret=secret,
                api_url=api_url,
            )
        else:
            client = get_client_from_env()

        # Test authentication by getting zone info
        zone_info = client.auth.zone_info
        if zone_info:
            click.echo("✓ Authentication successful!")
            click.echo(f"  Zone URL: {zone_info.url}")
            click.echo(f"  Database Type: {zone_info.data_base_type}")
        else:
            click.echo("✗ Authentication failed - could not detect zone")

    except AutotaskError as e:
        click.echo(f"✗ Authentication failed: {e}")
        sys.exit(1)


@main.group()
def get() -> None:
    """Get entities by ID."""


@get.command()
@click.argument("ticket_id", type=int)
@click.option("--output", "-o", type=click.Choice(["json", "table"]), default="json")
@click.pass_context
def ticket(ctx: click.Context, ticket_id: int, output: str) -> None:
    """Get a ticket by ID."""
    try:
        client = get_client_from_env()
        ticket_data = client.tickets.get(ticket_id)

        if ticket_data:
            if output == "json":
                click.echo(json.dumps(ticket_data, indent=2))
            else:
                # Simple table output
                click.echo(f"Ticket ID: {ticket_data.get('id', 'N/A')}")
                click.echo(f"Title: {ticket_data.get('title', 'N/A')}")
                click.echo(f"Status: {ticket_data.get('status', 'N/A')}")
                click.echo(f"Priority: {ticket_data.get('priority', 'N/A')}")
        else:
            click.echo(f"Ticket {ticket_id} not found")

    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@get.command()
@click.argument("company_id", type=int)
@click.option("--output", "-o", type=click.Choice(["json", "table"]), default="json")
@click.pass_context
def company(ctx: click.Context, company_id: int, output: str) -> None:
    """Get a company by ID."""
    try:
        client = get_client_from_env()
        company_data = client.companies.get(company_id)

        if company_data:
            if output == "json":
                click.echo(json.dumps(company_data, indent=2))
            else:
                # Simple table output
                click.echo(f"Company ID: {company_data.get('id', 'N/A')}")
                click.echo(f"Name: {company_data.get('companyName', 'N/A')}")
                click.echo(f"Type: {company_data.get('companyType', 'N/A')}")
                click.echo(f"Active: {company_data.get('isActive', 'N/A')}")
        else:
            click.echo(f"Company {company_id} not found")

    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@main.group()
def query() -> None:
    """Query entities with filters."""


@query.command()
@click.option("--filter", "-f", help="JSON filter string")
@click.option("--fields", help="Comma-separated list of fields to include")
@click.option("--max-records", type=int, help="Maximum records to return")
@click.option("--output", "-o", type=click.Choice(["json", "table"]), default="json")
@click.pass_context
def tickets(
    ctx: click.Context,
    filter: Optional[str],
    fields: Optional[str],
    max_records: Optional[int],
    output: str,
) -> None:
    """Query tickets with optional filters."""
    try:
        client = get_client_from_env()

        # Parse filter if provided
        filters = None
        if filter:
            try:
                filters = json.loads(filter)
            except json.JSONDecodeError:
                click.echo("Error: Invalid JSON filter format")
                sys.exit(1)

        # Parse fields if provided
        include_fields = None
        if fields:
            include_fields = [f.strip() for f in fields.split(",")]

        response = client.tickets.query(
            filters=filters, include_fields=include_fields, max_records=max_records
        )

        if output == "json":
            # Convert response to dict for JSON serialization
            result = {
                "items": response.items,
                "page_details": {
                    "count": response.page_details.count,
                    "request_count": response.page_details.request_count,
                    "next_page_url": response.page_details.next_page_url,
                    "prev_page_url": response.page_details.prev_page_url,
                },
            }
            click.echo(json.dumps(result, indent=2))
        else:
            # Simple table output
            click.echo(f"Found {len(response.items)} tickets:")
            for item in response.items:
                click.echo(f"  ID: {item.get('id')} - {item.get('title', 'No title')}")

    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@query.command()
@click.option("--filter", "-f", help="JSON filter string")
@click.option("--fields", help="Comma-separated list of fields to include")
@click.option("--max-records", type=int, help="Maximum records to return")
@click.option("--output", "-o", type=click.Choice(["json", "table"]), default="json")
@click.pass_context
def companies(
    ctx: click.Context,
    filter: Optional[str],
    fields: Optional[str],
    max_records: Optional[int],
    output: str,
) -> None:
    """Query companies with optional filters."""
    try:
        client = get_client_from_env()

        # Parse filter if provided
        filters = None
        if filter:
            try:
                filters = json.loads(filter)
            except json.JSONDecodeError:
                click.echo("Error: Invalid JSON filter format")
                sys.exit(1)

        # Parse fields if provided
        include_fields = None
        if fields:
            include_fields = [f.strip() for f in fields.split(",")]

        response = client.companies.query(
            filters=filters, include_fields=include_fields, max_records=max_records
        )

        if output == "json":
            # Convert response to dict for JSON serialization
            result = {
                "items": response.items,
                "page_details": {
                    "count": response.page_details.count,
                    "request_count": response.page_details.request_count,
                    "next_page_url": response.page_details.next_page_url,
                    "prev_page_url": response.page_details.prev_page_url,
                },
            }
            click.echo(json.dumps(result, indent=2))
        else:
            # Simple table output
            click.echo(f"Found {len(response.items)} companies:")
            for item in response.items:
                click.echo(
                    f"  ID: {item.get('id')} - {item.get('companyName', 'No name')}"
                )

    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@main.command()
@click.argument("entity")
@click.option("--output", "-o", type=click.Choice(["json", "table"]), default="json")
@click.pass_context
def info(ctx: click.Context, entity: str, output: str) -> None:
    """Get information about an entity type."""
    try:
        client = get_client_from_env()
        entity_info = client.get_entity_info(entity)

        if output == "json":
            click.echo(json.dumps(entity_info, indent=2))
        else:
            # Simple table output for entity info
            click.echo(f"Entity: {entity}")
            if "entityInformation" in entity_info:
                info = entity_info["entityInformation"]
                click.echo(f"Name: {info.get('name', 'N/A')}")
                click.echo(
                    f"Has User Defined Fields: {info.get('hasUserDefinedFields', 'N/A')}"
                )
                click.echo(f"Supports Query: {info.get('supportsQuery', 'N/A')}")

    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


# Phase 4: Batch Operations
@main.group()
def batch() -> None:
    """Batch operations for multiple entities."""


@batch.command()
@click.argument("entity")
@click.argument("data_file", type=click.File("r"))
@click.option("--batch-size", type=int, default=200, help="Batch size (max 200)")
@click.option(
    "--output", "-o", type=click.Choice(["json", "summary"]), default="summary"
)
@click.pass_context
def create(
    ctx: click.Context, entity: str, data_file, batch_size: int, output: str
) -> None:
    """Create multiple entities from JSON file."""
    try:
        client = get_client_from_env()

        # Parse input data
        try:
            entities_data = json.load(data_file)
            if not isinstance(entities_data, list):
                entities_data = [entities_data]
        except json.JSONDecodeError as e:
            click.echo(f"Error parsing JSON file: {e}")
            sys.exit(1)

        click.echo(
            f"Creating {len(entities_data)} {entity} entities in batches of {batch_size}..."
        )

        results = client.batch_create(entity, entities_data, batch_size)

        if output == "json":
            output_data = [{"item_id": r.item_id, "errors": r.errors} for r in results]
            click.echo(json.dumps(output_data, indent=2))
        else:
            success_count = sum(1 for r in results if r.item_id)
            click.echo(
                f"✓ Successfully created {success_count}/{len(entities_data)} entities"
            )

            # Show any errors
            for i, result in enumerate(results):
                if result.errors:
                    click.echo(f"  Entity {i + 1} errors: {result.errors}")

    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@batch.command()
@click.argument("entity")
@click.argument("data_file", type=click.File("r"))
@click.option("--batch-size", type=int, default=200, help="Batch size (max 200)")
@click.option(
    "--output", "-o", type=click.Choice(["json", "summary"]), default="summary"
)
@click.pass_context
def update(
    ctx: click.Context, entity: str, data_file, batch_size: int, output: str
) -> None:
    """Update multiple entities from JSON file."""
    try:
        client = get_client_from_env()

        # Parse input data
        try:
            entities_data = json.load(data_file)
            if not isinstance(entities_data, list):
                entities_data = [entities_data]
        except json.JSONDecodeError as e:
            click.echo(f"Error parsing JSON file: {e}")
            sys.exit(1)

        # Validate all have IDs
        for i, data in enumerate(entities_data):
            if not data.get("id"):
                click.echo(f"Error: Entity at index {i} missing 'id' field")
                sys.exit(1)

        click.echo(
            f"Updating {len(entities_data)} {entity} entities in batches of {batch_size}..."
        )

        results = client.batch_update(entity, entities_data, batch_size)

        if output == "json":
            click.echo(json.dumps(results, indent=2))
        else:
            click.echo(f"✓ Successfully updated {len(results)} entities")

    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@batch.command()
@click.argument("entity")
@click.argument("ids", nargs=-1, type=int)
@click.option("--batch-size", type=int, default=200, help="Batch size (max 200)")
@click.option(
    "--ids-file", type=click.File("r"), help="File with entity IDs (one per line)"
)
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete(
    ctx: click.Context,
    entity: str,
    ids: tuple,
    batch_size: int,
    ids_file,
    confirm: bool,
) -> None:
    """Delete multiple entities by ID."""
    try:
        # Collect entity IDs
        entity_ids = list(ids)

        if ids_file:
            for line in ids_file:
                line = line.strip()
                if line and line.isdigit():
                    entity_ids.append(int(line))

        if not entity_ids:
            click.echo("Error: No entity IDs provided")
            sys.exit(1)

        # Confirmation prompt
        if not confirm:
            if not click.confirm(f"Delete {len(entity_ids)} {entity} entities?"):
                click.echo("Aborted.")
                return

        click.echo(
            f"Deleting {len(entity_ids)} {entity} entities in batches of {batch_size}..."
        )

        client = get_client_from_env()
        results = client.batch_delete(entity, entity_ids, batch_size)

        success_count = sum(results)
        click.echo(f"✓ Successfully deleted {success_count}/{len(entity_ids)} entities")

        if success_count < len(entity_ids):
            failed_count = len(entity_ids) - success_count
            click.echo(f"⚠ {failed_count} deletions failed")

    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


# Phase 4: Attachment Operations
@main.group()
def attachments() -> None:
    """File attachment operations."""


@attachments.command()
@click.argument("parent_type")
@click.argument("parent_id", type=int)
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--title", help="Attachment title")
@click.option("--description", help="Attachment description")
@click.pass_context
def upload(
    ctx: click.Context,
    parent_type: str,
    parent_id: int,
    file_path: str,
    title: Optional[str],
    description: Optional[str],
) -> None:
    """Upload a file attachment to an entity."""
    try:
        client = get_client_from_env()

        click.echo(f"Uploading {file_path} to {parent_type} {parent_id}...")

        result = client.attachments.upload_file(
            parent_type=parent_type,
            parent_id=parent_id,
            file_path=file_path,
            title=title,
            description=description,
        )

        click.echo(f"✓ Successfully uploaded attachment with ID: {result.id}")
        click.echo(f"  Title: {result.title}")
        click.echo(f"  File: {result.file_name}")
        click.echo(f"  Size: {result.file_size} bytes")

    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@attachments.command()
@click.argument("attachment_id", type=int)
@click.argument("output_path", type=click.Path())
@click.pass_context
def download(ctx: click.Context, attachment_id: int, output_path: str) -> None:
    """Download an attachment by ID."""
    try:
        client = get_client_from_env()

        click.echo(f"Downloading attachment {attachment_id}...")

        file_data = client.attachments.download_file(
            attachment_id=attachment_id, output_path=output_path
        )

        click.echo(f"✓ Successfully downloaded to: {output_path}")
        click.echo(f"  Size: {len(file_data)} bytes")

    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@attachments.command()
@click.argument("parent_type")
@click.argument("parent_id", type=int)
@click.option("--output", "-o", type=click.Choice(["json", "table"]), default="table")
@click.pass_context
def list(ctx: click.Context, parent_type: str, parent_id: int, output: str) -> None:
    """List attachments for an entity."""
    try:
        client = get_client_from_env()

        attachments = client.attachments.get_attachments_for_entity(
            parent_type=parent_type, parent_id=parent_id
        )

        if output == "json":
            output_data = [a.dict() for a in attachments]
            click.echo(json.dumps(output_data, indent=2))
        else:
            if attachments:
                click.echo(f"Attachments for {parent_type} {parent_id}:")
                for attachment in attachments:
                    click.echo(f"  ID: {attachment.id}")
                    click.echo(f"    Title: {attachment.title}")
                    click.echo(f"    File: {attachment.file_name}")
                    click.echo(f"    Size: {attachment.file_size} bytes")
                    click.echo(f"    Type: {attachment.content_type}")
                    click.echo("")
            else:
                click.echo(f"No attachments found for {parent_type} {parent_id}")

    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@attachments.command()
@click.argument("attachment_id", type=int)
@click.option("--confirm", is_flag=True, help="Skip confirmation prompt")
@click.pass_context
def delete_attachment(ctx: click.Context, attachment_id: int, confirm: bool) -> None:
    """Delete an attachment by ID."""
    try:
        client = get_client_from_env()

        # Get attachment info first
        attachment = client.attachments.get_attachment_info(attachment_id)
        if not attachment:
            click.echo(f"Attachment {attachment_id} not found")
            sys.exit(1)

        # Confirmation prompt
        if not confirm:
            if not click.confirm(
                f"Delete attachment '{attachment.title}' ({attachment.file_name})?"
            ):
                click.echo("Aborted.")
                return

        success = client.attachments.delete_attachment(attachment_id)

        if success:
            click.echo(f"✓ Successfully deleted attachment {attachment_id}")
        else:
            click.echo(f"✗ Failed to delete attachment {attachment_id}")
            sys.exit(1)

    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
