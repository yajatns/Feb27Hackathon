"""Sam — Finance Agent. Handles salary benchmarks, payroll, compensation."""

import json
from agents.base import BaseAgent
from integrations.tavily import tavily_client


class FinanceAgent(BaseAgent):
    name = "Sam"
    description = "Finance specialist — salary benchmarks, payroll setup, compensation analysis"
    tools = ["tavily_search", "tavily_research"]

    async def execute(self, task: str, context: dict, hire_request_id: str) -> dict:
        role = context.get("role", "")
        location = context.get("location", "")
        salary = context.get("salary", 0)

        query = f"average salary for {role} in {location} 2026"
        try:
            research = await tavily_client.search(query, search_depth="advanced")
        except Exception as e:
            research = {"error": str(e), "fallback": "Using provided salary as baseline"}

        await self.log_action(
            task=f"Salary benchmark for {role} in {location}",
            result=json.dumps(research, default=str)[:1000],
            tool="tavily_search",
            hire_request_id=hire_request_id)

        return {"agent": self.name, "tool": "tavily_search", "result": research}


finance_agent = FinanceAgent()
