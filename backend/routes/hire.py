"""POST /api/hire — AI Orchestrator agent coordinates specialist agents for hiring."""

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
from integrations.openrouter import openrouter_client
from integrations.neo4j_client import neo4j_client

router = APIRouter()

# The orchestrator is itself an AI agent — it reasons about what to do
ORCHESTRATOR_PERSONA = """You are the backoffice.ai Orchestrator — an AI agent that coordinates specialist agents to handle business operations.

You have a team of specialist AI agents, each with their own tools and expertise:
- **Maya** (HR Specialist): Searches company policies and salary bands via Senso
- **Sam** (Finance Analyst): Researches market salary data via Tavily deep search
- **Compliance Officer**: Checks labor laws and internal compliance via Tavily + Senso
- **Alex** (IT Operations): Provisions accounts and enrolls benefits via Yutori portal automation
- **Aria** (Integration Specialist): Connects to 600+ SaaS systems via Airbyte

For each hire request, you coordinate the team:
1. Dispatch each specialist to their task
2. Review their findings
3. Synthesize a final recommendation with clear reasoning

You are NOT just running scripts — you are an AI making decisions about how to onboard an employee."""


@router.post("/hire", response_model=HireRequestResponse)
async def create_hire_request(request: HireRequestCreate, db: AsyncSession = Depends(get_db)):
    """Create a new hire request — the AI orchestrator coordinates all specialist agents."""
    hire = HireRequest(
        employee_name=request.employee_name, role=request.role,
        department=request.department, salary=request.salary,
        location=request.location, start_date=request.start_date, status="processing")
    db.add(hire)
    await db.flush()

    context = request.model_dump()
    hrid = str(hire.id)
    agent_responses = []

    # Each specialist agent is an LLM that reasons about its task
    specialists = [
        ("Maya", hr_agent, f"Look up company HR policies and salary bands for hiring a {request.role} in {request.department} at {request.location}. The proposed salary is ${request.salary:,.0f}. Determine if this fits within our policy."),
        ("Sam", finance_agent, f"Research current market salary data for a {request.role} in {request.location}. The proposed salary is ${request.salary:,.0f}. Is this competitive? Provide data-backed analysis."),
        ("Compliance", compliance_agent, f"Check regulatory compliance requirements for hiring a {request.role} in {request.location} starting {request.start_date}. What labor laws, benefits requirements, and compliance steps apply?"),
        ("Alex", it_agent, f"Set up benefits enrollment and account provisioning for {request.employee_name}, starting {request.start_date} in {request.location}. Provision health insurance, 401k, and IT accounts."),
    ]

    for agent_name, agent, task_description in specialists:
        try:
            # Log delegation in Neo4j
            try:
                if neo4j_client._driver is None:
                    await neo4j_client.connect()
                await neo4j_client.log_delegation(
                    "Orchestrator", agent_name, task_description[:100],
                    f"Orchestrator dispatched {agent_name} for {request.employee_name}",
                    hrid)
            except Exception:
                pass

            # Agent reasons using LLM + tools
            result = await agent.execute(task=task_description, context=context, hire_request_id=hrid)
            agent_responses.append(result)

            # Log completion in Neo4j
            try:
                await neo4j_client.log_completion(
                    agent_name=agent_name,
                    task=task_description[:100],
                    result=result.get("reasoning", "")[:500],
                    tool_used=",".join(t["tool"] for t in result.get("tool_calls_made", [])) or "reasoning",
                    hire_request_id=hrid)
            except Exception:
                pass

            # Store in DB
            task = AgentTask(
                hire_request_id=hire.id, agent_name=agent_name,
                tool_used=",".join(t["tool"] for t in result.get("tool_calls_made", [])) or "llm_reasoning",
                input_data=task_description,
                output_data=json.dumps(result, default=str)[:5000],
                status="completed",
                started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc))
            db.add(task)

        except Exception as e:
            agent_responses.append({"agent": agent_name, "error": str(e)})
            task = AgentTask(
                hire_request_id=hire.id, agent_name=agent_name,
                tool_used="error", input_data=task_description,
                output_data=str(e), status="failed",
                started_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc))
            db.add(task)

    # Orchestrator agent synthesizes all specialist responses
    try:
        synthesis = await openrouter_client.chat(
            messages=[
                {"role": "system", "content": ORCHESTRATOR_PERSONA},
                {"role": "user", "content": f"""I need to finalize the hiring decision for:
- Candidate: {request.employee_name}
- Role: {request.role} in {request.department}
- Proposed Salary: ${request.salary:,.0f}
- Location: {request.location}
- Start Date: {request.start_date}

Here are the reports from my specialist agents:

{json.dumps(agent_responses, default=str)[:6000]}

Based on all agent findings, provide:
1. Final salary recommendation (with reasoning)
2. Compliance status (clear/blocked/needs review)
3. Benefits & provisioning status
4. Any risks or flags
5. Final GO/NO-GO recommendation"""}
            ],
            max_tokens=1200)
        reasoning = synthesis["choices"][0]["message"]["content"]
    except Exception as e:
        reasoning = f"Pipeline completed with {len(agent_responses)} agent reports. Synthesis error: {e}"

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
