"""Senso API client — policy ground truth + self-improvement engine."""

import httpx
from app.config import settings


class SensoClient:
    def __init__(self):
        self.base_url = settings.senso_base_url
        self.api_key = settings.senso_api_key
        self.client = httpx.AsyncClient(timeout=30.0)

    @property
    def headers(self) -> dict:
        return {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    async def search_policy(self, query: str, top_k: int = 5) -> dict:
        resp = await self.client.post(f"{self.base_url}/org/search/context",
                                       headers=self.headers, json={"query": query, "top_k": top_k})
        resp.raise_for_status()
        return resp.json()

    async def upload_policy(self, filename: str, content: bytes, content_type: str = "application/pdf") -> dict:
        resp = await self.client.post(f"{self.base_url}/org/ingestion/upload",
                                       headers=self.headers,
                                       json={"filename": filename, "content_type": content_type})
        resp.raise_for_status()
        upload_data = resp.json()
        upload_url = upload_data.get("upload_url") or upload_data.get("url")
        if upload_url:
            await self.client.put(upload_url, content=content,
                                   headers={"Content-Type": content_type})
        return upload_data

    async def close(self):
        await self.client.aclose()


senso_client = SensoClient()
