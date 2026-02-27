"""Tavily API client — market research and external data."""

import httpx
from app.config import settings


class TavilyClient:
    def __init__(self):
        self.base_url = settings.tavily_base_url
        self.api_key = settings.tavily_api_key
        self.client = httpx.AsyncClient(timeout=60.0)

    async def search(self, query: str, max_results: int = 5, search_depth: str = "basic") -> dict:
        resp = await self.client.post(f"{self.base_url}/search",
                                       json={"api_key": self.api_key, "query": query,
                                             "max_results": max_results, "search_depth": search_depth})
        resp.raise_for_status()
        return resp.json()

    async def research(self, query: str) -> dict:
        resp = await self.client.post(f"{self.base_url}/search",
                                       json={"api_key": self.api_key, "query": query,
                                             "max_results": 10, "search_depth": "advanced",
                                             "include_answer": True})
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()


tavily_client = TavilyClient()
