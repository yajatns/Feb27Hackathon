"""Tavily API client — market research, salary benchmarks, regulatory data.

Supports both quick search and deep research modes.
Used by Finance Agent (salary benchmarks) and Compliance Agent (regulatory info).
"""

import httpx
from app.config import settings


class TavilyClient:
    def __init__(self):
        self.base_url = settings.tavily_base_url
        self.api_key = settings.tavily_api_key
        self.client = httpx.AsyncClient(timeout=60.0)

    async def search(self, query: str, max_results: int = 5,
                     search_depth: str = "basic") -> dict:
        """Quick search — good for salary lookups, basic questions."""
        resp = await self.client.post(f"{self.base_url}/search",
                                       json={"api_key": self.api_key, "query": query,
                                             "max_results": max_results, "search_depth": search_depth})
        resp.raise_for_status()
        return resp.json()

    async def research(self, query: str) -> dict:
        """Deep research — thorough analysis with answer synthesis."""
        resp = await self.client.post(f"{self.base_url}/search",
                                       json={"api_key": self.api_key, "query": query,
                                             "max_results": 10, "search_depth": "advanced",
                                             "include_answer": True, "include_raw_content": False})
        resp.raise_for_status()
        return resp.json()

    async def salary_benchmark(self, role: str, location: str) -> dict:
        """Specialized salary benchmark search."""
        query = f"average salary for {role} in {location} 2026 compensation range"
        return await self.research(query)

    async def regulatory_check(self, role: str, location: str) -> dict:
        """Check employment regulations for a role + location."""
        query = f"employment regulations requirements for {role} in {location} labor law compliance 2026"
        return await self.search(query, max_results=5, search_depth="advanced")

    async def market_analysis(self, topic: str) -> dict:
        """General market analysis on any topic."""
        return await self.research(topic)

    async def close(self):
        await self.client.aclose()


tavily_client = TavilyClient()
