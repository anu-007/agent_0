import argparse
import asyncio
import os
from agent import CodingAgent
from dotenv import load_dotenv
from llm_client import LLMClient

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
        response = await coding_agent.synthesize_and_run(instruction)
        print(response)


def main():
    parser = argparse.ArgumentParser(description="Agent 0, a intern coding agent")
    parser.add_argument('--provider', type=str, default="nvidia/nemotron-3-ultra-550b-a55b:free", help="llm model")
    parser.add_argument('--key', type=str, default=None, help='api key for the llm')
    args = parser.parse_args()

    provider = args.provider or os.environ.get("LLM_PROVIDER", "nvidia/nemotron-3-ultra-550b-a55b:free")
    api_key = args.key or os.environ.get("LLM_API_KEY")

    if not api_key:
        raise SyntaxError("ERROR: API key not found, Use --key, LLM_API_KEY env var")

    coding_agent = CodingAgent(LLMClient(provider=provider, api_key=api_key))
    
    try:
        asyncio.run(interactive(coding_agent))
    except KeyboardInterrupt:
        print("\nBye !!")

if __name__ == "__main__":
    main()
