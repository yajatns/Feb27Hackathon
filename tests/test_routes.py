"""Unit tests for API routes using httpx AsyncClient."""

import pytest
from httpx import AsyncClient, ASGITransport

# We test the health endpoint which doesn't need DB
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


@pytest.mark.asyncio
async def test_health():
    """Test health endpoint returns ok."""
    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "backoffice.ai"


@pytest.mark.asyncio
async def test_query_endpoint_exists():
    """Test that /api/query route is registered."""
    from main import app
    routes = [r.path for r in app.routes]
    assert "/api/query" in routes


@pytest.mark.asyncio
async def test_hire_endpoint_exists():
    """Test that /api/hire route is registered."""
    from main import app
    routes = [r.path for r in app.routes]
    assert "/api/hire" in routes


@pytest.mark.asyncio
async def test_graph_endpoint_exists():
    """Test that /api/graph route is registered."""
    from main import app
    routes = [r.path for r in app.routes]
    assert "/api/graph" in routes


@pytest.mark.asyncio
async def test_status_endpoint_exists():
    """Test that /api/status route is registered."""
    from main import app
    routes = [r.path for r in app.routes]
    assert "/api/status" in routes


@pytest.mark.asyncio
async def test_websocket_endpoint_exists():
    """Test that /api/stream WebSocket route is registered."""
    from main import app
    routes = [r.path for r in app.routes]
    assert "/api/stream" in routes
