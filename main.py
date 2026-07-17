import argparse
import asyncio
import os
from pathlib import Path
from agent import CodingAgent
from dotenv import load_dotenv
from llm_client import LLMClient
from retrieval import Embedder, Retriever, sync_index
from tools import create_default_registry, create_minimal_registry
from tools.registry import ToolRegistry

load_dotenv()

DEFAULT_WORKSPACE = Path("workspace")


async def get_or_build_retriever(workspace: Path):
    index_dir = workspace / ".agent0_index"
    store = await sync_index(root=workspace, index_dir=index_dir)
    return Retriever(store, Embedder())


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
    parser.add_argument(
        "--workspace",
        type=str,
        default=str(DEFAULT_WORKSPACE),
        help="Target folder for indexing, generation, and editing (default: workspace)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=os.environ.get("LLM_PROVIDER"),
        help="LLM model (default: LLM_PROVIDER from .env)",
    )
    parser.add_argument(
        "--key",
        type=str,
        default=os.environ.get("LLM_API_KEY"),
        help="API key for the LLM (default: LLM_API_KEY from .env; not needed for Ollama)",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=os.environ.get("LLM_BASE_URL"),
        help="Base URL for the LLM API (default: LLM_BASE_URL from .env; omit for OpenRouter)",
    )
    args = parser.parse_args()

    workspace = Path(args.workspace).resolve()
    workspace.mkdir(parents=True, exist_ok=True)

    if not args.provider:
        raise AttributeError(
            "ERROR: LLM provider not found. Set LLM_PROVIDER in .env or pass --provider."
        )

    is_ollama = (
        args.provider.startswith("ollama/")
        or (args.base_url and ("localhost:11434" in args.base_url or "127.0.0.1:11434" in args.base_url))
    )
    if not is_ollama and not args.key:
        raise AttributeError(
            "ERROR: API key not found. Set LLM_API_KEY in .env or pass --key."
        )

    llm = LLMClient(provider=args.provider, api_key=args.key, base_url=args.base_url)
    registry = (
        create_minimal_registry(llm, workspace=workspace)
        if is_ollama
        else create_default_registry(llm, workspace=workspace)
    )
    retriever = asyncio.run(get_or_build_retriever(workspace))
    coding_agent = CodingAgent(
        llm, registry, retriever, workspace=workspace, simple_mode=is_ollama
    )

    try:
        asyncio.run(interactive(coding_agent))
    except KeyboardInterrupt:
        print("\nBye !!")
    except Exception as e:
        print(f"Fatal error: {e}")


if __name__ == "__main__":
    main()
