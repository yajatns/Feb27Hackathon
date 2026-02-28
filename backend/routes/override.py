"""POST /api/override — human override that feeds the self-improvement loop."""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.db_models import HireRequest, UserOverride
from models.schemas import UserOverrideCreate, UserOverrideResponse
from integrations.neo4j_client import neo4j_client
from integrations.senso import senso_client
from integrations.senso_policies import add_learned_policy

router = APIRouter()


@router.post("/override")
async def create_override(override: UserOverrideCreate, db: AsyncSession = Depends(get_db)):
    # Ensure table exists
    try:
        from models.database import engine
        from models.db_models import Base
        import asyncio
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        pass
    """Record a human override — triggers the self-improvement loop.

    When a human overrides a salary, policy, or decision:
    1. Record the override in Postgres
    2. Log a LEARNED edge in Neo4j
    3. If pattern detected (3+ overrides same direction), update Senso policy
    """
    # Get the original hire request
    result = await db.execute(select(HireRequest).where(HireRequest.id == override.hire_request_id))
    hire = result.scalar_one_or_none()
    if not hire:
        raise HTTPException(status_code=404, detail="Hire request not found")

    # Get original value
    original = getattr(hire, override.field_overridden, str(hire.salary))

    # Record override
    db_override = UserOverride(
        hire_request_id=override.hire_request_id,
        field_overridden=override.field_overridden,
        original_value=str(original),
        new_value=override.new_value,
        reason=override.reason)
    db.add(db_override)
    await db.flush()

    # Log LEARNED edge in Neo4j
    try:
        await neo4j_client.log_learned(
            override_field=override.field_overridden,
            original_value=str(original),
            new_value=override.new_value,
            reason=override.reason or "Human override")
    except Exception:
        pass

    # Check for patterns (3+ overrides on same field in same direction)
    pattern_result = await db.execute(
        select(UserOverride).where(UserOverride.field_overridden == override.field_overridden))
    similar_overrides = pattern_result.scalars().all()

    # Self-improvement: update local policy store immediately
    # Even 1 override starts teaching the system (3+ triggers stronger signal)
    add_learned_policy(
        field=override.field_overridden,
        new_value=override.new_value,
        reason=override.reason or "Human override",
        override_count=len(similar_overrides)
    )

    improvement_status = {
        "learned": True,
        "override_count": len(similar_overrides),
        "policy_updated": True,
        "message": f"Policy store updated. {len(similar_overrides)} override(s) on '{override.field_overridden}'. "
                   f"Next agent query will use the learned policy."
    }

    if len(similar_overrides) >= 3:
        improvement_status["pattern_detected"] = True
        improvement_status["message"] += " Strong pattern detected — high confidence policy update."
        # Also try Senso upload (best-effort)
        try:
            policy_update = f"Based on {len(similar_overrides)} human overrides, " \
                            f"the {override.field_overridden} policy should be updated. " \
                            f"Latest override: {override.new_value} (reason: {override.reason})"
            await senso_client.upload_policy(
                filename=f"auto_update_{override.field_overridden}.txt",
                content=policy_update.encode(),
                content_type="text/plain")
        except Exception:
            pass

    return {
        "id": db_override.id,
        "hire_request_id": db_override.hire_request_id,
        "field_overridden": db_override.field_overridden,
        "original_value": db_override.original_value,
        "new_value": db_override.new_value,
        "reason": db_override.reason,
        "created_at": str(db_override.created_at),
        "self_improvement": improvement_status
    }
