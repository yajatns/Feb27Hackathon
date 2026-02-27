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

        # External regulatory check via Tavily
        try:
            external = await tavily_client.regulatory_check(role, location)
        except Exception as e:
            external = {"error": str(e)}

        # Internal compliance policies via Senso
        try:
            internal = await senso_client.search_policy(f"compliance checklist {role} {location}")
        except Exception as e:
            internal = {"error": str(e)}

        result = {"external_regulations": external, "internal_policies": internal}
        await self.log_action(
            task=f"Compliance check for {role} in {location}",
            result=json.dumps(result, default=str)[:1000],
            tool="tavily+senso",
            hire_request_id=hire_request_id)

        return {"agent": self.name, "tool": "tavily+senso", "result": result}


compliance_agent = ComplianceAgent()
