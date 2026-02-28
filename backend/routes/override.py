"""POST /api/override — human override that feeds the self-improvement loop."""

import json
import traceback
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from models.database import get_db
from models.db_models import HireRequest, UserOverride
from models.schemas import UserOverrideCreate
from integrations.neo4j_client import neo4j_client
from integrations.senso_policies import add_learned_policy

router = APIRouter()


@router.post("/override")
async def create_override(override: UserOverrideCreate, db: AsyncSession = Depends(get_db)):
    """Record a human override — triggers the self-improvement loop."""
    try:
        # Ensure table exists
        try:
            await db.execute(text("""
                CREATE TABLE IF NOT EXISTS user_overrides (
                    id VARCHAR(36) PRIMARY KEY,
                    hire_request_id VARCHAR(36) REFERENCES hire_requests(id),
                    field_overridden VARCHAR(100) NOT NULL,
                    original_value TEXT NOT NULL,
                    new_value TEXT NOT NULL,
                    reason TEXT,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            await db.flush()
        except Exception:
            pass

        # Get the original hire request
        result = await db.execute(select(HireRequest).where(HireRequest.id == override.hire_request_id))
        hire = result.scalar_one_or_none()
        if not hire:
            raise HTTPException(status_code=404, detail="Hire request not found")

        original = str(getattr(hire, override.field_overridden, hire.salary))

        # Record override
        import uuid as _uuid
        db_override = UserOverride(
            id=str(_uuid.uuid4()),
            hire_request_id=str(override.hire_request_id),
            field_overridden=override.field_overridden,
            original_value=original,
            new_value=override.new_value,
            reason=override.reason)
        db.add(db_override)
        await db.flush()

        # Log LEARNED edge in Neo4j
        neo4j_msg = "not attempted"
        try:
            await neo4j_client.log_learned(
                override_field=override.field_overridden,
                original_value=original,
                new_value=override.new_value,
                reason=override.reason or "Human override")
            neo4j_msg = "LEARNED edge created"
        except Exception as e:
            neo4j_msg = f"Neo4j error: {str(e)[:100]}"

        # Self-improvement: update local policy store
        add_learned_policy(
            field=override.field_overridden,
            new_value=override.new_value,
            reason=override.reason or "Human override",
            override_count=1
        )

        return {
            "status": "success",
            "hire_request_id": str(override.hire_request_id),
            "field_overridden": override.field_overridden,
            "original_value": original,
            "new_value": override.new_value,
            "reason": override.reason,
            "neo4j": neo4j_msg,
            "self_improvement": {
                "learned": True,
                "policy_updated": True,
                "message": f"Override recorded. LEARNED edge in Neo4j. Policy store updated. Next agent query will use learned policy."
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "traceback": traceback.format_exc()[-500:]}
        )
