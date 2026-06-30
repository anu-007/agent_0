from typing import Dict

class LLMClient:
    def __init__(self, provider:str, api_key:str = None):
        self.provider = provider
        self.api_key = api_key
        self.history = []
    
    async def complete(self, prompt: str, max_tokens: int = 512) -> str:
        self.history.append({"role": "user", "content": prompt})
        response = f"got prompt {prompt}"
        self.history.append({"role": "agent", "content": response})
        return response