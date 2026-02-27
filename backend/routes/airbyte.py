"""Airbyte specialist routes — connector discovery, sync, and data access."""

from fastapi import APIRouter

from agents.airbyte_agent import airbyte_agent

router = APIRouter()


@router.get("/airbyte/connectors")
async def list_connectors():
    """List all available Airbyte connectors."""
    return await airbyte_agent.execute("list all connectors", {"action": "discover_connectors"})


@router.get("/airbyte/connectors/{system}")
async def discover_connector(system: str):
    """Discover connectors for a specific system."""
    return await airbyte_agent.execute(
        f"find connectors for {system}",
        {"action": "discover_connectors", "system": system})


@router.get("/airbyte/streams/{system}")
async def list_streams(system: str):
    """List available data streams for a system."""
    return await airbyte_agent.execute(
        f"list streams for {system}",
        {"action": "list_available_streams", "system": system})


@router.post("/airbyte/sync/employee")
async def sync_employee(data: dict):
    """Sync employee data to an external system via Airbyte."""
    destination = data.pop("destination", "notion")
    return await airbyte_agent.execute(
        f"sync employee to {destination}",
        {"action": "sync_employee_to_notion", "employee_data": data})


@router.post("/airbyte/read/{system}")
async def read_from_system(system: str, data: dict | None = None):
    """Read data from any external system."""
    data = data or {}
    return await airbyte_agent.execute(
        f"read data from {system}",
        {"action": "read_data", "system": system, "streams": data.get("streams", []), "config": data.get("config", {})})


@router.get("/airbyte/tools")
async def get_airbyte_tools():
    """Return the Airbyte agent's tool definitions for the orchestrator."""
    return {"tools": airbyte_agent.get_tools_for_orchestrator()}
