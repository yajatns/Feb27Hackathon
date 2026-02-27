"""POST /api/query — plain English to tool routing via orchestrator with function calling."""

import json
import uuid
from fastapi import APIRouter
from models.schemas import QueryRequest, QueryResponse
from integrations.openrouter import openrouter_client
from integrations.senso import senso_client
from integrations.tavily import tavily_client
from integrations.reka import reka_client
from integrations.yutori import yutori_client
from integrations.neo4j_client import neo4j_client

router = APIRouter()

SYSTEM_PROMPT = """You are the backoffice.ai orchestrator — one AI that runs an entire back office.

You have these tools:
- senso_search: Search company policies, salary bands, HR rules, compliance requirements
- tavily_search: Research external market data — salary benchmarks, regulatory info, industry trends
- reka_analyze: Analyze documents or videos — resume parsing, ID verification, training video compliance
- yutori_browse: Automate web portals with no API — insurance enrollment, government filings, benefits

When a user asks something, use the right tools to answer. Chain them when needed.
For hiring: senso_search (policies) → tavily_search (benchmarks) → decide → yutori_browse (enroll)
For compliance: tavily_search (regulations) + senso_search (internal policies) → compare
For documents: reka_analyze → extract info → senso_search (verify against policy)

Always explain your reasoning."""

TOOLS = [
    {"type": "function", "function": {
        "name": "senso_search",
        "description": "Search company knowledge base for policies, salary bands, HR rules, compliance requirements",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "What to search for in company policies"}
        }, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "tavily_search",
        "description": "Search external market data — salary benchmarks, regulatory info, industry trends, competitor analysis",
        "parameters": {"type": "object", "properties": {
            "query": {"type": "string", "description": "Search query for market research"},
            "search_depth": {"type": "string", "enum": ["basic", "advanced"], "description": "basic=fast, advanced=thorough"}
        }, "required": ["query"]}}},
    {"type": "function", "function": {
        "name": "reka_analyze",
        "description": "Analyze a document or video using vision AI — resume parsing, ID verification, training video compliance check",
        "parameters": {"type": "object", "properties": {
            "url": {"type": "string", "description": "URL of the document, image, or video to analyze"},
            "question": {"type": "string", "description": "What to analyze or extract from the content"}
        }, "required": ["url", "question"]}}},
    {"type": "function", "function": {
        "name": "yutori_browse",
        "description": "Automate a web portal task — insurance enrollment, government filings, benefits setup, any site without an API",
        "parameters": {"type": "object", "properties": {
            "task": {"type": "string", "description": "Plain English description of what to do on the portal"},
            "start_url": {"type": "string", "description": "URL of the portal to automate"}
        }, "required": ["task"]}}},
]


async def _execute_tool(name: str, args: dict) -> dict:
    """Execute a tool call with the real API client."""
    try:
        if name == "senso_search":
            return await senso_client.search_policy(args.get("query", ""))
        elif name == "tavily_search":
            return await tavily_client.search(args.get("query", ""),
                                               search_depth=args.get("search_depth", "basic"))
        elif name == "reka_analyze":
            upload = await reka_client.upload_video(args.get("url", ""))
            vid = upload.get("id", upload.get("video_id", ""))
            if vid:
                return await reka_client.qa_chat(vid, args.get("question", "Analyze this"))
            return upload
        elif name == "yutori_browse":
            result = await yutori_client.create_task(task=args.get("task", ""),
                                                      start_url=args.get("start_url", ""))
            tid = result.get("id", result.get("task_id", ""))
            if tid:
                return await yutori_client.wait_for_task(tid, max_polls=10)
            return result
        else:
            return {"error": f"Unknown tool: {name}"}
    except Exception as e:
        return {"error": str(e)}


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a plain English query using OpenRouter function calling."""
    request_id = str(uuid.uuid4())
    tools_used = []
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": request.message},
    ]

    # Call LLM with tools — handle multi-turn tool calling loop
    max_rounds = 5
    for _ in range(max_rounds):
        response = await openrouter_client.chat(messages=messages, tools=TOOLS)
        choice = response["choices"][0]
        msg = choice["message"]

        # If no tool calls, we have the final answer
        if not msg.get("tool_calls"):
            break

        # Append assistant message with tool calls
        messages.append(msg)

        # Execute each tool call
        for tc in msg["tool_calls"]:
            fn_name = tc["function"]["name"]
            fn_args = json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str) else tc["function"]["arguments"]

            result = await _execute_tool(fn_name, fn_args)
            tools_used.append(fn_name)

            # Log to Neo4j
            try:
                await neo4j_client.log_completion("Orchestrator", fn_name,
                                                    json.dumps(result, default=str)[:500],
                                                    fn_name, request_id)
            except Exception:
                pass

            # Append tool result for next LLM turn
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": json.dumps(result, default=str)[:3000],
            })

    # Final response
    final_text = msg.get("content", "Processing complete.")

    return QueryResponse(
        response=final_text,
        tools_used=list(set(tools_used)),
        reasoning=f"Used {len(tools_used)} tool calls across {len(set(tools_used))} unique tools",
        hire_request_id=request_id,
    )
