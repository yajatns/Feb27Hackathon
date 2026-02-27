"""Compliance Agent — AI agent for regulatory monitoring using Tavily + Senso."""

import json
from agents.base import BaseAgent
from integrations.tavily import tavily_client
from integrations.senso import senso_client


class ComplianceAgent(BaseAgent):
    name = "Compliance"
    role = "Compliance Officer"
    system_prompt = """You are the Compliance Officer agent at backoffice.ai.
Your job is to verify that hiring decisions comply with labor laws, company policies,
and regulatory requirements.

You have access to:
- Tavily: Real-time web research for current labor laws and regulations
- Senso: Company's internal compliance policies and checklists

When given a hire request:
1. Check external labor laws and regulations for the role's location
2. Verify against internal compliance policies
3. **Check if salary is compliant with market standards and anti-exploitation laws**
   - A salary drastically below market (e.g. $120K for a Director in SF) may indicate a compliance risk
   - Flag potential equal pay violations or below-market offers that could indicate discrimination
4. Flag any issues or provide clearance with specific reasoning

Be thorough and aggressive about flagging risks — missed compliance issues are costly.
If you see a red flag, say it clearly: "🚨 COMPLIANCE FLAG: [issue]"."""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "check_labor_regulations",
                "description": "Research current labor laws, minimum wage, and employment regulations for a specific location and role type using Tavily.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "description": "Job role/title"},
                        "location": {"type": "string", "description": "City/state for regulatory lookup"}
                    },
                    "required": ["location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_internal_compliance",
                "description": "Search company's internal compliance policies and checklists via Senso.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Compliance policy search query"}
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    async def _execute_tool(self, tool_name: str, args: dict, context: dict, hire_request_id: str) -> dict:
        if tool_name == "check_labor_regulations":
            try:
                result = await tavily_client.regulatory_check(
                    args.get("role", context.get("role", "")),
                    args["location"])
                return {"source": "tavily", "location": args["location"], "regulations": result}
            except Exception as e:
                return {"source": "tavily", "error": str(e),
                        "fallback": "Standard federal + state employment law applies"}

        elif tool_name == "check_internal_compliance":
            try:
                result = await senso_client.search_policy(args["query"])
                return {"source": "senso", "query": args["query"], "policies": result}
            except Exception as e:
                return {"source": "senso", "error": str(e),
                        "fallback": "Using standard compliance checklist"}

        return {"error": f"Unknown tool: {tool_name}"}


compliance_agent = ComplianceAgent()
