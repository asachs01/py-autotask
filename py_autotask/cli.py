"""
Command-line interface for py-autotask.

This module provides a CLI for common Autotask API operations,
allowing users to interact with the API from the command line.
"""

import json
import logging
import os
import sys
from typing import Any, Dict, Optional

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
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def get_client_from_env() -> AutotaskClient:
    """Create client from environment variables."""
    username = os.getenv('AUTOTASK_USERNAME')
    integration_code = os.getenv('AUTOTASK_INTEGRATION_CODE')
    secret = os.getenv('AUTOTASK_SECRET')
    api_url = os.getenv('AUTOTASK_API_URL')
    
    if not all([username, integration_code, secret]):
        click.echo("Error: Missing required environment variables.")
        click.echo("Please set: AUTOTASK_USERNAME, AUTOTASK_INTEGRATION_CODE, AUTOTASK_SECRET")
        sys.exit(1)
    
    return AutotaskClient.create(
        username=username,
        integration_code=integration_code,
        secret=secret,
        api_url=api_url
    )


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """py-autotask: Python client for Autotask REST API."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_logging(verbose)


@main.command()
@click.option('--username', '-u', help='API username')
@click.option('--integration-code', '-i', help='Integration code')
@click.option('--secret', '-s', help='API secret')
@click.option('--api-url', help='Override API URL')
@click.pass_context
def auth(
    ctx: click.Context,
    username: Optional[str],
    integration_code: Optional[str], 
    secret: Optional[str],
    api_url: Optional[str]
) -> None:
    """Test authentication and zone detection."""
    try:
        if username and integration_code and secret:
            client = AutotaskClient.create(
                username=username,
                integration_code=integration_code,
                secret=secret,
                api_url=api_url
            )
        else:
            client = get_client_from_env()
        
        # Test authentication by getting zone info
        zone_info = client.auth.zone_info
        if zone_info:
            click.echo(f"✓ Authentication successful!")
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
    pass


@get.command()
@click.argument('ticket_id', type=int)
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='json')
@click.pass_context
def ticket(ctx: click.Context, ticket_id: int, output: str) -> None:
    """Get a ticket by ID."""
    try:
        client = get_client_from_env()
        ticket_data = client.tickets.get(ticket_id)
        
        if ticket_data:
            if output == 'json':
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
@click.argument('company_id', type=int)
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='json')
@click.pass_context
def company(ctx: click.Context, company_id: int, output: str) -> None:
    """Get a company by ID."""
    try:
        client = get_client_from_env()
        company_data = client.companies.get(company_id)
        
        if company_data:
            if output == 'json':
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
    pass


@query.command()
@click.option('--filter', '-f', help='JSON filter string')
@click.option('--fields', help='Comma-separated list of fields to include')
@click.option('--max-records', type=int, help='Maximum records to return')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='json')
@click.pass_context
def tickets(
    ctx: click.Context,
    filter: Optional[str],
    fields: Optional[str],
    max_records: Optional[int],
    output: str
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
            include_fields = [f.strip() for f in fields.split(',')]
        
        response = client.tickets.query(
            filters=filters,
            include_fields=include_fields,
            max_records=max_records
        )
        
        if output == 'json':
            # Convert response to dict for JSON serialization
            result = {
                'items': response.items,
                'page_details': {
                    'count': response.page_details.count,
                    'request_count': response.page_details.request_count,
                    'next_page_url': response.page_details.next_page_url,
                    'prev_page_url': response.page_details.prev_page_url,
                }
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
@click.option('--filter', '-f', help='JSON filter string')
@click.option('--fields', help='Comma-separated list of fields to include')
@click.option('--max-records', type=int, help='Maximum records to return')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='json')
@click.pass_context
def companies(
    ctx: click.Context,
    filter: Optional[str],
    fields: Optional[str],
    max_records: Optional[int],
    output: str
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
            include_fields = [f.strip() for f in fields.split(',')]
        
        response = client.companies.query(
            filters=filters,
            include_fields=include_fields,
            max_records=max_records
        )
        
        if output == 'json':
            # Convert response to dict for JSON serialization
            result = {
                'items': response.items,
                'page_details': {
                    'count': response.page_details.count,
                    'request_count': response.page_details.request_count,
                    'next_page_url': response.page_details.next_page_url,
                    'prev_page_url': response.page_details.prev_page_url,
                }
            }
            click.echo(json.dumps(result, indent=2))
        else:
            # Simple table output
            click.echo(f"Found {len(response.items)} companies:")
            for item in response.items:
                click.echo(f"  ID: {item.get('id')} - {item.get('companyName', 'No name')}")
                
    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


@main.command()
@click.argument('entity')
@click.option('--output', '-o', type=click.Choice(['json', 'table']), default='json')
@click.pass_context
def info(ctx: click.Context, entity: str, output: str) -> None:
    """Get field information for an entity."""
    try:
        client = get_client_from_env()
        field_info = client.get_field_info(entity)
        
        if output == 'json':
            click.echo(json.dumps(field_info, indent=2))
        else:
            # Simple table output
            click.echo(f"Field information for {entity}:")
            fields = field_info.get('fields', [])
            for field in fields:
                click.echo(f"  {field.get('name', 'N/A')} ({field.get('dataType', 'N/A')})")
                
    except AutotaskError as e:
        click.echo(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 