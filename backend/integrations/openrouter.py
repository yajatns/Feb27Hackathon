"""OpenRouter LLM client — Claude Sonnet via OpenRouter."""

import json
import httpx
from app.config import settings


class OpenRouterClient:
    def __init__(self):
        self.base_url = settings.openrouter_base_url
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.client = httpx.AsyncClient(timeout=120.0)

    async def chat(self, messages: list[dict], tools: list[dict] | None = None,
                   temperature: float = 0.3, max_tokens: int = 4096) -> dict:
        payload = {"model": self.model, "messages": messages,
                   "temperature": temperature, "max_tokens": max_tokens}
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        resp = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json",
                     "HTTP-Referer": "https://backoffice.ai",
                     "X-Title": "backoffice.ai"},
            json=payload)
        resp.raise_for_status()
        return resp.json()

    async def structured_output(self, prompt: str, system: str = "") -> dict:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload = {"model": self.model, "messages": messages,
                   "temperature": 0.2, "max_tokens": 4096,
                   "response_format": {"type": "json_object"}}
        resp = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}",
                     "Content-Type": "application/json",
                     "HTTP-Referer": "https://backoffice.ai",
                     "X-Title": "backoffice.ai"},
            json=payload)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"raw": content}

    async def close(self):
        await self.client.aclose()


openrouter_client = OpenRouterClient()
