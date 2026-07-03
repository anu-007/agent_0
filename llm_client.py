import json
from typing import List, Dict
import httpx
from openrouter import OpenRouter


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
        try:
            return await self._chat_sdk(messages, max_tokens)
        except Exception as e:
            # The openrouter SDK sometimes fails to parse certain model responses.
            # Fall back to a direct HTTP call using httpx.
            print(f"[LLMClient] SDK call failed: {e}. Falling back to httpx.")
            return await self._chat_http(messages, max_tokens)

    async def _chat_sdk(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        with OpenRouter(api_key=self.api_key) as client:
            response = client.chat.send(
                model=self.provider,
                messages=messages,
                max_tokens=max_tokens,
            )
            print(response)
        return response.choices[0].message.content

    async def _chat_http(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
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
            response.raise_for_status()
            data = response.json()
            if "choices" not in data or not data["choices"]:
                raise ValueError(f"OpenRouter returned no choices: {json.dumps(data)}")
            return data["choices"][0]["message"]["content"]