"""GET /api/graph — Neo4j reasoning graph visualization data."""

import traceback
from fastapi import APIRouter, Query
from integrations.neo4j_client import neo4j_client

router = APIRouter()


@router.get("/graph")
async def get_graph(hire_request_id: str | None = Query(None)):
    """Get the Neo4j reasoning graph for NVL visualization."""
    try:
        data = await neo4j_client.get_full_graph(hire_request_id)
        return {
            "nodes": [{"id": str(n["id"]), "label": str(n["label"]), "type": str(n["type"]),
                        "properties": n.get("properties", {})} for n in data.get("nodes", [])],
            "edges": [{"source": str(e["source"]), "target": str(e["target"]), "type": str(e["type"]),
                        "properties": e.get("properties", {})} for e in data.get("edges", [])]
        }
    except Exception as e:
        print(f"[GRAPH ERROR] {e}\n{traceback.format_exc()}")
        return {"nodes": [], "edges": [], "error": str(e)}
