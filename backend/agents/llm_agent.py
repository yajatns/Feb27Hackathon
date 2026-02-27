"""LLM-powered Agent base — every specialist agent uses OpenRouter function calling to reason and act."""

import json
import logging
from typing import Any

from integrations.openrouter import openrouter_client

logger = logging.getLogger(__name__)


class LLMAgent:
    """Base class for AI-powered specialist agents.
    
    Each agent has:
    - A persona (system prompt defining who they are)
    - Tools (functions they can call)
    - Reasoning loop (LLM decides what to do, calls tools, reasons about results)
    """
    
    name: str = "Agent"
    role: str = "Specialist"
    persona: str = ""
    tools: list[dict] = []
    
    async def execute(self, task: str, context: dict[str, Any], hire_request_id: str = "") -> dict:
        """Run the agent's reasoning loop.
        
        1. Send task + context to LLM with available tools
        2. LLM decides which tools to call (or none)
        3. Execute tool calls, feed results back
        4. LLM reasons about results and returns final answer
        """
        messages = [
            {"role": "system", "content": self.persona},
            {"role": "user", "content": f"""Task: {task}

Context:
{json.dumps(context, default=str, indent=2)}

Use your available tools to complete this task. Reason step by step about what you find.
Return your analysis and recommendations."""}
        ]
        
        max_iterations = 3
        tool_results = []
        
        for i in range(max_iterations):
            try:
                response = await openrouter_client.chat(
                    messages=messages,
                    tools=self.tools if self.tools else None,
                    temperature=0.3,
                    max_tokens=1500
                )
                
                choice = response["choices"][0]
                message = choice["message"]
                
                # Check if LLM wants to call tools
                tool_calls = message.get("tool_calls", [])
                
                if not tool_calls:
                    # Agent is done reasoning — return final response
                    return {
                        "agent": self.name,
                        "role": self.role,
                        "reasoning": message.get("content", ""),
                        "tool_calls_made": tool_results,
                        "iterations": i + 1
                    }
                
                # Execute tool calls
                messages.append(message)  # Add assistant message with tool_calls
                
                for tc in tool_calls:
                    fn_name = tc["function"]["name"]
                    fn_args = json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str) else tc["function"]["arguments"]
                    
                    logger.info(f"[{self.name}] Calling tool: {fn_name}({fn_args})")
                    
                    result = await self._execute_tool(fn_name, fn_args)
                    tool_results.append({"tool": fn_name, "args": fn_args, "result": result})
                    
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps(result, default=str)[:3000]
                    })
                    
            except Exception as e:
                logger.error(f"[{self.name}] Error in reasoning loop: {e}")
                return {
                    "agent": self.name,
                    "role": self.role,
                    "reasoning": f"Error during reasoning: {e}",
                    "tool_calls_made": tool_results,
                    "iterations": i + 1,
                    "error": str(e)
                }
        
        # Max iterations reached
        return {
            "agent": self.name,
            "role": self.role,
            "reasoning": "Reached maximum reasoning iterations.",
            "tool_calls_made": tool_results,
            "iterations": max_iterations
        }
    
    async def _execute_tool(self, name: str, args: dict) -> dict:
        """Override in subclass to execute tools."""
        return {"error": f"Tool {name} not implemented"}
