"""Reka Vision API client — document and video intelligence. Vision ONLY."""

import httpx
from app.config import settings


class RekaClient:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=120.0)

    @property
    def api_key(self):
        return settings.reka_api_key

    @property
    def base_url(self):
        return settings.reka_base_url

    @property
    def headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    async def upload_video(self, video_url: str, name: str = "backoffice-upload") -> dict:
        resp = await self.client.post(f"{self.base_url}/v1/videos/upload",
                                       headers=self.headers, json={"url": video_url, "name": name})
        resp.raise_for_status()
        return resp.json()

    async def qa_chat(self, video_id: str, question: str) -> dict:
        resp = await self.client.post(f"{self.base_url}/v1/qa/chat",
                                       headers=self.headers,
                                       json={"video_id": video_id, "question": question})
        resp.raise_for_status()
        return resp.json()

    async def get_clips(self, video_id: str, query: str = "") -> dict:
        resp = await self.client.post(f"{self.base_url}/v1/clips",
                                       headers=self.headers,
                                       json={"video_id": video_id, "query": query})
        resp.raise_for_status()
        return resp.json()

    async def analyze_image(self, image_url: str, question: str) -> dict:
        resp = await self.client.post(f"{self.base_url}/v1/qa/chat",
                                       headers=self.headers,
                                       json={"image_url": image_url, "question": question})
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self.client.aclose()


reka_client = RekaClient()
