from typing import Dict

class LLMClient:
    def __init__(self, provider:str, api_key:str = None):
        self.provider = provider
        self.api_key = api_key
    
    def complete(self, prompt: str, max_tokens: int = 512) -> str:
        pass