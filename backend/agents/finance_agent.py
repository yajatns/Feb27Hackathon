"""Sam — AI-powered Finance Agent. Uses LLM reasoning + Tavily to research market compensation."""

from agents.llm_agent import LLMAgent
from integrations.tavily import tavily_client


class FinanceAgent(LLMAgent):
    name = "Sam"
    role = "Finance Analyst"
    persona = """You are Sam, an AI finance analyst at backoffice.ai.

Your job is to research market salary data and compensation benchmarks.
You have access to Tavily, a deep research tool that searches the web for real-time data.

When given a hire request:
1. Research current market salary for the role in the specified location
2. Compare the proposed salary against market data
3. Provide a recommendation: is the offer competitive? Too high? Too low?
4. Cite specific data sources and numbers

Be data-driven. Use real numbers from your research, not guesses."""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "research_salary",
                "description": "Research market salary data for a role and location using Tavily deep web search. Returns real salary data from multiple sources.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "role": {"type": "string", "description": "Job title to research"},
                        "location": {"type": "string", "description": "City/region for salary data"}
                    },
                    "required": ["role", "location"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "market_analysis",
                "description": "Perform broader market analysis for industry trends, hiring conditions, and compensation trends.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Market research query"}
                    },
                    "required": ["query"]
                }
            }
        }
    ]

    async def _execute_tool(self, name: str, args: dict) -> dict:
        if name == "research_salary":
            try:
                return await tavily_client.salary_benchmark(args["role"], args["location"])
            except Exception as e:
                return {"error": str(e)}
        elif name == "market_analysis":
            try:
                return await tavily_client.market_analysis(args["query"])
            except Exception as e:
                return {"error": str(e)}
        return {"error": f"Unknown tool: {name}"}


finance_agent = FinanceAgent()
