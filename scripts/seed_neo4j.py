"""Seed Neo4j with backoffice.ai demo data.

Run standalone:  python -m scripts.seed_neo4j
Or call seed_database(driver) programmatically.
"""

import asyncio
import uuid
from datetime import datetime, timezone

# ── Helpers ──────────────────────────────────────────────────────────────

def _id():
    return str(uuid.uuid4())


def _ts(days_ago: int = 0):
    """ISO timestamp for `days_ago` days before now."""
    from datetime import timedelta
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()


# ── Seed queries ─────────────────────────────────────────────────────────

SEED_CYPHER = []


def _q(cypher: str, params: dict | None = None):
    SEED_CYPHER.append((cypher, params or {}))


# Company
company_id = _id()
_q(
    "MERGE (c:Company {id: $id}) SET c.name = $name, c.domain = $domain",
    {"id": company_id, "name": "Alex SaaS Inc", "domain": "alexsaas.com"},
)

# Departments
dept_ids = {}
for dept_name in ["Engineering", "Finance", "HR", "Marketing", "IT"]:
    did = _id()
    dept_ids[dept_name] = did
    _q(
        "MERGE (d:Department {id: $id}) SET d.name = $name",
        {"id": did, "name": dept_name},
    )
    _q(
        """
        MATCH (c:Company {id: $cid}), (d:Department {id: $did})
        MERGE (c)-[:HAS_DEPT]->(d)
        """,
        {"cid": company_id, "did": did},
    )

# Agents
agent_ids = {}
agents = [
    ("Chief", "Orchestrator", "Coordinates all agents"),
    ("Maya", "HR", "Handles HR workflows"),
    ("Sam", "Finance", "Handles finance workflows"),
    ("Alex", "IT", "Handles IT workflows"),
]
for aname, arole, adesc in agents:
    aid = _id()
    agent_ids[aname] = aid
    _q(
        "MERGE (a:Agent {id: $id}) SET a.name = $name, a.role = $role, a.description = $desc",
        {"id": aid, "name": aname, "role": arole, "desc": adesc},
    )

# ── Past hires ───────────────────────────────────────────────────────────

hires = [
    {
        "name": "John Miller",
        "title": "Sr Engineer",
        "salary": 145000,
        "dept": "Engineering",
        "status": "completed",
        "days_ago": 90,
        "notes": "Clean hire",
        "override": False,
        "escalated": False,
    },
    {
        "name": "Lisa Park",
        "title": "Staff Engineer",
        "salary": 180000,
        "dept": "Engineering",
        "status": "completed",
        "days_ago": 75,
        "notes": "Clean hire",
        "override": False,
        "escalated": False,
    },
    {
        "name": "Mike Johnson",
        "title": "Sr Engineer",
        "salary": 160000,
        "dept": "Engineering",
        "status": "completed",
        "days_ago": 60,
        "notes": "Salary override from $150K",
        "override": True,
        "original_salary": 150000,
        "escalated": False,
    },
    {
        "name": "Anna Lee",
        "title": "Engineering Manager",
        "salary": 190000,
        "dept": "Engineering",
        "status": "completed",
        "days_ago": 45,
        "notes": "Escalated to VP",
        "override": False,
        "escalated": True,
    },
    {
        "name": "Tom Wilson",
        "title": "Jr Engineer",
        "salary": 120000,
        "dept": "Engineering",
        "status": "completed",
        "days_ago": 30,
        "notes": "Clean hire",
        "override": False,
        "escalated": False,
    },
]

for h in hires:
    emp_id = _id()
    hire_id = _id()
    ts = _ts(h["days_ago"])
    req_id = _id()

    # Employee node
    _q(
        """
        MERGE (e:Employee {id: $id})
        SET e.name = $name, e.title = $title, e.salary = $salary
        """,
        {"id": emp_id, "name": h["name"], "title": h["title"], "salary": h["salary"]},
    )
    _q(
        "MATCH (e:Employee {id: $eid}), (d:Department {id: $did}) MERGE (e)-[:WORKS_IN]->(d)",
        {"eid": emp_id, "did": dept_ids[h["dept"]]},
    )

    # HireRequest node
    _q(
        """
        MERGE (hr:HireRequest {id: $id})
        SET hr.candidate_name = $name, hr.title = $title,
            hr.salary = $salary, hr.status = $status,
            hr.notes = $notes, hr.created_at = $ts
        """,
        {
            "id": hire_id,
            "name": h["name"],
            "title": h["title"],
            "salary": h["salary"],
            "status": h["status"],
            "notes": h["notes"],
            "ts": ts,
        },
    )
    _q(
        "MATCH (hr:HireRequest {id: $hid}), (e:Employee {id: $eid}) MERGE (hr)-[:AFFECTED]->(e)",
        {"hid": hire_id, "eid": emp_id},
    )

    # Chief delegates to Maya (HR check)
    _q(
        """
        MATCH (chief:Agent {id: $chief_id}), (maya:Agent {id: $maya_id})
        CREATE (chief)-[:DELEGATED {
            context_keys: $ctx, reasoning: $reason,
            timestamp: $ts, request_id: $req_id
        }]->(maya)
        """,
        {
            "chief_id": agent_ids["Chief"],
            "maya_id": agent_ids["Maya"],
            "ctx": ["candidate_name", "title", "salary"],
            "reason": "HR verification for " + h["name"],
            "ts": ts,
            "req_id": req_id,
        },
    )

    # Maya completes
    _q(
        """
        MATCH (maya:Agent {id: $maya_id}), (chief:Agent {id: $chief_id})
        CREATE (maya)-[:COMPLETED {
            result_summary: $summary, context_added: $ctx,
            duration_ms: $dur, systems_touched: $sys,
            timestamp: $ts, request_id: $req_id
        }]->(chief)
        """,
        {
            "maya_id": agent_ids["Maya"],
            "chief_id": agent_ids["Chief"],
            "summary": "HR check passed for " + h["name"],
            "ctx": ["background_ok", "references_ok"],
            "dur": 1200,
            "sys": ["senso"],
            "ts": ts,
            "req_id": req_id,
        },
    )

    # Chief delegates to Sam (Finance check)
    _q(
        """
        MATCH (chief:Agent {id: $chief_id}), (sam:Agent {id: $sam_id})
        CREATE (chief)-[:DELEGATED {
            context_keys: $ctx, reasoning: $reason,
            timestamp: $ts, request_id: $req_id
        }]->(sam)
        """,
        {
            "chief_id": agent_ids["Chief"],
            "sam_id": agent_ids["Sam"],
            "ctx": ["salary", "title", "department"],
            "reason": "Finance review for " + h["name"],
            "ts": ts,
            "req_id": req_id,
        },
    )

    # Sam completes
    _q(
        """
        MATCH (sam:Agent {id: $sam_id}), (chief:Agent {id: $chief_id})
        CREATE (sam)-[:COMPLETED {
            result_summary: $summary, context_added: $ctx,
            duration_ms: $dur, systems_touched: $sys,
            timestamp: $ts, request_id: $req_id
        }]->(chief)
        """,
        {
            "sam_id": agent_ids["Sam"],
            "chief_id": agent_ids["Chief"],
            "summary": "Budget approved for " + h["name"],
            "ctx": ["budget_approved", "comp_band_ok"],
            "dur": 800,
            "sys": ["senso"],
            "ts": ts,
            "req_id": req_id,
        },
    )

    # Tavily research result
    research_id = _id()
    _q(
        """
        MERGE (r:ResearchResult {id: $id})
        SET r.source = 'tavily', r.query = $query,
            r.summary = $summary, r.timestamp = $ts
        """,
        {
            "id": research_id,
            "query": h["name"] + " " + h["title"] + " background",
            "summary": "Web research completed for " + h["name"],
            "ts": ts,
        },
    )
    _q(
        "MATCH (hr:HireRequest {id: $hid}), (r:ResearchResult {id: $rid}) MERGE (hr)-[:INFORMED_BY]->(r)",
        {"hid": hire_id, "rid": research_id},
    )

    # Senso policy lookup
    policy_id = _id()
    _q(
        """
        MERGE (p:PolicyLookup {id: $id})
        SET p.source = 'senso', p.policy_area = $area,
            p.result = $result, p.timestamp = $ts
        """,
        {
            "id": policy_id,
            "area": "compensation_band",
            "result": "Comp band verified for " + h["title"],
            "ts": ts,
        },
    )
    _q(
        "MATCH (hr:HireRequest {id: $hid}), (p:PolicyLookup {id: $pid}) MERGE (hr)-[:APPLIED_POLICY]->(p)",
        {"hid": hire_id, "pid": policy_id},
    )

# ── LEARNED edge: Mike's salary override → PolicyUpdate ──────────────────

policy_update_id = _id()
_q(
    """
    MERGE (pu:PolicyUpdate {id: $id})
    SET pu.description = $desc, pu.source_event = $src,
        pu.new_rule = $rule, pu.timestamp = $ts
    """,
    {
        "id": policy_update_id,
        "desc": "SF Sr Engineer salary floor updated",
        "src": "Mike Johnson salary override",
        "rule": "SF Sr Engineer salary floor: $155K",
        "ts": _ts(60),
    },
)
_q(
    """
    MATCH (sam:Agent {id: $sam_id}), (pu:PolicyUpdate {id: $pu_id})
    CREATE (sam)-[:LEARNED {timestamp: $ts, trigger: $trigger}]->(pu)
    """,
    {
        "sam_id": agent_ids["Sam"],
        "pu_id": policy_update_id,
        "ts": _ts(60),
        "trigger": "Mike Johnson salary override $150K -> $160K",
    },
)

# ── Pre-seeded improvement notification ──────────────────────────────────

notification_id = _id()
_q(
    """
    MERGE (d:Decision {id: $id})
    SET d.type = 'improvement_notification',
        d.summary = $summary,
        d.timestamp = $ts
    """,
    {
        "id": notification_id,
        "summary": "Salary band auto-adjustment enabled based on override patterns",
        "ts": _ts(30),
    },
)
_q(
    """
    MATCH (chief:Agent {id: $chief_id}), (d:Decision {id: $did})
    CREATE (chief)-[:DECIDED_BY]->(d)
    """,
    {"chief_id": agent_ids["Chief"], "did": notification_id},
)


# ── Public interface ─────────────────────────────────────────────────────

async def seed_database(driver):
    """Execute all seed Cypher statements against the given driver."""
    async with driver.session(database="neo4j") as session:
        for cypher, params in SEED_CYPHER:
            await session.run(cypher, params)


# ── CLI entry point ──────────────────────────────────────────────────────

async def _main():
    from backend.graph.client import get_neo4j_driver, close_neo4j_driver
    from backend.graph.schema import setup_schema

    driver = await get_neo4j_driver()
    print("Setting up schema...")
    await setup_schema(driver)
    print("Seeding data...")
    await seed_database(driver)
    print("Done!")
    await close_neo4j_driver()


if __name__ == "__main__":
    asyncio.run(_main())
