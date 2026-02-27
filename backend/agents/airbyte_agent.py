"""Airbyte Specialist Agent — universal connector that handles ALL external system integrations.

The orchestrator says "sync employee data to Notion" or "pull sales data from Stripe" 
and this agent handles everything: discover connectors, configure, connect, sync.

Uses Airbyte Agent Connectors (standalone Python packages) — no hosted Airbyte needed.
Supports 600+ connectors via PyAirbyte + agent-native connectors for typed access.
"""

import json
import logging
from typing import Any

from agents.base import BaseAgent
from integrations.airbyte_connector import AirbyteConnectorManager
from integrations.neo4j_client import neo4j_client

logger = logging.getLogger(__name__)


class AirbyteSpecialistAgent(BaseAgent):
    """Universal connector agent — bridges the orchestrator to ANY external system."""

    name = "Aria"
    role = "Integration Specialist"
    description = (
        "Airbyte-powered agent that connects to 600+ SaaS systems. "
        "Handles connector discovery, configuration, authentication, "
        "data sync, and monitoring. The orchestrator's bridge to the outside world."
    )

    CAPABILITIES = [
        "discover_connectors",      # Find available connectors for a system
        "configure_source",         # Set up a source connector
        "configure_destination",    # Set up a destination connector
        "create_connection",        # Link source → destination
        "trigger_sync",             # Run a sync job
        "check_sync_status",        # Monitor sync progress
        "read_data",                # Pull data from a source directly
        "list_available_streams",   # Show what data streams a source has
        "sync_employee_to_notion",  # High-level: push employee data to Notion
        "pull_from_system",         # High-level: read data from any connected system
    ]

    # Known connector packages (pip installable)
    AGENT_CONNECTORS = {
        "github": "airbyte-agent-github",
        "gong": "airbyte-agent-gong",
        "stripe": "airbyte-agent-stripe",
        "salesforce": "airbyte-agent-salesforce",
        "hubspot": "airbyte-agent-hubspot",
        "jira": "airbyte-agent-jira",
        "zendesk": "airbyte-agent-zendesk",
        "notion": "airbyte-agent-notion",
        "slack": "airbyte-agent-slack",
        "google-sheets": "airbyte-agent-google-sheets",
        "postgres": "airbyte-agent-postgres",
        "mysql": "airbyte-agent-mysql",
        "mongodb": "airbyte-agent-mongodb",
    }

    # PyAirbyte source connectors (600+)
    PYAIRBYTE_SOURCES = {
        "notion": "source-notion",
        "github": "source-github",
        "stripe": "source-stripe",
        "salesforce": "source-salesforce",
        "hubspot": "source-hubspot",
        "jira": "source-jira-cloud",
        "zendesk": "source-zendesk-support",
        "slack": "source-slack",
        "google-sheets": "source-google-sheets",
        "postgres": "source-postgres",
        "mysql": "source-mysql",
        "mongodb": "source-mongodb-v2",
        "shopify": "source-shopify",
        "intercom": "source-intercom",
        "airtable": "source-airtable",
        "asana": "source-asana",
        "confluence": "source-confluence",
        "linear": "source-linear",
        "mailchimp": "source-mailchimp",
        "twilio": "source-twilio",
    }

    def __init__(self):
        self.connector_manager = AirbyteConnectorManager()

    async def execute(self, task: str, context: dict[str, Any] | None = None) -> dict:
        """Execute an Airbyte integration task."""
        context = context or {}
        action = context.get("action", self._classify_task(task))

        result = await self._dispatch(action, task, context)

        # Log to Neo4j
        try:
            await neo4j_client.log_completion(
                agent_name=self.name,
                task=f"airbyte_{action}",
                result=json.dumps(result, default=str)[:500],
                tool_used="airbyte",
                hire_request_id=context.get("hire_request_id", ""))
        except Exception:
            pass

        return result

    def _classify_task(self, task: str) -> str:
        """Classify natural language task into an action."""
        task_lower = task.lower()
        if any(w in task_lower for w in ["discover", "find", "search", "what connector"]):
            return "discover_connectors"
        if any(w in task_lower for w in ["configure source", "set up source", "connect to"]):
            return "configure_source"
        if any(w in task_lower for w in ["configure dest", "set up dest"]):
            return "configure_destination"
        if any(w in task_lower for w in ["sync employee", "push to notion", "create employee"]):
            return "sync_employee_to_notion"
        if any(w in task_lower for w in ["sync", "trigger", "run sync"]):
            return "trigger_sync"
        if any(w in task_lower for w in ["status", "progress", "check"]):
            return "check_sync_status"
        if any(w in task_lower for w in ["read", "pull", "fetch", "get data"]):
            return "read_data"
        if any(w in task_lower for w in ["streams", "tables", "collections"]):
            return "list_available_streams"
        return "discover_connectors"

    async def _dispatch(self, action: str, task: str, context: dict) -> dict:
        """Route to the right handler."""
        handlers = {
            "discover_connectors": self._discover_connectors,
            "configure_source": self._configure_source,
            "configure_destination": self._configure_destination,
            "create_connection": self._create_connection,
            "trigger_sync": self._trigger_sync,
            "check_sync_status": self._check_sync_status,
            "read_data": self._read_data,
            "list_available_streams": self._list_streams,
            "sync_employee_to_notion": self._sync_employee_to_notion,
            "pull_from_system": self._pull_from_system,
        }
        handler = handlers.get(action, self._discover_connectors)
        return await handler(task, context)

    async def _discover_connectors(self, task: str, context: dict) -> dict:
        """Find available connectors for a given system."""
        system = context.get("system", "")
        if not system:
            # Extract system name from task
            for name in self.PYAIRBYTE_SOURCES:
                if name in task.lower():
                    system = name
                    break

        agent_connector = self.AGENT_CONNECTORS.get(system)
        pyairbyte_source = self.PYAIRBYTE_SOURCES.get(system)

        return {
            "system": system or "all",
            "agent_connector": agent_connector,
            "pyairbyte_source": pyairbyte_source,
            "available_agent_connectors": list(self.AGENT_CONNECTORS.keys()),
            "available_pyairbyte_sources": list(self.PYAIRBYTE_SOURCES.keys()),
            "total_connectors": "600+",
            "recommendation": (
                f"Use agent connector '{agent_connector}' for typed access"
                if agent_connector
                else f"Use PyAirbyte source '{pyairbyte_source}' for data sync"
                if pyairbyte_source
                else "Search PyAirbyte catalog for this system"
            ),
        }

    async def _configure_source(self, task: str, context: dict) -> dict:
        """Configure a source connector."""
        system = context.get("system", "notion")
        config = context.get("config", {})
        return await self.connector_manager.configure_source(system, config)

    async def _configure_destination(self, task: str, context: dict) -> dict:
        """Configure a destination connector."""
        system = context.get("system", "")
        config = context.get("config", {})
        return await self.connector_manager.configure_destination(system, config)

    async def _create_connection(self, task: str, context: dict) -> dict:
        """Create a source → destination connection."""
        source = context.get("source", "")
        destination = context.get("destination", "")
        return await self.connector_manager.create_connection(source, destination)

    async def _trigger_sync(self, task: str, context: dict) -> dict:
        """Trigger a sync job."""
        connection_id = context.get("connection_id", "")
        return await self.connector_manager.trigger_sync(connection_id)

    async def _check_sync_status(self, task: str, context: dict) -> dict:
        """Check sync job status."""
        job_id = context.get("job_id", "")
        return await self.connector_manager.check_status(job_id)

    async def _read_data(self, task: str, context: dict) -> dict:
        """Read data directly from a source."""
        system = context.get("system", "")
        streams = context.get("streams", [])
        config = context.get("config", {})
        return await self.connector_manager.read_source(system, streams, config)

    async def _list_streams(self, task: str, context: dict) -> dict:
        """List available data streams from a source."""
        system = context.get("system", "")
        config = context.get("config", {})
        return await self.connector_manager.list_streams(system, config)

    async def _sync_employee_to_notion(self, task: str, context: dict) -> dict:
        """High-level: sync employee data to Notion workspace."""
        employee_data = context.get("employee_data", {})
        return await self.connector_manager.sync_to_notion(employee_data)

    async def _pull_from_system(self, task: str, context: dict) -> dict:
        """High-level: pull data from any connected system."""
        system = context.get("system", "")
        query = context.get("query", task)
        return await self.connector_manager.pull_data(system, query)

    def get_tools_for_orchestrator(self) -> list[dict]:
        """Return tool definitions for the OpenRouter function calling loop."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "airbyte_discover",
                    "description": "Find available Airbyte connectors for a given system (e.g., Notion, Stripe, Salesforce). Returns connector packages and setup instructions.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "system": {"type": "string", "description": "System name to find connectors for"}
                        },
                        "required": ["system"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "airbyte_sync_employee",
                    "description": "Sync employee data to an external system (Notion, Salesforce, etc.) via Airbyte connectors.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "employee_name": {"type": "string"},
                            "role": {"type": "string"},
                            "department": {"type": "string"},
                            "salary": {"type": "number"},
                            "destination": {"type": "string", "description": "Target system (notion, salesforce, etc.)"},
                        },
                        "required": ["employee_name", "destination"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "airbyte_read_data",
                    "description": "Read data from any external system via Airbyte (600+ connectors). Use for pulling CRM data, analytics, etc.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "system": {"type": "string", "description": "Source system (stripe, hubspot, jira, etc.)"},
                            "streams": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Data streams to read (e.g., ['customers', 'invoices'])",
                            },
                        },
                        "required": ["system"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "airbyte_list_connectors",
                    "description": "List all available Airbyte connectors and their categories.",
                    "parameters": {"type": "object", "properties": {}},
                },
            },
        ]


# Singleton
airbyte_agent = AirbyteSpecialistAgent()
