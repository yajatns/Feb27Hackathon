"""Orchestrator Agent — AI agent that decides which specialist agents to invoke."""

import json
from integrations.openrouter import openrouter_client
from integrations.neo4j_client import neo4j_client
from agents.hr_agent import hr_agent
from agents.finance_agent import finance_agent
from agents.compliance_agent import compliance_agent
from agents.it_agent import it_agent
from agents.airbyte_agent import airbyte_agent

ORCHESTRATOR_SYSTEM = """You are the backoffice.ai Orchestrator — an autonomous AI agent that manages
employee onboarding by coordinating specialist agents. You do NOT do the work yourself.
You delegate to specialist agents and synthesize their findings.

Available specialist agents:
1. **Maya (HR)** — Searches company HR policies and salary bands via Senso
2. **Sam (Finance)** — Researches market salary benchmarks via Tavily  
3. **Compliance** — Checks labor laws and internal compliance via Tavily + Senso
4. **Alex (IT)** — Provisions accounts and enrolls benefits via Yutori
5. **Aria (Airbyte)** — Syncs employee data to external systems (Notion, Salesforce, etc.)

For each hire request, decide which agents to invoke and in what order.
After receiving their results, synthesize a final recommendation.

**CRITICAL: If ANY agent flags a red flag (salary too low, compliance issue, etc.), your final
recommendation MUST prominently surface that flag. Do NOT approve a hire that has unresolved red flags.**

For example: If Sam says the salary is 50% below market, your recommendation should be:
"🚨 BLOCKED — Salary of $X is drastically below market rate of $Y. Cannot proceed until adjusted."

You communicate with agents via the delegate_to_agent tool. Each agent is autonomous —
they decide which of their own tools to use. You just tell them what you need.

Think step by step about what information you need and which agent can provide it."""

ORCHESTRATOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "delegate_to_maya",
            "description": "Delegate a task to Maya (HR Agent). She searches company HR policies, salary bands, and onboarding requirements via Senso.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "What you need Maya to do"}
                },
                "required": ["task"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_to_sam",
            "description": "Delegate a task to Sam (Finance Agent). He researches market salary benchmarks and compensation data via Tavily.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "What you need Sam to do"}
                },
                "required": ["task"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_to_compliance",
            "description": "Delegate a task to the Compliance Agent. They check labor laws and internal compliance policies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "What you need Compliance to verify"}
                },
                "required": ["task"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_to_alex",
            "description": "Delegate a task to Alex (IT Agent). He provisions accounts, sets up credentials, and enrolls benefits via Yutori.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "What you need Alex to provision"}
                },
                "required": ["task"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delegate_to_aria",
            "description": "Delegate a task to Aria (Airbyte Agent). She syncs employee data to external systems like Notion, Salesforce, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "What you need Aria to sync"}
                },
                "required": ["task"]
            }
        }
    }
]

AGENT_MAP = {
    "delegate_to_maya": ("Maya", hr_agent),
    "delegate_to_sam": ("Sam", finance_agent),
    "delegate_to_compliance": ("Compliance", compliance_agent),
    "delegate_to_alex": ("Alex", it_agent),
    "delegate_to_aria": ("Aria", airbyte_agent),
}


async def orchestrate_hire(context: dict, hire_request_id: str) -> dict:
    """Run the orchestrator agent — it decides which specialists to call."""

    prompt = f"""New hire request for {context.get('employee_name', 'N/A')}:
- Role: {context.get('role', 'N/A')}
- Department: {context.get('department', 'N/A')}
- Proposed Salary: ${context.get('salary', 0):,.0f}
- Location: {context.get('location', 'N/A')}
- Start Date: {context.get('start_date', 'N/A')}

Decide which specialist agents to invoke to process this hire request.
You should typically: check HR policies first, then benchmark salary,
then verify compliance, then provision IT accounts.
Delegate to each agent with a clear task description."""

    messages = [
        {"role": "system", "content": ORCHESTRATOR_SYSTEM},
        {"role": "user", "content": prompt}
    ]

    agent_results = []
    delegations = []
    max_iterations = 6

    for _ in range(max_iterations):
        response = await openrouter_client.chat(
            messages=messages,
            tools=ORCHESTRATOR_TOOLS,
            temperature=0.3
        )

        choice = response["choices"][0]
        msg = choice["message"]

        if msg.get("tool_calls"):
            messages.append(msg)

            for tc in msg["tool_calls"]:
                fn_name = tc["function"]["name"]
                fn_args = json.loads(tc["function"]["arguments"])

                if fn_name in AGENT_MAP:
                    agent_name, agent = AGENT_MAP[fn_name]

                    # Log delegation to Neo4j
                    try:
                        await neo4j_client.log_delegation(
                            "Orchestrator", agent_name, fn_args.get("task", ""),
                            f"Orchestrator delegated: {fn_args.get('task', '')}",
                            hire_request_id)
                    except Exception:
                        pass

                    # Run the specialist agent (it's also an LLM with tools)
                    result = await agent.execute(
                        task=fn_args.get("task", ""),
                        context=context,
                        hire_request_id=hire_request_id
                    )

                    agent_results.append(result)
                    delegations.append({
                        "agent": agent_name,
                        "task": fn_args.get("task", ""),
                        "tools_used": result.get("tools_used", []),
                        "reasoning": result.get("reasoning", "")[:500]
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps({
                            "agent": agent_name,
                            "reasoning": result.get("reasoning", ""),
                            "tools_used": result.get("tools_used", []),
                            "tool_calls": result.get("tool_calls", [])
                        }, default=str)[:3000]
                    })
                else:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": json.dumps({"error": f"Unknown agent: {fn_name}"})
                    })
        else:
            # Final synthesis from orchestrator
            break

    final_reasoning = msg.get("content", "Orchestrator completed pipeline.")

    return {
        "orchestrator_reasoning": final_reasoning,
        "delegations": delegations,
        "agent_results": agent_results,
        "total_agents_invoked": len(delegations),
        "total_tool_calls": sum(len(r.get("tool_calls", [])) for r in agent_results)
    }
