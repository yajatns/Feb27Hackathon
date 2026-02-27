"""Maya — HR Agent. Handles policies, employee records, onboarding docs."""

import json
from agents.base import BaseAgent
from integrations.senso import senso_client


class HRAgent(BaseAgent):
    name = "Maya"
    description = "HR specialist — company policies, salary bands, employee records"
    tools = ["senso_search", "senso_upload"]

    async def execute(self, task: str, context: dict, hire_request_id: str) -> dict:
        role = context.get("role", "")
        department = context.get("department", "")
        location = context.get("location", "")

        # Search Senso for relevant HR policies
        query = f"salary band and HR policies for {role} in {department} at {location}"
        try:
            policy_result = await senso_client.search_policy(query)
        except Exception as e:
            policy_result = {"error": str(e), "fallback": "No policies found — using defaults"}

        await self.log_action(
            task=f"HR policy lookup for {role}",
            result=json.dumps(policy_result, default=str)[:1000],
            tool="senso_search",
            hire_request_id=hire_request_id)

        return {"agent": self.name, "tool": "senso_search", "result": policy_result}


hr_agent = HRAgent()
