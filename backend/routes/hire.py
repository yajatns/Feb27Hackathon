"""POST /api/hire — orchestrate full employee onboarding."""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.db_models import AgentTask, HireRequest
from models.schemas import HireRequestCreate, HireRequestResponse
from agents.hr_agent import hr_agent
from agents.finance_agent import finance_agent
from agents.it_agent import it_agent
from agents.compliance_agent import compliance_agent
from integrations.neo4j_client import neo4j_client

router = APIRouter()


@router.post("/hire", response_model=HireRequestResponse)
async def create_hire_request(request: HireRequestCreate, db: AsyncSession = Depends(get_db)):
    """Create a new hire request and run the full agent pipeline."""
    hire = HireRequest(
        employee_name=request.employee_name, role=request.role,
        department=request.department, salary=request.salary,
        location=request.location, start_date=request.start_date, status="processing")
    db.add(hire)
    await db.flush()

    context = request.model_dump()
    hrid = str(hire.id)
    results = []

    # Run agents in sequence: HR → Finance → Compliance → IT
    agents = [
        ("Maya", hr_agent, "Policy lookup"),
        ("Sam", finance_agent, "Salary benchmark"),
        ("Compliance", compliance_agent, "Regulatory check"),
        ("Alex", it_agent, "Benefits enrollment"),
    ]

    for agent_name, agent, description in agents:
        try:
            # Log delegation
            try:
                await neo4j_client.log_delegation("Orchestrator", agent_name, description,
                                                    f"Running {description} for {request.employee_name}", hrid)
            except Exception:
                pass

            result = await agent.execute(task=description, context=context, hire_request_id=hrid)
            results.append(result)

            task = AgentTask(
                hire_request_id=hire.id, agent_name=agent_name,
                tool_used=result.get("tool", "unknown"),
                input_data=json.dumps(context),
                output_data=json.dumps(result.get("result", {}), default=str)[:5000],
                status="completed",
                started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc))
            db.add(task)
        except Exception as e:
            task = AgentTask(
                hire_request_id=hire.id, agent_name=agent_name,
                tool_used="error", input_data=json.dumps(context),
                output_data=str(e), status="failed",
                started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc))
            db.add(task)

    hire.status = "completed"
    hire.reasoning_summary = f"Processed {len(results)} agent steps for {request.employee_name}"
    await db.flush()

    stmt = select(HireRequest).where(HireRequest.id == hire.id)
    result = await db.execute(stmt)
    return result.scalar_one()


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
