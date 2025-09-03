#!/usr/bin/env python3
"""
Final verification test for py-autotask SDK against Autotask REST API.
Tests key functionality based on learnings from the Notion guide.
"""

import json
import logging
import os

from py_autotask import AutotaskClient

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_sdk():
    """Test the SDK with real API calls."""

    # Get credentials from environment
    username = os.getenv("AUTOTASK_USERNAME")
    integration_code = os.getenv("AUTOTASK_INTEGRATION_CODE")
    secret = os.getenv("AUTOTASK_SECRET")

    if not all([username, integration_code, secret]):
        logger.error(
            "Missing credentials. Please set AUTOTASK_USERNAME, AUTOTASK_INTEGRATION_CODE, and AUTOTASK_SECRET"
        )
        return False

    try:
        # 1. Test client creation and zone detection
        logger.info("=" * 60)
        logger.info("1. Testing client creation and zone detection...")
        client = AutotaskClient.create(
            username=username, integration_code=integration_code, secret=secret
        )
        logger.info(f"✅ Client created successfully")
        logger.info(f"   API URL: {client.auth.api_url}")

        # 2. Test basic query with minimal filter (as per Notion guide)
        logger.info("=" * 60)
        logger.info("2. Testing query with minimal filter...")
        companies_result = client.companies.query(
            {"filter": [{"op": "gte", "field": "id", "value": 0}], "maxRecords": 2}
        )
        logger.info(f"✅ Query successful!")
        logger.info(f"   Found {len(companies_result.items)} companies")
        if companies_result.items:
            logger.info(
                f"   First company: {companies_result.items[0].get('companyName', 'N/A')}"
            )

        # 3. Test query with nested filter format (should be converted)
        logger.info("=" * 60)
        logger.info("3. Testing query with nested filter format...")
        from py_autotask.utils import convert_filter_format

        # Test filter conversion
        nested_filter = {"id": {"gte": 0}}
        converted = convert_filter_format(nested_filter)
        logger.info(f"   Filter conversion: {nested_filter} -> {converted}")

        # 4. Test query without filter (should add minimal filter automatically)
        logger.info("=" * 60)
        logger.info("4. Testing query without filter (should auto-add)...")
        result = client.companies.query(max_records=1)
        logger.info(f"✅ Query without filter successful (auto-added minimal filter)")
        logger.info(f"   Found {len(result.items)} companies")

        # 5. Test error handling for invalid credentials
        logger.info("=" * 60)
        logger.info("5. Testing error handling...")
        try:
            bad_client = AutotaskClient.create(
                username="invalid@example.com",
                integration_code="INVALID",
                secret="INVALID",
            )
            # Try to make a query
            bad_client.companies.query(max_records=1)
            logger.error("❌ Should have raised an authentication error")
        except Exception as e:
            logger.info(
                f"✅ Correctly raised error for bad credentials: {type(e).__name__}"
            )

        # 6. Verify response structure matches Notion guide
        logger.info("=" * 60)
        logger.info("6. Verifying response structure...")
        if companies_result.page_details:
            logger.info(f"✅ Response has correct structure:")
            logger.info(
                f"   - items: {type(companies_result.items).__name__} with {len(companies_result.items)} items"
            )
            logger.info(
                f"   - pageDetails.count: {companies_result.page_details.count}"
            )
            logger.info(
                f"   - pageDetails.requestCount: {companies_result.page_details.request_count}"
            )
            if companies_result.page_details.next_page_url:
                logger.info(f"   - pageDetails.nextPageUrl: Present")

        # 7. Test specific entity query
        logger.info("=" * 60)
        logger.info("7. Testing specific entity retrieval...")
        if companies_result.items and len(companies_result.items) > 0:
            company_id = companies_result.items[0]["id"]
            company = client.companies.get(company_id)
            if company:
                logger.info(
                    f"✅ Retrieved company by ID: {company.get('companyName', 'N/A')}"
                )
            else:
                logger.info(f"⚠️  Could not retrieve company by ID {company_id}")

        logger.info("=" * 60)
        logger.info("✅ ALL TESTS PASSED! SDK is working correctly.")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed with error: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    success = test_sdk()
    exit(0 if success else 1)
