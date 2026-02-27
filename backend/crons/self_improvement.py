"""Self-Improvement Cron — analyzes override patterns and updates Senso policies.

The heart of backoffice.ai's learning loop:
1. Query Neo4j for LEARNED edges (human overrides)
2. Detect patterns (3+ overrides in same direction)
3. Auto-update Senso policies based on patterns
4. Log the improvement back to Neo4j
"""

import json
from datetime import datetime, timezone

from integrations.neo4j_client import neo4j_client
from integrations.senso import senso_client
from integrations.senso_policies import add_learned_policy


async def run_self_improvement(db_session=None) -> dict:
    """Analyze override patterns and update policies."""
    improvements = []

    # Query Neo4j for LEARNED edges
    try:
        learned_query = """
        MATCH (o:Override)-[:LEARNED]->(pu:PolicyUpdate)
        RETURN o.field AS field, o.original AS original, o.new_val AS new_value,
               o.reason AS reason, pu.new_val AS policy_update
        ORDER BY o.timestamp DESC
        LIMIT 50
        """
        overrides = await neo4j_client.run_query(learned_query)
    except Exception as e:
        overrides = []
        improvements.append({"error": f"Neo4j query failed: {e}"})

    # Group overrides by field
    field_groups: dict[str, list] = {}
    for override in overrides:
        field = override.get("field", "unknown")
        if field not in field_groups:
            field_groups[field] = []
        field_groups[field].append(override)

    # Detect patterns (3+ overrides on same field)
    for field, group in field_groups.items():
        if len(group) >= 3:
            # Pattern detected — generate policy update
            latest_values = [g.get("new_value", "") for g in group[:5]]
            reasons = [g.get("reason", "") for g in group[:5] if g.get("reason")]

            improvement = {
                "field": field,
                "override_count": len(group),
                "pattern": f"{len(group)} overrides detected on {field}",
                "latest_values": latest_values,
                "reasons": reasons,
                "action": "policy_update_recommended",
            }

            # Update local policy store (immediate effect on next agent query)
            learned_key = add_learned_policy(
                field=field,
                new_value=', '.join(str(v) for v in latest_values[:3]),
                reason='; '.join(reasons[:3]) if reasons else f"Pattern detected from {len(group)} overrides",
                override_count=len(group)
            )
            improvement["local_policy_updated"] = learned_key

            # Also try to upload to Senso (best-effort)
            try:
                policy_text = (
                    f"AUTO-UPDATED POLICY: Based on {len(group)} human overrides, "
                    f"the {field} policy has been adjusted. "
                    f"Recent override values: {', '.join(str(v) for v in latest_values[:3])}. "
                    f"Reasons cited: {'; '.join(reasons[:3])}"
                )
                await senso_client.upload_policy(
                    filename=f"auto_policy_{field}_{datetime.now(timezone.utc).strftime('%Y%m%d')}.txt",
                    content=policy_text.encode(),
                    content_type="text/plain")
                improvement["senso_update"] = "uploaded"
            except Exception as e:
                improvement["senso_update"] = f"failed (using local store): {e}"

            improvements.append(improvement)

    # Log improvement cycle to Neo4j
    try:
        await neo4j_client.log_completion(
            agent_name="SelfImprovementCron",
            task="self_improvement_cycle",
            result=json.dumps({"improvements": len(improvements)}, default=str),
            tool_used="neo4j+senso",
            hire_request_id=f"cron-improve-{datetime.now(timezone.utc).strftime('%Y%m%d')}")
    except Exception:
        pass

    return {
        "cron_type": "self_improvement",
        "improvements_count": len(improvements),
        "improvements": improvements,
        "override_fields_analyzed": list(field_groups.keys()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
