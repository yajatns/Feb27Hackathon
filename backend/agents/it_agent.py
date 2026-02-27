"""Alex — IT Agent. Handles account provisioning, portal automation, benefits."""

import json
from agents.base import BaseAgent
from integrations.yutori import yutori_client


class ITAgent(BaseAgent):
    name = "Alex"
    description = "IT specialist — account provisioning, portal automation, benefits enrollment"
    tools = ["yutori_browse"]

    async def execute(self, task: str, context: dict, hire_request_id: str) -> dict:
        employee_name = context.get("employee_name", "")
        start_date = context.get("start_date", "")
        location = context.get("location", "")

        # Use specialized benefits enrollment
        try:
            task_result = await yutori_client.enroll_benefits(
                employee_name=employee_name, start_date=start_date)
            task_id = task_result.get("id", task_result.get("task_id", ""))
            if task_id:
                result = await yutori_client.wait_for_task(task_id, max_polls=10)
            else:
                result = task_result
        except Exception as e:
            result = {"error": str(e), "fallback": "Manual enrollment required",
                      "employee": employee_name, "start_date": start_date}

        await self.log_action(
            task=f"Benefits enrollment for {employee_name}",
            result=json.dumps(result, default=str)[:1000],
            tool="yutori_browse",
            hire_request_id=hire_request_id)

        return {"agent": self.name, "tool": "yutori_browse", "result": result}


it_agent = ITAgent()
