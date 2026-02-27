"""Alex — IT Agent. AI agent for account provisioning using Yutori portal automation."""

import json
from agents.base import BaseAgent
from integrations.yutori import yutori_client


class ITAgent(BaseAgent):
    name = "Alex"
    role = "IT Specialist"
    system_prompt = """You are Alex, the IT Specialist agent at backoffice.ai.
Your job is to provision employee accounts, set up benefits enrollment,
and automate portal interactions for new hires.

You have access to Yutori — a portal automation API that can navigate
web portals, fill forms, and complete enrollment processes.

When given a hire request:
1. Initiate benefits enrollment for the new employee
2. Check the enrollment status
3. Report what was provisioned and any manual steps needed

Be specific about what systems were set up and what's pending."""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "enroll_benefits",
                "description": "Initiate employee benefits enrollment by automating the benefits portal via Yutori. Handles health insurance, 401k, and other standard benefits.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_name": {"type": "string", "description": "Full name of the employee"},
                        "start_date": {"type": "string", "description": "Employment start date"},
                        "benefits_tier": {"type": "string", "description": "Benefits tier: standard, premium, executive", "default": "standard"}
                    },
                    "required": ["employee_name", "start_date"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "provision_accounts",
                "description": "Set up IT accounts and access credentials for a new employee — email, Slack, Jira, GitHub, etc.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "employee_name": {"type": "string", "description": "Full name of the employee"},
                        "department": {"type": "string", "description": "Department for access provisioning"},
                        "role": {"type": "string", "description": "Role for permission levels"}
                    },
                    "required": ["employee_name", "department"]
                }
            }
        }
    ]

    async def _execute_tool(self, tool_name: str, args: dict, context: dict, hire_request_id: str) -> dict:
        if tool_name == "enroll_benefits":
            try:
                result = await yutori_client.enroll_benefits(
                    employee_name=args["employee_name"],
                    start_date=args.get("start_date", context.get("start_date", "")))
                task_id = result.get("id", result.get("task_id", ""))
                if task_id:
                    status = await yutori_client.wait_for_task(task_id, max_polls=5)
                    return {"source": "yutori", "enrollment": status}
                return {"source": "yutori", "enrollment": result}
            except Exception as e:
                return {"source": "yutori", "error": str(e),
                        "fallback": {"status": "pending_manual",
                                     "employee": args["employee_name"],
                                     "action_needed": "Manual benefits portal enrollment required"}}

        elif tool_name == "provision_accounts":
            # Simulate account provisioning (would connect to real identity provider)
            return {"source": "internal",
                    "provisioned": {
                        "email": f"{args['employee_name'].lower().replace(' ', '.')}@alexsaas.com",
                        "slack": "Invited",
                        "jira": f"Added to {args.get('department', 'General')} board",
                        "github": f"Added to {args.get('department', 'General').lower()} team",
                        "status": "completed"
                    }}

        return {"error": f"Unknown tool: {tool_name}"}


it_agent = ITAgent()
