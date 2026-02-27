"""Maya — AI-powered HR Agent. Uses LLM reasoning + Senso tools to analyze HR policies."""

from agents.llm_agent import LLMAgent
from integrations.senso import senso_client


class HRAgent(LLMAgent):
    name = "Maya"
    role = "HR Specialist"
    persona = """You are Maya, an AI HR specialist at backoffice.ai.

Your job is to look up company HR policies and salary bands for new hires.
You have access to Senso, the company's policy knowledge base.

When given a hire request:
1. Search for relevant salary band policies for the role and department
2. Search for onboarding requirements and checklists
3. Analyze whether the proposed salary fits within company policy
4. Flag any policy concerns

Be specific about what you found (or didn't find) in the policy database.
If no policies are found, explicitly say so and recommend creating them."""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_hr_policy",
                "description": "Search the company's HR policy database (Senso) for relevant policies, salary bands, and guidelines.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural language search query for HR policies"}
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    async def _execute_tool(self, name: str, args: dict) -> dict:
        if name == "search_hr_policy":
            try:
                return await senso_client.search_policy(args["query"])
            except Exception as e:
                return {"error": str(e), "note": "Policy database unavailable — recommend manual review"}
        return {"error": f"Unknown tool: {name}"}


hr_agent = HRAgent()
