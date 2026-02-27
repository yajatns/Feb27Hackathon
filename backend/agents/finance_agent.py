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

        # Use specialized salary benchmark method
        try:
            research = await tavily_client.salary_benchmark(role, location)
        except Exception as e:
            research = {"error": str(e), "fallback": f"Using proposed salary ${salary:,.0f} as baseline"}

        await self.log_action(
            task=f"Salary benchmark for {role} in {location}",
            result=json.dumps(research, default=str)[:1000],
            tool="tavily_research",
            hire_request_id=hire_request_id)

        return {"agent": self.name, "tool": "tavily_research", "result": research}


finance_agent = FinanceAgent()
