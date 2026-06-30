import argparse
import asyncio
import os
from llm_client import LLMClient
from dotenv import load_dotenv

load_dotenv()

async def interactive(llm_client):
    print("Agent 0 ready. Type 'exit' to quit.")
    while True:
        try:
            prompt = input("> ")
        except (EOFError, KeyboardInterrupt):
            break
        if prompt.strip().lower() in {"exit", "quit"}:
            break
        response = await llm_client.complete(prompt)
        print(response)


def main():
    parser = argparse.ArgumentParser(description="Agent 0, a intern coding agent")
    parser.add_argument('--provider', type=str, default="anthropic-haiku", help="llm model")
    parser.add_argument('--key', type=str, default=None, help='api key for the llm')
    args = parser.parse_args()

    provider = args.provider or os.environ.get("LLM_PROVIDER", "anthropic-haiku")
    api_key = args.key or os.environ.get("LLM_API_KEY")

    if not api_key:
        raise SyntaxError("ERROR: API key not found, Use --key, LLM_API_KEY env var")

    llm_client = LLMClient(provider=provider, api_key=api_key)
    
    try:
        asyncio.run(interactive(llm_client))
    except KeyboardInterrupt:
        print("\nBye !!")

if __name__ == "__main__":
    main()
