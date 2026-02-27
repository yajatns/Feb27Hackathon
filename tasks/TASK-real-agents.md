# URGENT: Refactor to Real AI Agents (1 hour deadline)

## What's wrong now
- Hire pipeline agents (Maya, Sam, etc.) are just Python functions calling APIs directly
- No LLM reasoning, no tool selection, no autonomy
- The `/api/query` endpoint IS agentic (LLM picks tools) but hire is not

## What we need
Every agent should be an LLM-powered agent that:
1. Receives a task in natural language
2. Uses OpenRouter function calling to decide what tools to use
3. Reasons about the results
4. Returns a structured response with its reasoning

## Architecture
```
User → Orchestrator Agent (LLM) → decides which specialists to call
  → Maya Agent (LLM + Senso tools) → reasons about HR policies
  → Sam Agent (LLM + Tavily tools) → reasons about salary data
  → Compliance Agent (LLM + Tavily+Senso tools) → reasons about regulations
  → Alex Agent (LLM + Yutori tools) → reasons about provisioning
  → Aria Agent (LLM + Airbyte tools) → reasons about integrations
Orchestrator → synthesizes all agent responses → final decision
```

Each agent call is: system prompt + tools → OpenRouter → tool calls → results → reasoning
