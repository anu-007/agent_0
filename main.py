import argparse
import asyncio
import os
from agent import CodingAgent
from dotenv import load_dotenv
from llm_client import LLMClient
from tools import create_default_registry

load_dotenv()


async def interactive(coding_agent):
    print("Agent 0 ready. Type 'exit' to quit.")
    while True:
        try:
            instruction = input("> ")
        except (EOFError, KeyboardInterrupt):
            break
        if instruction.strip().lower() in {"exit", "quit"}:
            break
        try:
            response = await coding_agent.synthesize_and_run(instruction)
            print(response)
        except Exception as e:
            print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Agent 0, an intern coding agent")
    parser.add_argument('--provider', type=str, default="tencent/hy3:free", help="llm model")
    parser.add_argument('--key', type=str, default=None, help='api key for the llm')
    args = parser.parse_args()

    provider = args.provider or os.environ.get("LLM_PROVIDER", "tencent/hy3:free")
    api_key = args.key or os.environ.get("LLM_API_KEY")

    if not api_key:
        raise AttributeError("ERROR: API key not found, Use --key, LLM_API_KEY env var")

    llm = LLMClient(provider=provider, api_key=api_key)
    registry = create_default_registry(llm)
    coding_agent = CodingAgent(llm, registry)

    try:
        asyncio.run(interactive(coding_agent))
    except KeyboardInterrupt:
        print("\nBye !!")
    except Exception as e:
        print(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
