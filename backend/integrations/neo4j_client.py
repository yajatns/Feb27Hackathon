"""Neo4j client — System of Reasoning graph."""

from neo4j import AsyncGraphDatabase
from app.config import settings


class Neo4jClient:
    def __init__(self):
        self._driver = None

    @property
    def uri(self):
        return settings.neo4j_uri

    @property
    def user(self):
        return settings.neo4j_user

    @property
    def password(self):
        return settings.neo4j_password

    async def connect(self):
        self._driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
        await self._driver.verify_connectivity()

    async def close(self):
        if self._driver:
            await self._driver.close()

    async def run_query(self, query: str, params: dict | None = None) -> list[dict]:
        async with self._driver.session() as session:
            result = await session.run(query, params or {})
            return await result.data()

    async def log_delegation(self, from_agent: str, to_agent: str, task: str,
                              reasoning: str, hire_request_id: str) -> dict:
        query = """
        MERGE (f:Agent {name: $from_agent})
        MERGE (t:Agent {name: $to_agent})
        CREATE (f)-[r:DELEGATED {task: $task, reasoning: $reasoning,
                hire_request_id: $hire_request_id, timestamp: datetime()}]->(t)
        RETURN f.name AS from_agent, t.name AS to_agent, r.task AS task
        """
        results = await self.run_query(query, {"from_agent": from_agent, "to_agent": to_agent,
                                                "task": task, "reasoning": reasoning,
                                                "hire_request_id": hire_request_id})
        return results[0] if results else {}

    async def log_completion(self, agent_name: str, task: str, result: str,
                              tool_used: str, hire_request_id: str) -> dict:
        query = """
        MERGE (agent:Agent {name: $agent_name})
        CREATE (action:Action {task: $task, result: $result, tool_used: $tool_used,
                hire_request_id: $hire_request_id, timestamp: datetime()})
        CREATE (agent)-[:COMPLETED]->(action)
        RETURN agent.name AS agent, action.task AS task
        """
        results = await self.run_query(query, {"agent_name": agent_name, "task": task,
                                                "result": result, "tool_used": tool_used,
                                                "hire_request_id": hire_request_id})
        return results[0] if results else {}

    async def log_learned(self, override_field: str, original_value: str,
                           new_value: str, reason: str) -> dict:
        query = """
        CREATE (o:Override {field: $field, original: $original, new_val: $new_val,
                reason: $reason, timestamp: datetime()})
        CREATE (u:PolicyUpdate {field: $field, new_val: $new_val, timestamp: datetime()})
        CREATE (o)-[:LEARNED]->(u)
        RETURN o.field AS field, u.new_val AS new_value
        """
        results = await self.run_query(query, {"field": override_field, "original": original_value,
                                                "new_val": new_value, "reason": reason})
        return results[0] if results else {}

    async def get_full_graph(self, hire_request_id: str | None = None) -> dict:
        if hire_request_id:
            query = """MATCH (n)-[r]->(m)
            WHERE n.hire_request_id = $hrid OR m.hire_request_id = $hrid OR n.hire_request_id IS NULL
            RETURN n, labels(n) as n_labels, r, type(r) as r_type, m, labels(m) as m_labels LIMIT 200"""
            params = {"hrid": hire_request_id}
        else:
            query = "MATCH (n)-[r]->(m) RETURN n, labels(n) as n_labels, r, type(r) as r_type, m, labels(m) as m_labels LIMIT 200"
            params = {}
        records = await self.run_query(query, params)
        nodes, edges = {}, []
        for rec in records:
            for key, lbl_key in [("n", "n_labels"), ("m", "m_labels")]:
                node = rec.get(key, {})
                if isinstance(node, dict):
                    nid = node.get("name", node.get("task", str(hash(str(node)))))
                    if nid not in nodes:
                        labels = rec.get(lbl_key, ["Node"])
                        nodes[nid] = {"id": nid, "label": nid, "type": labels[0] if labels else "Node",
                                       "properties": node}
            edges.append({"source": str(rec.get("n", {}).get("name", "")),
                          "target": str(rec.get("m", {}).get("name", "")),
                          "type": rec.get("r_type", "RELATED"), "properties": {}})
        return {"nodes": list(nodes.values()), "edges": edges}


neo4j_client = Neo4jClient()
