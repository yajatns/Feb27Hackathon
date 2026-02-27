"""GET /api/graph — Neo4j reasoning graph visualization data."""

from fastapi import APIRouter, Query
from models.schemas import GraphResponse
from integrations.neo4j_client import neo4j_client

router = APIRouter()


@router.get("/graph", response_model=GraphResponse)
async def get_graph(hire_request_id: str | None = Query(None)):
    """Get the Neo4j reasoning graph for NVL visualization."""
    try:
        data = await neo4j_client.get_full_graph(hire_request_id)
        return GraphResponse(
            nodes=[{"id": n["id"], "label": n["label"], "type": n["type"],
                     "properties": n.get("properties", {})} for n in data.get("nodes", [])],
            edges=[{"source": e["source"], "target": e["target"], "type": e["type"],
                     "properties": e.get("properties", {})} for e in data.get("edges", [])])
    except Exception:
        return GraphResponse(nodes=[], edges=[])
