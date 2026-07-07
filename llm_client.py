import json
from typing import List, Dict
import httpx


class LLMClient:
    def __init__(self, provider: str, api_key: str = None):
        self.provider = provider
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Agent 0",
        }

    async def complete(self, prompt: str, max_tokens: int = 512) -> str:
        return await self.chat(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )

    async def chat(self, messages: List[Dict[str, str]], max_tokens: int = 512) -> str:
        payload = {
            "model": self.provider,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=60,
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                body = response.text or "<empty body>"
                raise RuntimeError(
                    f"OpenRouter request failed: {e.response.status_code} {e.response.reason_phrase}\n"
                    f"URL: {e.response.url}\n"
                    f"Response body: {body}\n"
                    f"Model: {self.provider}"
                ) from e
            data = response.json()
            if "choices" not in data or not data["choices"]:
                raise ValueError(f"OpenRouter returned no choices: {json.dumps(data)}")
            return data["choices"][0]["message"]["content"]