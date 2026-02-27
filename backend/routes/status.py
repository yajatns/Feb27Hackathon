"""GET /api/status — agent pipeline status."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.db_models import HireRequest, AgentTask
from models.schemas import PipelineStatus, AgentStatus

router = APIRouter()


@router.get("/status", response_model=PipelineStatus)
async def get_pipeline_status(hire_request_id: str | None = Query(None),
                               db: AsyncSession = Depends(get_db)):
    """Get the current pipeline status."""
    if hire_request_id:
        result = await db.execute(select(HireRequest).where(HireRequest.id == hire_request_id))
        hire = result.scalar_one_or_none()
        if not hire:
            return PipelineStatus(overall_status="not_found", agents=[])

        tasks_result = await db.execute(
            select(AgentTask).where(AgentTask.hire_request_id == hire.id))
        tasks = tasks_result.scalars().all()

        agents = [AgentStatus(name=t.agent_name, status=t.status,
                               current_task=t.tool_used, last_active=t.completed_at) for t in tasks]
        completed = sum(1 for t in tasks if t.status == "completed")
        total = len(tasks) or 1

        return PipelineStatus(
            hire_request_id=str(hire.id), overall_status=hire.status,
            agents=agents, progress_pct=(completed / total) * 100)

    # No specific request — return overall stats
    count_result = await db.execute(select(func.count()).select_from(HireRequest))
    total = count_result.scalar() or 0

    return PipelineStatus(overall_status=f"{total} total hire requests", agents=[], progress_pct=100.0)
