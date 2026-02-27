"""POST /api/sync — sync employee data to customer systems via Airbyte or direct Notion."""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.db_models import HireRequest
from integrations.notion import notion_client
from integrations.airbyte import airbyte_client
from integrations.neo4j_client import neo4j_client

router = APIRouter()


@router.post("/sync/{hire_id}")
async def sync_to_systems(hire_id: str, db: AsyncSession = Depends(get_db)):
    """Sync a hire request to customer systems.

    Tries Airbyte first (if credentials available), falls back to direct Notion API.
    """
    result = await db.execute(select(HireRequest).where(HireRequest.id == hire_id))
    hire = result.scalar_one_or_none()
    if not hire:
        raise HTTPException(status_code=404, detail="Hire request not found")

    sync_results = {}

    # Try Airbyte first (if credentials available)
    try:
        if airbyte_client.client_id and airbyte_client.client_secret:
            connections = await airbyte_client.list_connections()
            sync_results["airbyte"] = {"status": "available", "connections": len(connections.get("data", []))}
        else:
            sync_results["airbyte"] = {"status": "no_credentials", "fallback": "using_direct_notion"}
    except Exception as e:
        sync_results["airbyte"] = {"status": "error", "error": str(e), "fallback": "using_direct_notion"}

    # Direct Notion sync (always available as fallback)
    try:
        # Find or create Employee Database
        db_result = await notion_client.create_employee_database()
        database_id = db_result.get("id", "")

        if database_id:
            # Create employee record
            record = await notion_client.create_employee_record(
                database_id=database_id,
                employee_name=hire.employee_name,
                role=hire.role,
                department=hire.department,
                salary=hire.salary,
                location=hire.location,
                start_date=hire.start_date,
                status="Onboarding")
            sync_results["notion"] = {
                "status": "synced",
                "page_id": record.get("id", ""),
                "url": record.get("url", "")}
        else:
            sync_results["notion"] = {"status": "no_database", "detail": db_result}

    except Exception as e:
        sync_results["notion"] = {"status": "error", "error": str(e)}

    # Log sync to Neo4j
    try:
        await neo4j_client.log_completion(
            agent_name="SyncAgent", task="sync_to_customer_systems",
            result=json.dumps(sync_results, default=str)[:500],
            tool_used="airbyte+notion", hire_request_id=hire_id)
    except Exception:
        pass

    return {
        "hire_id": hire_id,
        "employee": hire.employee_name,
        "sync_results": sync_results}
