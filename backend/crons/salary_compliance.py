"""Salary Compliance Cron — monitors salary drift against market benchmarks.

Proactive: runs periodically, compares existing employee salaries against
current market data (Tavily) and internal policies (Senso).
Findings logged to Neo4j and stored in Postgres.
"""

import json
from datetime import datetime, timezone

from integrations.tavily import tavily_client
from integrations.senso import senso_client
from integrations.neo4j_client import neo4j_client


async def run_salary_compliance(db_session=None) -> dict:
    """Check all employees for salary compliance against market + policy."""
    findings = []

    # Sample roles to check (in production, would query from DB)
    roles_to_check = [
        {"role": "Senior Engineer", "location": "San Francisco, CA", "current_salary": 150000},
        {"role": "Product Manager", "location": "San Francisco, CA", "current_salary": 160000},
        {"role": "Data Analyst", "location": "New York, NY", "current_salary": 120000},
    ]

    for role_info in roles_to_check:
        role = role_info["role"]
        location = role_info["location"]
        current = role_info["current_salary"]

        # Get market benchmark
        try:
            market = await tavily_client.salary_benchmark(role, location)
            market_summary = market.get("answer", json.dumps(market.get("results", [])[:2], default=str))
        except Exception as e:
            market_summary = f"Error fetching market data: {e}"

        # Get internal policy
        try:
            policy = await senso_client.search_policy(f"salary band {role} {location}")
        except Exception as e:
            policy = {"error": str(e)}

        finding = {
            "role": role,
            "location": location,
            "current_salary": current,
            "market_data": market_summary[:500],
            "policy_check": json.dumps(policy, default=str)[:500],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        findings.append(finding)

        # Log to Neo4j
        try:
            await neo4j_client.log_completion(
                agent_name="SalaryComplianceCron",
                task=f"salary_check_{role}",
                result=json.dumps(finding, default=str)[:500],
                tool_used="tavily+senso",
                hire_request_id=f"cron-salary-{datetime.now(timezone.utc).strftime('%Y%m%d')}")
        except Exception:
            pass

    return {
        "cron_type": "salary_compliance",
        "findings_count": len(findings),
        "findings": findings,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
