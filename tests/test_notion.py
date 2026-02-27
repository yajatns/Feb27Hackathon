"""Tests for Notion integration and sync route."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

HAS_NOTION = bool(os.getenv("NOTION_TOKEN"))


class TestNotionClientUnit:
    def test_client_has_methods(self):
        from integrations.notion import notion_client
        assert hasattr(notion_client, "search")
        assert hasattr(notion_client, "list_databases")
        assert hasattr(notion_client, "query_database")
        assert hasattr(notion_client, "create_page")
        assert hasattr(notion_client, "create_employee_record")
        assert hasattr(notion_client, "create_employee_database")

    def test_headers_include_version(self):
        from integrations.notion import notion_client
        headers = notion_client.headers
        assert "Notion-Version" in headers
        assert headers["Notion-Version"] == "2022-06-28"


class TestSyncRoute:
    def test_sync_route_registered(self):
        from main import app
        paths = [r.path for r in app.routes]
        assert "/api/sync/{hire_id}" in paths


@pytest.mark.skipif(not HAS_NOTION, reason="No Notion token")
@pytest.mark.asyncio
async def test_notion_search():
    from integrations.notion import notion_client
    result = await notion_client.search()
    assert isinstance(result, dict)
    assert "results" in result


@pytest.mark.skipif(not HAS_NOTION, reason="No Notion token")
@pytest.mark.asyncio
async def test_notion_list_databases():
    from integrations.notion import notion_client
    result = await notion_client.list_databases()
    assert isinstance(result, list)
