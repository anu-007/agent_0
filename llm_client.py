import json
from typing import List, Dict
import httpx


class LLMClient:
    def __init__(self, provider: str, api_key: str = None, base_url: str = None):
        self.provider = provider
        self.api_key = api_key

        # Detect Ollama: either provider starts with "ollama/" or base_url points
        # to a local Ollama server.
        self.is_ollama = (
            provider.startswith("ollama/")
            or (base_url is not None and ("localhost:11434" in base_url or "127.0.0.1:11434" in base_url))
        )

        if self.is_ollama:
            self.base_url = base_url or "http://localhost:11434"
            self.model = provider.replace("ollama/", "") if provider.startswith("ollama/") else provider
            self.headers = {
                "Content-Type": "application/json",
            }
        else:
            self.base_url = base_url or "https://openrouter.ai/api/v1"
            self.model = provider
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

    async def chat(self, messages: List[Dict[str, str]], max_tokens: int = 2048) -> str:
        if self.is_ollama:
            return await self._chat_ollama(messages, max_tokens)
        return await self._chat_openrouter(messages, max_tokens)

    async def _chat_openrouter(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        payload = {
            "model": self.model,
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
                    f"Model: {self.model}"
                ) from e
            data = response.json()
            if "choices" not in data or not data["choices"]:
                raise ValueError(f"OpenRouter returned no choices: {json.dumps(data)}")

            message = data["choices"][0].get("message", {})
            content = message.get("content")
            if content is None or content == "":
                # Some reasoning models return output in the "reasoning" field.
                content = message.get("reasoning")
            if content is None or content == "":
                raise ValueError(
                    f"OpenRouter returned empty content for model {self.model}: {json.dumps(data)}"
                )
            return content

    async def _chat_ollama(self, messages: List[Dict[str, str]], max_tokens: int) -> str:
        # Qwen3 models think by default, which consumes tokens without producing
        # visible content. Prefix with /no_think to keep responses actionable.
        if "qwen3" in self.model.lower():
            messages = [dict(m) for m in messages]
            if messages and messages[0].get("role") == "system":
                messages[0] = {
                    **messages[0],
                    "content": "/no_think\n" + messages[0].get("content", ""),
                }
            else:
                messages.insert(0, {"role": "system", "content": "/no_think"})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7,
            },
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                headers=self.headers,
                json=payload,
                timeout=120,
            )
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                body = response.text or "<empty body>"
                raise RuntimeError(
                    f"Ollama request failed: {e.response.status_code} {e.response.reason_phrase}\n"
                    f"URL: {e.response.url}\n"
                    f"Response body: {body}\n"
                    f"Model: {self.model}"
                ) from e
            data = response.json()
            message = data.get("message", {})
            content = message.get("content")
            if content is None or content == "":
                content = message.get("thinking")
            if content is None or content == "":
                raise ValueError(
                    f"Ollama returned empty content for model {self.model}: {json.dumps(data)}"
                )
            return content