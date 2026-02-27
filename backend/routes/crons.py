"""Cron management routes — trigger and view monitoring results."""

import json
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.db_models import CronResult
from models.schemas import CronResultResponse
from crons.salary_compliance import run_salary_compliance
from crons.self_improvement import run_self_improvement
from crons.video_audit import run_video_audit

router = APIRouter()

CRON_REGISTRY = {
    "salary_compliance": run_salary_compliance,
    "self_improvement": run_self_improvement,
    "video_audit": run_video_audit,
}


@router.post("/crons/{cron_type}")
async def trigger_cron(cron_type: str, db: AsyncSession = Depends(get_db)):
    """Manually trigger a monitoring cron job."""
    if cron_type not in CRON_REGISTRY:
        return {"error": f"Unknown cron type. Available: {list(CRON_REGISTRY.keys())}"}

    runner = CRON_REGISTRY[cron_type]
    result = await runner(db_session=db)

    # Store result in Postgres
    cron_record = CronResult(
        cron_type=cron_type,
        findings=json.dumps(result.get("findings", []), default=str),
        recommendations=json.dumps(result.get("improvements", []), default=str))
    db.add(cron_record)
    await db.flush()

    return {"cron_type": cron_type, "result": result, "stored_id": str(cron_record.id)}


@router.get("/crons", response_model=list[CronResultResponse])
async def list_cron_results(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """List recent cron results."""
    result = await db.execute(
        select(CronResult).order_by(CronResult.created_at.desc()).limit(limit))
    return result.scalars().all()


@router.get("/crons/types")
async def list_cron_types():
    """List available cron types."""
    return {"available_crons": list(CRON_REGISTRY.keys())}
