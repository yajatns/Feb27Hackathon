"""Maya — HR Agent. AI agent that reasons about HR policies using Senso."""

import json
from agents.base import BaseAgent
from integrations.senso import senso_client


class HRAgent(BaseAgent):
    name = "Maya"
    role = "HR Specialist"
    system_prompt = """You are Maya, the HR Specialist agent at backoffice.ai.
Your job is to look up company HR policies, salary bands, and onboarding requirements.
You have access to Senso — the company's policy knowledge base.

When given a hire request:
1. Search for relevant salary band policies for the role and department
2. Search for onboarding checklists and requirements
3. Analyze what you find and provide your HR recommendation

Be specific about what policies you found (or didn't find) and what they say."""

    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_hr_policy",
                "description": "Search the company's HR policy knowledge base (Senso) for salary bands, onboarding requirements, benefits eligibility, and HR procedures.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query for HR policies"}
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "search_onboarding_checklist",
                "description": "Search for onboarding checklists and new hire requirements by department and role.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "department": {"type": "string", "description": "Department name"},
                        "role": {"type": "string", "description": "Job role/title"}
                    },
                    "required": ["department"]
                }
            }
        }
    ]

    async def _execute_tool(self, tool_name: str, args: dict, context: dict, hire_request_id: str) -> dict:
        if tool_name == "search_hr_policy":
            try:
                result = await senso_client.search_policy(args["query"])
                return {"source": "senso", "query": args["query"], "results": result}
            except Exception as e:
                return {"source": "senso", "query": args["query"], "error": str(e),
                        "fallback": "Policy database returned no results — using company defaults"}

        elif tool_name == "search_onboarding_checklist":
            dept = args.get("department", "General")
            role = args.get("role", "")
            try:
                result = await senso_client.search_policy(f"onboarding checklist {dept} {role}")
                return {"source": "senso", "department": dept, "results": result}
            except Exception as e:
                return {"source": "senso", "error": str(e),
                        "fallback_checklist": ["Background check", "I-9 verification",
                                               "Tax forms (W-4)", "Benefits enrollment",
                                               "Equipment provisioning", "Access credentials"]}

        return {"error": f"Unknown tool: {tool_name}"}


hr_agent = HRAgent()
