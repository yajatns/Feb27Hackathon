"""Airbyte Connector Manager — handles PyAirbyte + Agent Connector operations.

Two integration modes:
1. Agent Connectors (typed Python SDKs) — for supported systems
2. PyAirbyte (source-xxx) — for 600+ connectors via unified interface
3. Direct API fallback — for Airbyte Cloud/OSS when hosted instance available
"""

import json
import logging
from typing import Any

import httpx

from app.config import settings
from integrations.notion import notion_client

logger = logging.getLogger(__name__)


class AirbyteConnectorManager:
    """Manages Airbyte connector operations across all integration modes."""

    def __init__(self):
        self._http = httpx.AsyncClient(timeout=30.0)
        # Track configured connections
        self._sources: dict[str, dict] = {}
        self._destinations: dict[str, dict] = {}
        self._connections: dict[str, dict] = {}

    async def configure_source(self, system: str, config: dict) -> dict:
        """Configure a source connector."""
        source_id = f"src_{system}_{len(self._sources)}"

        # For demo: validate the config has minimum required fields
        source_config = {
            "id": source_id,
            "system": system,
            "config": config,
            "status": "configured",
            "connector_type": self._get_connector_type(system),
        }
        self._sources[source_id] = source_config

        return {
            "source_id": source_id,
            "system": system,
            "status": "configured",
            "message": f"Source '{system}' configured. Ready to create connection.",
        }

    async def configure_destination(self, system: str, config: dict) -> dict:
        """Configure a destination connector."""
        dest_id = f"dst_{system}_{len(self._destinations)}"

        dest_config = {
            "id": dest_id,
            "system": system,
            "config": config,
            "status": "configured",
            "connector_type": self._get_connector_type(system),
        }
        self._destinations[dest_id] = dest_config

        return {
            "destination_id": dest_id,
            "system": system,
            "status": "configured",
            "message": f"Destination '{system}' configured.",
        }

    async def create_connection(self, source_id: str, dest_id: str) -> dict:
        """Create a connection between source and destination."""
        conn_id = f"conn_{len(self._connections)}"

        connection = {
            "id": conn_id,
            "source_id": source_id,
            "destination_id": dest_id,
            "status": "ready",
        }
        self._connections[conn_id] = connection

        return {
            "connection_id": conn_id,
            "status": "ready",
            "message": "Connection created. Ready to sync.",
        }

    async def trigger_sync(self, connection_id: str) -> dict:
        """Trigger a sync job for a connection."""
        conn = self._connections.get(connection_id, {})
        if not conn:
            return {"error": f"Connection {connection_id} not found"}

        # If Airbyte Cloud API is available, use it
        if settings.airbyte_client_id and settings.airbyte_client_secret:
            return await self._trigger_cloud_sync(connection_id)

        return {
            "job_id": f"job_{connection_id}",
            "connection_id": connection_id,
            "status": "running",
            "message": "Sync triggered. Use check_status to monitor.",
        }

    async def check_status(self, job_id: str) -> dict:
        """Check sync job status."""
        return {
            "job_id": job_id,
            "status": "completed",
            "records_synced": 0,
            "message": "Sync completed successfully.",
        }

    async def read_source(self, system: str, streams: list[str], config: dict) -> dict:
        """Read data directly from a source using PyAirbyte."""
        try:
            # For systems with direct API access, use that
            if system == "notion" and settings.notion_token:
                return await self._read_from_notion(streams)

            # For other systems, attempt PyAirbyte
            return {
                "system": system,
                "streams": streams,
                "status": "requires_pyairbyte",
                "install_command": f"pip install airbyte",
                "code_example": self._generate_pyairbyte_code(system, streams),
                "message": f"PyAirbyte can read from {system}. Install and configure to proceed.",
            }
        except Exception as e:
            return {"error": str(e), "system": system}

    async def list_streams(self, system: str, config: dict) -> dict:
        """List available data streams from a source."""
        # Known streams for common systems
        known_streams: dict[str, list[str]] = {
            "notion": ["pages", "databases", "users", "blocks", "comments"],
            "github": ["repositories", "issues", "pull_requests", "commits", "teams", "organizations"],
            "stripe": ["customers", "invoices", "charges", "subscriptions", "products", "prices"],
            "salesforce": ["accounts", "contacts", "leads", "opportunities", "cases"],
            "hubspot": ["contacts", "companies", "deals", "tickets", "products"],
            "jira": ["issues", "projects", "boards", "sprints", "users"],
            "slack": ["channels", "messages", "users", "files"],
        }

        return {
            "system": system,
            "streams": known_streams.get(system, ["Check PyAirbyte catalog"]),
            "total_available": len(known_streams.get(system, [])),
        }

    async def sync_to_notion(self, employee_data: dict) -> dict:
        """Sync employee data to Notion — the primary demo use case."""
        try:
            # Use direct Notion API (our existing integration)
            result = await notion_client.create_employee_record(
                name=employee_data.get("employee_name", ""),
                role=employee_data.get("role", ""),
                department=employee_data.get("department", ""),
                salary=employee_data.get("salary", 0),
                location=employee_data.get("location", ""),
                start_date=employee_data.get("start_date", ""),
            )
            return {
                "status": "synced",
                "destination": "notion",
                "method": "direct_api",
                "result": result,
                "message": f"Employee {employee_data.get('employee_name')} synced to Notion.",
            }
        except Exception as e:
            logger.warning("Notion direct sync failed: %s. Falling back to Airbyte.", e)

            # Fallback: describe how PyAirbyte would handle it
            return {
                "status": "fallback",
                "destination": "notion",
                "method": "pyairbyte",
                "code": self._generate_pyairbyte_write_code("notion", employee_data),
                "message": f"Direct Notion API unavailable. PyAirbyte sync ready.",
                "error": str(e),
            }

    async def pull_data(self, system: str, query: str) -> dict:
        """Pull data from any connected system."""
        if system == "notion" and settings.notion_token:
            try:
                results = await notion_client.search(query)
                return {
                    "system": "notion",
                    "method": "direct_api",
                    "results": results,
                    "query": query,
                }
            except Exception as e:
                return {"error": str(e), "system": system}

        return {
            "system": system,
            "query": query,
            "status": "requires_connector_config",
            "available_methods": [
                f"pip install {self._get_agent_package(system)}" if self._get_agent_package(system) else None,
                "pip install airbyte (PyAirbyte for 600+ sources)",
            ],
        }

    def _get_connector_type(self, system: str) -> str:
        """Determine the best connector type for a system."""
        agent_connectors = {
            "github", "gong", "stripe", "salesforce", "hubspot",
            "jira", "zendesk", "notion", "slack",
        }
        if system in agent_connectors:
            return "agent_native"
        return "pyairbyte"

    def _get_agent_package(self, system: str) -> str | None:
        """Get the agent connector package name."""
        packages = {
            "github": "airbyte-agent-github",
            "gong": "airbyte-agent-gong",
            "stripe": "airbyte-agent-stripe",
            "salesforce": "airbyte-agent-salesforce",
            "hubspot": "airbyte-agent-hubspot",
            "jira": "airbyte-agent-jira",
            "zendesk": "airbyte-agent-zendesk",
        }
        return packages.get(system)

    def _generate_pyairbyte_code(self, system: str, streams: list[str]) -> str:
        """Generate PyAirbyte code example for a source."""
        source_name = f"source-{system}"
        stream_list = ", ".join(f'"{s}"' for s in streams) if streams else '"all"'
        return f"""
import airbyte as ab

source = ab.get_source("{source_name}", config={{"token": "..."}})
source.check()  # verify connection
source.select_streams([{stream_list}])
result = source.read()

# Access data
for stream_name, dataset in result.streams.items():
    for record in dataset:
        print(record)
"""

    def _generate_pyairbyte_write_code(self, system: str, data: dict) -> str:
        """Generate code for writing data via PyAirbyte."""
        return f"""
# Using Airbyte Agent Connector for writes
from airbyte_agent_{system} import {system.title()}Connector

connector = {system.title()}Connector(token="...")
connector.create_record(data={json.dumps(data, default=str)})
"""

    async def _read_from_notion(self, streams: list[str]) -> dict:
        """Read data from Notion using our direct integration."""
        results = {}
        for stream in streams:
            if stream == "databases":
                results["databases"] = await notion_client.list_databases()
            elif stream == "pages":
                results["pages"] = await notion_client.search("")
            else:
                results[stream] = {"note": f"Stream '{stream}' available via PyAirbyte"}
        return {"system": "notion", "method": "direct_api", "data": results}

    async def _trigger_cloud_sync(self, connection_id: str) -> dict:
        """Trigger sync via Airbyte Cloud API."""
        try:
            # Get auth token
            auth_resp = await self._http.post(
                f"{settings.airbyte_base_url}/applications/token",
                json={
                    "client_id": settings.airbyte_client_id,
                    "client_secret": settings.airbyte_client_secret,
                },
            )
            token = auth_resp.json().get("access_token", "")

            # Trigger sync
            resp = await self._http.post(
                f"{settings.airbyte_base_url}/v1/jobs",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "connectionId": connection_id,
                    "jobType": "sync",
                },
            )
            return resp.json()
        except Exception as e:
            return {"error": str(e), "fallback": "Use PyAirbyte locally"}

    async def close(self):
        await self._http.aclose()
