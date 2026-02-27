"""POST /api/query — plain English to tool routing via orchestrator."""

import json
import uuid
from fastapi import APIRouter
from models.schemas import QueryRequest, QueryResponse
from integrations.openrouter import openrouter_client
from integrations.senso import senso_client
from integrations.tavily import tavily_client
from integrations.neo4j_client import neo4j_client

router = APIRouter()

SYSTEM_PROMPT = """You are the backoffice.ai orchestrator. Given a user request, return a JSON plan:
{
    "intent": "hire|research|compliance|general",
    "steps": [{"tool": "senso_search|tavily_search|reka_analyze|yutori_browse", "params": {...}, "reasoning": "..."}],
    "summary": "What you'll do"
}
Tools: senso_search (company policies), tavily_search (market data), reka_analyze (docs/video), yutori_browse (web portals)."""


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a plain English query through the AI orchestrator."""
    request_id = str(uuid.uuid4())

    # Get execution plan from LLM
    plan = await openrouter_client.structured_output(prompt=request.message, system=SYSTEM_PROMPT)

    tools_used = []
    results = []

    for step in plan.get("steps", []):
        tool = step.get("tool", "")
        params = step.get("params", {})
        try:
            if tool == "senso_search":
                result = await senso_client.search_policy(params.get("query", request.message))
            elif tool == "tavily_search":
                result = await tavily_client.search(params.get("query", request.message))
            else:
                result = {"info": f"Tool {tool} execution planned"}
            tools_used.append(tool)
            results.append({"tool": tool, "result": result})

            try:
                await neo4j_client.log_completion("Orchestrator", tool,
                                                    json.dumps(result, default=str)[:500],
                                                    tool, request_id)
            except Exception:
                pass
        except Exception as e:
            results.append({"tool": tool, "error": str(e)})

    # Generate summary
    summary_resp = await openrouter_client.chat(
        messages=[
            {"role": "system", "content": "Summarize concisely what backoffice.ai found."},
            {"role": "user", "content": f"Request: {request.message}\nResults: {json.dumps(results, default=str)[:3000]}"}
        ], max_tokens=500)
    response_text = summary_resp["choices"][0]["message"]["content"]

    return QueryResponse(response=response_text, tools_used=tools_used,
                          reasoning=plan.get("summary"), hire_request_id=request_id)
