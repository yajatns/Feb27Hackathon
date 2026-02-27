"""Tests for Airbyte Specialist Agent."""

import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))


class TestAirbyteAgent:
    def test_agent_imports(self):
        from agents.airbyte_agent import airbyte_agent
        assert airbyte_agent is not None
        assert airbyte_agent.name == "Aria"
        assert airbyte_agent.role == "Integration Specialist"

    def test_capabilities(self):
        from agents.airbyte_agent import AirbyteSpecialistAgent
        agent = AirbyteSpecialistAgent()
        assert "discover_connectors" in agent.CAPABILITIES
        assert "sync_employee_to_notion" in agent.CAPABILITIES
        assert "read_data" in agent.CAPABILITIES

    def test_classify_task_discover(self):
        from agents.airbyte_agent import AirbyteSpecialistAgent
        agent = AirbyteSpecialistAgent()
        assert agent._classify_task("find connectors for Stripe") == "discover_connectors"
        assert agent._classify_task("what connectors exist for Salesforce") == "discover_connectors"

    def test_classify_task_sync(self):
        from agents.airbyte_agent import AirbyteSpecialistAgent
        agent = AirbyteSpecialistAgent()
        assert agent._classify_task("sync employee data to Notion") == "sync_employee_to_notion"
        assert agent._classify_task("push to notion") == "sync_employee_to_notion"

    def test_classify_task_read(self):
        from agents.airbyte_agent import AirbyteSpecialistAgent
        agent = AirbyteSpecialistAgent()
        assert agent._classify_task("read data from Stripe") == "read_data"
        assert agent._classify_task("pull customer records") == "read_data"

    def test_known_connectors(self):
        from agents.airbyte_agent import AirbyteSpecialistAgent
        agent = AirbyteSpecialistAgent()
        assert "github" in agent.AGENT_CONNECTORS
        assert "stripe" in agent.AGENT_CONNECTORS
        assert "notion" in agent.PYAIRBYTE_SOURCES
        assert len(agent.PYAIRBYTE_SOURCES) >= 15

    def test_tools_for_orchestrator(self):
        from agents.airbyte_agent import AirbyteSpecialistAgent
        agent = AirbyteSpecialistAgent()
        tools = agent.get_tools_for_orchestrator()
        assert len(tools) == 4
        names = [t["function"]["name"] for t in tools]
        assert "airbyte_discover" in names
        assert "airbyte_sync_employee" in names
        assert "airbyte_read_data" in names
        assert "airbyte_list_connectors" in names


class TestAirbyteRoutes:
    def test_routes_registered(self):
        from main import app
        paths = [r.path for r in app.routes]
        assert "/api/airbyte/connectors" in paths
        assert "/api/airbyte/connectors/{system}" in paths
        assert "/api/airbyte/streams/{system}" in paths
        assert "/api/airbyte/sync/employee" in paths
        assert "/api/airbyte/tools" in paths


class TestConnectorManager:
    def test_manager_imports(self):
        from integrations.airbyte_connector import AirbyteConnectorManager
        mgr = AirbyteConnectorManager()
        assert mgr is not None

    def test_get_connector_type(self):
        from integrations.airbyte_connector import AirbyteConnectorManager
        mgr = AirbyteConnectorManager()
        assert mgr._get_connector_type("github") == "agent_native"
        assert mgr._get_connector_type("shopify") == "pyairbyte"

    def test_generate_pyairbyte_code(self):
        from integrations.airbyte_connector import AirbyteConnectorManager
        mgr = AirbyteConnectorManager()
        code = mgr._generate_pyairbyte_code("stripe", ["customers", "invoices"])
        assert "source-stripe" in code
        assert "customers" in code
