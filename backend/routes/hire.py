"""POST /api/hire — orchestrate full employee onboarding with autonomous AI agents."""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.db_models import AgentTask, HireRequest
from models.schemas import HireRequestCreate, HireRequestResponse
from agents.orchestrator import orchestrate_hire

router = APIRouter()


@router.post("/hire", response_model=HireRequestResponse)
async def create_hire_request(request: HireRequestCreate, db: AsyncSession = Depends(get_db)):
    """Create a new hire request and run the autonomous agent pipeline.

    The Orchestrator Agent (LLM) decides which specialist agents to invoke.
    Each specialist agent is also an LLM that reasons about its task and
    selects which tools to call. This is multi-agent A2A communication.
    """
    hire = HireRequest(
        employee_name=request.employee_name, role=request.role,
        department=request.department, salary=request.salary,
        location=request.location, start_date=request.start_date, status="processing")
    db.add(hire)
    await db.flush()

    context = request.model_dump()
    hrid = str(hire.id)

    try:
        # Run the autonomous orchestrator — it delegates to specialist agents
        result = await orchestrate_hire(context=context, hire_request_id=hrid)

        # Store each agent's work as a task record
        for delegation in result.get("delegations", []):
            task = AgentTask(
                hire_request_id=hire.id,
                agent_name=delegation["agent"],
                tool_used=", ".join(delegation.get("tools_used", ["reasoning"])),
                input_data=json.dumps({"task": delegation["task"]}),
                output_data=delegation.get("reasoning", "")[:5000],
                status="completed",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc))
            db.add(task)

        hire.status = "completed"
        hire.reasoning_summary = result.get("orchestrator_reasoning", "Pipeline completed.")

    except Exception as e:
        hire.status = "failed"
        hire.reasoning_summary = f"Pipeline error: {str(e)}"

    await db.flush()

    stmt = select(HireRequest).where(HireRequest.id == hire.id)
    db_result = await db.execute(stmt)
    return db_result.scalar_one()


@router.get("/hire/{hire_id}", response_model=HireRequestResponse)
async def get_hire_request(hire_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HireRequest).where(HireRequest.id == hire_id))
    hire = result.scalar_one_or_none()
    if not hire:
        raise HTTPException(status_code=404, detail="Hire request not found")
    return hire


@router.get("/hires", response_model=list[HireRequestResponse])
async def list_hire_requests(limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(HireRequest).order_by(HireRequest.created_at.desc()).limit(limit))
    return result.scalars().all()
