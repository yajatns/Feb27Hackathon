"""Neo4j graph layer for backoffice.ai."""

try:
    from graph.client import get_neo4j_driver, close_neo4j_driver, get_session
    from graph.schema import setup_schema
except ImportError:
    # Fallback for when imported from different contexts
    get_neo4j_driver = None
    close_neo4j_driver = None
    get_session = None
    setup_schema = None

__all__ = [
    "get_neo4j_driver",
    "close_neo4j_driver",
    "get_session",
    "setup_schema",
]
