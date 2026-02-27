"""Sam — Finance Agent. AI agent that researches salary benchmarks using Tavily."""

import json
from agents.base import BaseAgent
from integrations.tavily import tavily_client


class FinanceAgent(BaseAgent):
    name = "Sam"
    role = "Finance Specialist"
    system_prompt = """You are Sam, the Finance Specialist agent at backoffice.ai.
Your job is to research market salary benchmarks, analyze compensation competitiveness,
and provide salary recommendations.

You have access to Tavily — a real-time web research API that pulls live data
from salary databases (salary.com, levels.fyi, glassdoor, etc.).

When given a hire request:
1. Research market salary benchmarks for the role and location
2. Compare the proposed salary against market data
3. Calculate the percentage difference from market average
4. **FLAG RED FLAGS AGGRESSIVELY:**
   - If proposed salary is >15% below market → 🚨 CRITICAL: Lowball offer, will not attract talent
   - If proposed salary is >10% below market → ⚠️ WARNING: Below competitive range
   - If proposed salary is >20% above market → ⚠️ WARNING: Overpaying vs market
5. Provide a CLEAR recommendation: APPROVE, ADJUST UP (with specific number), or REJECT

Be direct and data-driven. If someone proposes $120K for a Director of Engineering in SF
when market rate is $250K+, say that clearly — don't sugarcoat it.

Always cite specific data points and sources from your research."""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "research_salary_benchmark",
                "description": "Research current market salary benchmarks for a specific role and location using Tavily deep search. Returns real-time data from salary databases.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "description": "Job title/role to research"},
                        "location": {"type": "string", "description": "City or region for salary data"}
                    },
                    "required": ["role", "location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "research_compensation_trends",
                "description": "Research compensation trends and total comp packages for a role in a specific industry or market.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Compensation research query"}
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    async def _execute_tool(self, tool_name: str, args: dict, context: dict, hire_request_id: str) -> dict:
        if tool_name == "research_salary_benchmark":
            try:
                result = await tavily_client.salary_benchmark(args["role"], args["location"])
                return {"source": "tavily", "role": args["role"], "location": args["location"],
                        "research": result}
            except Exception as e:
                return {"source": "tavily", "error": str(e),
                        "fallback": f"Unable to fetch live data — using proposed salary as baseline"}

        elif tool_name == "research_compensation_trends":
            try:
                result = await tavily_client.search(args["query"])
                return {"source": "tavily", "query": args["query"], "results": result}
            except Exception as e:
                return {"source": "tavily", "error": str(e)}

        return {"error": f"Unknown tool: {tool_name}"}


finance_agent = FinanceAgent()
