"""Tests for Neo4j client, schema, and seed data."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.graph.client import (
    close_neo4j_driver,
    get_neo4j_driver,
    get_session,
    check_neo4j_health,
)
from backend.graph.schema import (
    CONSTRAINTS,
    INDEXES,
    NODE_TYPES,
    RELATIONSHIP_TYPES,
    setup_schema,
)
from scripts.seed_neo4j import SEED_CYPHER, seed_database


# ── Schema tests ─────────────────────────────────────────────────────────

class TestSchema:
    def test_constraints_cover_all_node_types(self):
        """Every node type should have a uniqueness constraint."""
        for node_type in NODE_TYPES:
            matching = [c for c in CONSTRAINTS if node_type in c]
            assert matching, f"No constraint found for {node_type}"

    def test_constraint_syntax(self):
        """Constraints should use valid Cypher syntax."""
        for stmt in CONSTRAINTS:
            assert stmt.startswith("CREATE CONSTRAINT IF NOT EXISTS")
            assert "REQUIRE" in stmt
            assert "IS UNIQUE" in stmt

    def test_indexes_are_defined(self):
        """We should have at least one index defined."""
        assert len(INDEXES) > 0
        for stmt in INDEXES:
            assert stmt.startswith("CREATE INDEX IF NOT EXISTS")

    def test_expected_node_types(self):
        expected = {
            "Company", "Department", "Employee", "Agent", "Action",
            "HireRequest", "Decision", "DecisionContext", "ResearchResult",
            "PolicyLookup", "PolicyUpdate", "DocumentVerification",
        }
        assert set(NODE_TYPES) == expected

    def test_expected_relationship_types(self):
        expected = {
            "HAS_DEPT", "WORKS_IN", "DELEGATED", "COMPLETED", "DECIDED_BY",
            "INFORMED_BY", "APPLIED_POLICY", "LEARNED", "TRIGGERED",
            "PERFORMED", "AFFECTED", "USED_SYSTEM",
        }
        assert set(RELATIONSHIP_TYPES.keys()) == expected

    def test_delegated_properties(self):
        props = RELATIONSHIP_TYPES["DELEGATED"]
        assert "context_keys" in props
        assert "reasoning" in props
        assert "timestamp" in props
        assert "request_id" in props

    def test_completed_properties(self):
        props = RELATIONSHIP_TYPES["COMPLETED"]
        assert "result_summary" in props
        assert "context_added" in props
        assert "duration_ms" in props
        assert "systems_touched" in props
        assert "timestamp" in props
        assert "request_id" in props

    @pytest.mark.asyncio
    async def test_setup_schema_runs_all_statements(self):
        """setup_schema should execute every constraint and index."""
        mock_session = AsyncMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_driver.session.return_value.__aexit__ = AsyncMock(return_value=False)

        await setup_schema(mock_driver)

        expected_calls = len(CONSTRAINTS) + len(INDEXES)
        assert mock_session.run.call_count == expected_calls


# ── Seed data tests ──────────────────────────────────────────────────────

class TestSeedData:
    def test_seed_cypher_not_empty(self):
        assert len(SEED_CYPHER) > 0

    def test_all_queries_are_parameterized(self):
        """No raw string interpolation — all queries must use $params."""
        for cypher, params in SEED_CYPHER:
            # Every param key should appear as $key in the query
            for key in params:
                assert f"${key}" in cypher, (
                    f"Parameter ${key} not found in query: {cypher[:80]}"
                )

    def test_seed_creates_company(self):
        company_queries = [c for c, _ in SEED_CYPHER if "Company" in c and "MERGE" in c]
        assert len(company_queries) >= 1

    def test_seed_creates_departments(self):
        dept_queries = [c for c, p in SEED_CYPHER if "Department" in c and "MERGE" in c and "name" in p]
        dept_names = {p["name"] for c, p in SEED_CYPHER if "Department" in c and "MERGE" in c and "name" in p}
        assert dept_names == {"Engineering", "Finance", "HR", "Marketing", "IT"}

    def test_seed_creates_agents(self):
        agent_queries = [
            p for c, p in SEED_CYPHER
            if "Agent" in c and "MERGE" in c and "name" in p and "role" in p
        ]
        agent_names = {p["name"] for p in agent_queries}
        assert {"Chief", "Maya", "Sam", "Alex"} == agent_names

    def test_seed_creates_employees(self):
        emp_queries = [
            p for c, p in SEED_CYPHER
            if "Employee" in c and "MERGE" in c and "name" in p
        ]
        names = {p["name"] for p in emp_queries}
        assert names == {"John Miller", "Lisa Park", "Mike Johnson", "Anna Lee", "Tom Wilson"}

    def test_seed_has_learned_edge(self):
        learned = [c for c, _ in SEED_CYPHER if "LEARNED" in c]
        assert len(learned) >= 1

    def test_seed_has_policy_update(self):
        pu = [c for c, p in SEED_CYPHER if "PolicyUpdate" in c and "MERGE" in c]
        assert len(pu) >= 1

    @pytest.mark.asyncio
    async def test_seed_database_executes_all(self):
        mock_session = AsyncMock()
        mock_driver = MagicMock()
        mock_driver.session.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_driver.session.return_value.__aexit__ = AsyncMock(return_value=False)

        await seed_database(mock_driver)

        assert mock_session.run.call_count == len(SEED_CYPHER)


# ── Client tests ─────────────────────────────────────────────────────────

class TestClient:
    @pytest.mark.asyncio
    async def test_get_driver_returns_driver(self):
        with patch("backend.graph.client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_agd.driver.return_value = mock_driver

            # Reset singleton
            import backend.graph.client as client_mod
            client_mod._driver = None

            driver = await get_neo4j_driver()
            assert driver is mock_driver
            mock_agd.driver.assert_called_once()

            # Cleanup
            client_mod._driver = None

    @pytest.mark.asyncio
    async def test_get_driver_is_singleton(self):
        with patch("backend.graph.client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_agd.driver.return_value = mock_driver

            import backend.graph.client as client_mod
            client_mod._driver = None

            d1 = await get_neo4j_driver()
            d2 = await get_neo4j_driver()
            assert d1 is d2
            assert mock_agd.driver.call_count == 1

            client_mod._driver = None

    @pytest.mark.asyncio
    async def test_close_driver(self):
        import backend.graph.client as client_mod
        mock_driver = AsyncMock()
        client_mod._driver = mock_driver

        await close_neo4j_driver()

        mock_driver.close.assert_awaited_once()
        assert client_mod._driver is None

    @pytest.mark.asyncio
    async def test_health_check(self):
        with patch("backend.graph.client.AsyncGraphDatabase") as mock_agd:
            mock_driver = AsyncMock()
            mock_agd.driver.return_value = mock_driver

            import backend.graph.client as client_mod
            client_mod._driver = None

            result = await check_neo4j_health()
            assert result is True
            mock_driver.verify_connectivity.assert_awaited_once()

            client_mod._driver = None

    @pytest.mark.asyncio
    async def test_get_session_context_manager(self):
        import backend.graph.client as client_mod
        mock_driver = MagicMock()
        mock_session = AsyncMock()
        mock_driver.session.return_value = mock_session
        client_mod._driver = mock_driver

        async with get_session() as session:
            assert session is mock_session

        mock_session.close.assert_awaited_once()

        client_mod._driver = None
