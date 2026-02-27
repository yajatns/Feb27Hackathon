"""Tests for orchestrator function calling and override routes."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


class TestOrchestrator:
    def test_tools_defined(self):
        """Verify all 4 tool definitions exist in query router."""
        from routes.query import TOOLS
        tool_names = {t["function"]["name"] for t in TOOLS}
        assert tool_names == {"senso_search", "tavily_search", "reka_analyze", "yutori_browse"}

    def test_tool_params(self):
        """Each tool should have required parameters."""
        from routes.query import TOOLS
        for tool in TOOLS:
            fn = tool["function"]
            assert "parameters" in fn
            assert "required" in fn["parameters"]
            assert len(fn["parameters"]["required"]) > 0

    def test_system_prompt_mentions_all_tools(self):
        """System prompt should reference all tools."""
        from routes.query import SYSTEM_PROMPT
        for name in ["senso_search", "tavily_search", "reka_analyze", "yutori_browse"]:
            assert name in SYSTEM_PROMPT

    def test_hire_system_prompt(self):
        """Hire system prompt should mention all agents."""
        from routes.hire import HIRE_SYSTEM
        for name in ["Maya", "Sam", "Compliance", "Alex"]:
            assert name in HIRE_SYSTEM


class TestOverrideRoute:
    def test_override_route_registered(self):
        """Override route should be registered."""
        from main import app
        routes = [r.path for r in app.routes]
        assert "/api/override" in routes


@pytest.mark.asyncio
async def test_execute_tool_unknown():
    """Unknown tool should return error."""
    from routes.query import _execute_tool
    result = await _execute_tool("unknown_tool", {})
    assert "error" in result
