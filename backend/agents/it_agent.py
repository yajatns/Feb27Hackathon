"""Alex — AI-powered IT Agent. Uses LLM reasoning + Yutori for portal automation."""

from agents.llm_agent import LLMAgent
from integrations.yutori import yutori_client


class ITAgent(LLMAgent):
    name = "Alex"
    role = "IT Operations"
    persona = """You are Alex, the AI IT Operations specialist at backoffice.ai.

Your job is to provision accounts and handle benefits enrollment for new hires.
You have access to Yutori, a web browsing automation tool that can interact with portals.

When given a hire request:
1. Set up benefits enrollment through the benefits portal
2. Report what was successfully provisioned
3. Flag anything that needs manual intervention

If tools fail, explain what manual steps are needed and provide a checklist."""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "enroll_benefits",
                "description": "Automate benefits enrollment through web portals using Yutori browser automation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_name": {"type": "string", "description": "Name of the employee to enroll"},
                        "start_date": {"type": "string", "description": "Employment start date"},
                        "benefits_type": {"type": "string", "description": "Type of benefits to enroll (health, dental, 401k, etc.)"}
                    },
                    "required": ["employee_name", "start_date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "browse_portal",
                "description": "Browse and interact with any web portal using Yutori automation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task": {"type": "string", "description": "What to do on the portal"},
                        "url": {"type": "string", "description": "URL of the portal"}
                    },
                    "required": ["task"]
                }
            }
        }
    ]

    async def _execute_tool(self, name: str, args: dict) -> dict:
        if name == "enroll_benefits":
            try:
                result = await yutori_client.enroll_benefits(
                    employee_name=args["employee_name"],
                    start_date=args.get("start_date", ""))
                task_id = result.get("id", result.get("task_id", ""))
                if task_id:
                    return await yutori_client.wait_for_task(task_id, max_polls=5)
                return result
            except Exception as e:
                return {"error": str(e), "fallback": "Manual enrollment required"}
        elif name == "browse_portal":
            try:
                return await yutori_client.browse(
                    task=args["task"],
                    start_url=args.get("url", "https://benefits.example.com"))
            except Exception as e:
                return {"error": str(e), "fallback": "Manual portal access required"}
        return {"error": f"Unknown tool: {name}"}


it_agent = ITAgent()
