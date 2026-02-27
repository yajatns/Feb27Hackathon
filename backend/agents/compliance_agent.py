"""Compliance Agent — AI-powered regulatory compliance checker with LLM reasoning."""

from agents.llm_agent import LLMAgent
from integrations.tavily import tavily_client
from integrations.senso import senso_client


class ComplianceAgent(LLMAgent):
    name = "Compliance"
    role = "Compliance Officer"
    persona = """You are the AI Compliance Officer at backoffice.ai.

Your job is to ensure all hiring decisions comply with labor laws and company policies.
You have access to:
- Tavily: for researching current labor laws, regulations, and compliance requirements
- Senso: for checking internal compliance policies and checklists

When given a hire request:
1. Research labor laws for the location (state/city employment laws)
2. Check internal compliance policies
3. Identify any regulatory requirements (benefits, equal pay, etc.)
4. Flag any compliance risks or required actions

Be thorough — missing a compliance requirement can be costly."""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "research_regulations",
                "description": "Research employment regulations, labor laws, and compliance requirements for a specific role and location.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Regulatory research query"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "check_internal_compliance",
                "description": "Search internal compliance policies and checklists via Senso.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Internal compliance policy query"}
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    async def _execute_tool(self, name: str, args: dict) -> dict:
        if name == "research_regulations":
            try:
                return await tavily_client.regulatory_check(args["query"], "")
            except Exception as e:
                return {"error": str(e)}
        elif name == "check_internal_compliance":
            try:
                return await senso_client.search_policy(args["query"])
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"Unknown tool: {name}"}


compliance_agent = ComplianceAgent()
