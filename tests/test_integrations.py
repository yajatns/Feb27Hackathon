"""Integration tests for real API clients. Skip if keys not set."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

SKIP_NO_KEY = pytest.mark.skipif(
    not os.getenv("TAVILY_API_KEY"), reason="No API keys configured")


@SKIP_NO_KEY
@pytest.mark.asyncio
async def test_tavily_search():
    """Test Tavily search with real API."""
    from integrations.tavily import tavily_client
    result = await tavily_client.search("average senior engineer salary San Francisco 2026", max_results=3)
    assert "results" in result or "answer" in result


@pytest.mark.skipif(not os.getenv("SENSO_API_KEY"), reason="No Senso key")
@pytest.mark.asyncio
async def test_senso_search():
    """Test Senso policy search with real API."""
    from integrations.senso import senso_client
    result = await senso_client.search_policy("salary band for senior engineer")
    assert isinstance(result, dict)


@pytest.mark.skipif(not os.getenv("OPENROUTER_API_KEY"), reason="No OpenRouter key")
@pytest.mark.asyncio
async def test_openrouter_chat():
    """Test OpenRouter chat with real API."""
    from integrations.openrouter import openrouter_client
    result = await openrouter_client.chat(
        messages=[{"role": "user", "content": "Say 'hello backoffice' in 3 words"}],
        max_tokens=20)
    assert "choices" in result
    assert len(result["choices"]) > 0
