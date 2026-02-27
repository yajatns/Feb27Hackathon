# T2: Neo4j Setup on Render

## Context
We're building backoffice.ai for a hackathon. This is the Neo4j "System of Reasoning" setup.

## Branch
Create branch: `chhotu/T2-neo4j`  (branch off `main`)

## Requirements

1. **Neo4j Connection Client** (`backend/graph/client.py`):
   - Async Neo4j driver connection using `neo4j` Python package
   - Connection settings from env vars: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
   - Connection pool with health check
   - Context manager for session handling

2. **Neo4j Schema** (`backend/graph/schema.py`):
   - Constraint creation for unique IDs on all node types
   - Node types: Company, Department, Employee, Agent, Action, HireRequest, Decision, DecisionContext, ResearchResult, PolicyLookup, PolicyUpdate, DocumentVerification
   - Relationship types: HAS_DEPT, WORKS_IN, DELEGATED (with context_keys, reasoning, timestamp, request_id), COMPLETED (with result_summary, context_added, duration_ms, systems_touched, timestamp, request_id), DECIDED_BY, INFORMED_BY, APPLIED_POLICY, LEARNED, TRIGGERED, PERFORMED, AFFECTED, USED_SYSTEM
   - Function `setup_schema(driver)` that creates all constraints and indexes

3. **Neo4j Seed Data** (`scripts/seed_neo4j.py`):
   - Company: Alex SaaS Inc
   - Departments: Engineering, Finance, HR, Marketing, IT
   - 5 past hires with full DELEGATED/COMPLETED edges between agents:
     - John Miller, Sr Engineer, $145K (clean hire)
     - Lisa Park, Staff Engineer, $180K (clean hire)  
     - Mike Johnson, Sr Engineer, $160K (salary override from $150K — the learning moment)
     - Anna Lee, Engineering Manager, $190K (escalated to VP)
     - Tom Wilson, Jr Engineer, $120K (clean hire)
   - 4 Agents: Chief (Orchestrator), Maya (HR), Sam (Finance), Alex (IT)
   - Tavily research result nodes attached to each hire
   - Senso policy lookup nodes attached to each hire
   - 1 LEARNED edge: Mike's override → PolicyUpdate "SF Sr Engineer salary floor: $155K"
   - 1 pre-seeded improvement notification

4. **Tests** (`tests/test_neo4j.py`):
   - Test schema creation (mock driver)
   - Test seed data Cypher queries are valid
   - Test client connection handling

5. **Integration with FastAPI** (`backend/graph/__init__.py`):
   - Export `get_neo4j_driver()`, `setup_schema()`, `seed_database()`
   - FastAPI lifespan event to connect on startup

## Environment Variables
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j  
NEO4J_PASSWORD=backoffice2026
```

## Notes
- Use Neo4j Aura free tier for cloud hosting (Render doesn't natively support Neo4j Docker)
- Or use a local Neo4j for dev, Aura for production
- All Cypher queries should be parameterized (no string concatenation)
- After completion: git add, commit, push, create PR

When completely finished, run: openclaw system event --text "Done: T2 Neo4j setup - schema, seed data, client, tests" --mode now
