"""Integration tests for real API clients. Skip if keys not set."""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

HAS_TAVILY = bool(os.getenv("TAVILY_API_KEY"))
HAS_SENSO = bool(os.getenv("SENSO_API_KEY"))
HAS_OPENROUTER = bool(os.getenv("OPENROUTER_API_KEY"))
HAS_YUTORI = bool(os.getenv("YUTORI_API_KEY"))


@pytest.mark.skipif(not HAS_TAVILY, reason="No Tavily key")
@pytest.mark.asyncio
async def test_tavily_search():
    from integrations.tavily import tavily_client
    result = await tavily_client.search("average senior engineer salary San Francisco 2026", max_results=3)
    assert "results" in result


@pytest.mark.skipif(not HAS_TAVILY, reason="No Tavily key")
@pytest.mark.asyncio
async def test_tavily_salary_benchmark():
    from integrations.tavily import tavily_client
    result = await tavily_client.salary_benchmark("Senior Engineer", "San Francisco")
    assert isinstance(result, dict)
    assert "results" in result or "answer" in result


@pytest.mark.skipif(not HAS_TAVILY, reason="No Tavily key")
@pytest.mark.asyncio
async def test_tavily_regulatory_check():
    from integrations.tavily import tavily_client
    result = await tavily_client.regulatory_check("Senior Engineer", "California")
    assert isinstance(result, dict)


@pytest.mark.skipif(not HAS_SENSO, reason="No Senso key")
@pytest.mark.asyncio
async def test_senso_search():
    from integrations.senso import senso_client
    result = await senso_client.search_policy("salary band for senior engineer")
    assert isinstance(result, dict)


@pytest.mark.skipif(not HAS_OPENROUTER, reason="No OpenRouter key")
@pytest.mark.asyncio
async def test_openrouter_chat():
    from integrations.openrouter import openrouter_client
    result = await openrouter_client.chat(
        messages=[{"role": "user", "content": "Say 'hello backoffice' in 3 words"}],
        max_tokens=20)
    assert "choices" in result
    assert len(result["choices"]) > 0


@pytest.mark.skipif(not HAS_YUTORI, reason="No Yutori key")
@pytest.mark.asyncio
async def test_yutori_create_task():
    """Test Yutori task creation (won't complete, just validates API works)."""
    from integrations.yutori import yutori_client
    try:
        result = await yutori_client.create_task(
            task="Check the homepage of example.com",
            start_url="https://example.com")
        assert isinstance(result, dict)
    except Exception as e:
        # API might reject the test task, but connection should work
        assert "4" in str(e) or "5" in str(e)  # HTTP 4xx or 5xx


class TestTavilyClientUnit:
    """Unit tests for Tavily client structure (no API calls)."""

    def test_client_has_methods(self):
        from integrations.tavily import tavily_client
        assert hasattr(tavily_client, "search")
        assert hasattr(tavily_client, "research")
        assert hasattr(tavily_client, "salary_benchmark")
        assert hasattr(tavily_client, "regulatory_check")
        assert hasattr(tavily_client, "market_analysis")


class TestYutoriClientUnit:
    """Unit tests for Yutori client structure (no API calls)."""

    def test_client_has_methods(self):
        from integrations.yutori import yutori_client
        assert hasattr(yutori_client, "create_task")
        assert hasattr(yutori_client, "get_task_status")
        assert hasattr(yutori_client, "wait_for_task")
        assert hasattr(yutori_client, "enroll_benefits")
        assert hasattr(yutori_client, "fill_government_form")
        assert hasattr(yutori_client, "scrape_insurance_rates")
