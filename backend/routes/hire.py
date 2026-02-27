"""POST /api/hire — orchestrate full employee onboarding with real tool calling."""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.db_models import AgentTask, HireRequest
from models.schemas import HireRequestCreate, HireRequestResponse
from agents.hr_agent import hr_agent
from agents.finance_agent import finance_agent
from agents.it_agent import it_agent
from agents.compliance_agent import compliance_agent
from agents.marketing_agent import marketing_agent
from integrations.openrouter import openrouter_client
from integrations.neo4j_client import neo4j_client

router = APIRouter()

HIRE_SYSTEM = """You are the backoffice.ai hiring orchestrator. You coordinate a multi-agent pipeline for employee onboarding.

Given a hire request, execute this pipeline IN ORDER:
1. Maya (HR Agent) — look up company salary band and HR policies via Senso
2. Sam (Finance Agent) — research market salary benchmarks via Tavily
3. Compare internal policy vs market data, adjust salary if needed with reasoning
4. Compliance Agent — check regulatory requirements for role + location
5. Alex (IT Agent) — set up benefits enrollment via Yutori (web portals)

After all agents complete, summarize:
- Final salary decision (and reasoning if adjusted)
- Compliance status
- Benefits enrollment status
- Any flags or recommendations

Be specific about WHAT each agent found and WHY decisions were made."""


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
    all_results = []

    # Run agents in sequence: HR → Finance → Compliance → IT
    agents = [
        ("Maya", hr_agent, "HR policy lookup"),
        ("Sam", finance_agent, "Salary benchmarking"),
        ("Compliance", compliance_agent, "Regulatory check"),
        ("Alex", it_agent, "Benefits enrollment"),
    ]

    for agent_name, agent, description in agents:
        try:
            # Log delegation to Neo4j
            try:
                await neo4j_client.log_delegation(
                    "Orchestrator", agent_name, description,
                    f"{description} for {request.employee_name} ({request.role}, ${request.salary:,.0f}, {request.location})",
                    hrid)
            except Exception:
                pass

            result = await agent.execute(task=description, context=context, hire_request_id=hrid)
            all_results.append({"agent": agent_name, "status": "completed", **result})

            task = AgentTask(
                hire_request_id=hire.id, agent_name=agent_name,
                tool_used=result.get("tool", "unknown"),
                input_data=json.dumps(context),
                output_data=json.dumps(result.get("result", {}), default=str)[:5000],
                status="completed",
                started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc))
            db.add(task)

        except Exception as e:
            all_results.append({"agent": agent_name, "status": "failed", "error": str(e)})
            task = AgentTask(
                hire_request_id=hire.id, agent_name=agent_name,
                tool_used="error", input_data=json.dumps(context),
                output_data=str(e), status="failed",
                started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc))
            db.add(task)

    # Generate final reasoning summary via LLM
    try:
        summary_resp = await openrouter_client.chat(
            messages=[
                {"role": "system", "content": HIRE_SYSTEM},
                {"role": "user", "content": f"""Hire request for {request.employee_name}:
- Role: {request.role}
- Department: {request.department}
- Proposed Salary: ${request.salary:,.0f}
- Location: {request.location}
- Start Date: {request.start_date}

Agent results:
{json.dumps(all_results, default=str)[:4000]}

Provide the final reasoning summary."""}
            ],
            max_tokens=800)
        reasoning = summary_resp["choices"][0]["message"]["content"]
    except Exception as e:
        reasoning = f"Pipeline completed with {len(all_results)} agent steps. Error generating summary: {e}"

    hire.status = "completed"
    hire.reasoning_summary = reasoning
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
