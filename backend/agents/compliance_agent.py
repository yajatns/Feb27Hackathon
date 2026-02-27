"""Compliance Agent — regulatory monitoring and policy enforcement."""

import json
from agents.base import BaseAgent
from integrations.tavily import tavily_client
from integrations.senso import senso_client


class ComplianceAgent(BaseAgent):
    name = "Compliance"
    description = "Regulatory monitoring, policy enforcement, labor law compliance"
    tools = ["tavily_search", "senso_search"]

    async def execute(self, task: str, context: dict, hire_request_id: str) -> dict:
        location = context.get("location", "California")
        role = context.get("role", "")

        query = f"employment compliance requirements for {role} in {location} 2026"
        try:
            compliance_data = await tavily_client.search(query)
        except Exception as e:
            compliance_data = {"error": str(e)}

        # Also check internal compliance policies
        try:
            internal = await senso_client.search_policy(f"compliance checklist {role}")
        except Exception as e:
            internal = {"error": str(e)}

        result = {"external": compliance_data, "internal": internal}
        await self.log_action(
            task=f"Compliance check for {role} in {location}",
            result=json.dumps(result, default=str)[:1000],
            tool="tavily+senso",
            hire_request_id=hire_request_id)

        return {"agent": self.name, "tool": "tavily+senso", "result": result}


compliance_agent = ComplianceAgent()
