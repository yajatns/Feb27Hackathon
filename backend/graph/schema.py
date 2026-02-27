"""Neo4j schema: constraints, indexes, and type definitions for backoffice.ai."""

# ── Node labels ──────────────────────────────────────────────────────────
NODE_TYPES = [
    "Company",
    "Department",
    "Employee",
    "Agent",
    "Action",
    "HireRequest",
    "Decision",
    "DecisionContext",
    "ResearchResult",
    "PolicyLookup",
    "PolicyUpdate",
    "DocumentVerification",
]

# ── Relationship types (with property specs in comments) ─────────────────
RELATIONSHIP_TYPES = {
    "HAS_DEPT": {},
    "WORKS_IN": {},
    "DELEGATED": {
        "context_keys": "list",
        "reasoning": "string",
        "timestamp": "datetime",
        "request_id": "string",
    },
    "COMPLETED": {
        "result_summary": "string",
        "context_added": "list",
        "duration_ms": "integer",
        "systems_touched": "list",
        "timestamp": "datetime",
        "request_id": "string",
    },
    "DECIDED_BY": {},
    "INFORMED_BY": {},
    "APPLIED_POLICY": {},
    "LEARNED": {},
    "TRIGGERED": {},
    "PERFORMED": {},
    "AFFECTED": {},
    "USED_SYSTEM": {},
}

# ── Constraint & index Cypher statements ─────────────────────────────────

CONSTRAINTS = [
    f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE"
    for label in NODE_TYPES
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS FOR (n:Employee) ON (n.name)",
    "CREATE INDEX IF NOT EXISTS FOR (n:Agent) ON (n.name)",
    "CREATE INDEX IF NOT EXISTS FOR (n:HireRequest) ON (n.status)",
]


async def setup_schema(driver):
    """Create all constraints and indexes in Neo4j."""
    async with driver.session(database="neo4j") as session:
        for stmt in CONSTRAINTS + INDEXES:
            await session.run(stmt)
