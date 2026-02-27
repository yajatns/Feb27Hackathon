"""Base agent class for specialist agents."""

from integrations.openrouter import openrouter_client
from integrations.neo4j_client import neo4j_client


class BaseAgent:
    """Base class for all specialist agents."""

    name: str = "BaseAgent"
    description: str = ""
    tools: list[str] = []

    async def execute(self, task: str, context: dict, hire_request_id: str) -> dict:
        """Execute a task. Override in subclasses."""
        raise NotImplementedError

    async def think(self, prompt: str, system: str = "") -> dict:
        """Use LLM to reason about a task."""
        return await openrouter_client.structured_output(prompt=prompt, system=system)

    async def log_action(self, task: str, result: str, tool: str, hire_request_id: str):
        """Log action to Neo4j."""
        try:
            await neo4j_client.log_completion(
                agent_name=self.name, task=task, result=result[:1000],
                tool_used=tool, hire_request_id=hire_request_id)
        except Exception:
            pass  # Neo4j is optional, don't block execution
