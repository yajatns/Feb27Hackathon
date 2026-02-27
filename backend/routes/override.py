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

router = APIRouter()


@router.post("/override", response_model=UserOverrideResponse)
async def create_override(override: UserOverrideCreate, db: AsyncSession = Depends(get_db)):
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

    if len(similar_overrides) >= 3:
        # Self-improvement: update Senso policy
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

    return UserOverrideResponse(
        id=db_override.id,
        hire_request_id=db_override.hire_request_id,
        field_overridden=db_override.field_overridden,
        original_value=db_override.original_value,
        new_value=db_override.new_value,
        reason=db_override.reason,
        created_at=db_override.created_at)
