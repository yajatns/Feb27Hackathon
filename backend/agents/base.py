"""Base agent class — each specialist is an LLM agent with tools."""

import json
from integrations.openrouter import openrouter_client
from integrations.neo4j_client import neo4j_client


class BaseAgent:
    """Base class for all specialist agents. Each agent is an LLM with tools."""

    name: str = "BaseAgent"
    role: str = ""
    system_prompt: str = ""
    tools: list[dict] = []

    async def execute(self, task: str, context: dict, hire_request_id: str) -> dict:
        """Run the agent: LLM reasons about the task, selects tools, executes them."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self._build_prompt(task, context)}
        ]

        tool_calls_made = []
        max_iterations = 3  # prevent infinite loops

        for _ in range(max_iterations):
            # LLM decides what to do
            response = await openrouter_client.chat(
                messages=messages,
                tools=self.tools if self.tools else None,
                temperature=0.3
            )

            choice = response["choices"][0]
            msg = choice["message"]

            # If the LLM wants to call tools
            if msg.get("tool_calls"):
                messages.append(msg)  # add assistant message with tool_calls

                for tc in msg["tool_calls"]:
                    fn_name = tc["function"]["name"]
                    fn_args = json.loads(tc["function"]["arguments"])

                    # Execute the tool
                    tool_result = await self._execute_tool(fn_name, fn_args, context, hire_request_id)
                    tool_calls_made.append({"tool": fn_name, "args": fn_args, "result_preview": str(tool_result)[:500]})

                    # Feed result back to LLM
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(tool_result, default=str)[:3000]
                    })

                    # Log to Neo4j
                    await self.log_action(task=fn_name, result=str(tool_result)[:1000],
                                          tool=fn_name, hire_request_id=hire_request_id)
            else:
                # LLM gave a final answer
                break

        final_response = msg.get("content", "Agent completed without response.")

        return {
            "agent": self.name,
            "role": self.role,
            "reasoning": final_response,
            "tool_calls": tool_calls_made,
            "tools_used": [tc["tool"] for tc in tool_calls_made]
        }

    def _build_prompt(self, task: str, context: dict) -> str:
        """Build the user prompt from task and context."""
        return f"""Task: {task}

Context:
- Employee: {context.get('employee_name', 'N/A')}
- Role: {context.get('role', 'N/A')}
- Department: {context.get('department', 'N/A')}
- Salary: ${context.get('salary', 0):,.0f}
- Location: {context.get('location', 'N/A')}
- Start Date: {context.get('start_date', 'N/A')}

Use your tools to complete this task. Reason step by step about what you need to do,
call the appropriate tools, then provide your analysis and recommendation."""

    async def _execute_tool(self, tool_name: str, args: dict, context: dict, hire_request_id: str) -> dict:
        """Execute a tool. Override in subclasses to add real tool implementations."""
        return {"error": f"Tool {tool_name} not implemented"}

    async def log_action(self, task: str, result: str, tool: str, hire_request_id: str):
        """Log action to Neo4j reasoning graph."""
        try:
            await neo4j_client.log_completion(
                agent_name=self.name, task=task, result=result[:1000],
                tool_used=tool, hire_request_id=hire_request_id)
        except Exception:
            pass
