from openrouter import OpenRouter

class LLMClient:
    def __init__(self, provider:str, api_key:str = None):
        self.provider = provider
        self.api_key = api_key
    
    async def complete(self, prompt: str, max_tokens: int = 512) -> str:
        with OpenRouter(api_key=self.api_key) as client:
            response = client.chat.send(
                model=self.provider,
                messages=[
                    {"role": "user", "content": prompt}
                ],
            )
            print(response.choices[0].message.content)
        return response.choices[0].message.content