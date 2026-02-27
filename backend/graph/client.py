"""Neo4j async driver client for backoffice.ai."""

import os
from contextlib import asynccontextmanager

from neo4j import AsyncGraphDatabase

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "backoffice2026")

_driver = None


async def get_neo4j_driver():
    """Return the singleton async Neo4j driver, creating it if needed."""
    global _driver
    if _driver is None:
        _driver = AsyncGraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            max_connection_pool_size=50,
        )
    return _driver


async def close_neo4j_driver():
    """Close the Neo4j driver and reset the singleton."""
    global _driver
    if _driver is not None:
        await _driver.close()
        _driver = None


async def check_neo4j_health():
    """Verify connectivity to Neo4j."""
    driver = await get_neo4j_driver()
    await driver.verify_connectivity()
    return True


@asynccontextmanager
async def get_session(database="neo4j"):
    """Async context manager that yields a Neo4j async session."""
    driver = await get_neo4j_driver()
    session = driver.session(database=database)
    try:
        yield session
    finally:
        await session.close()
