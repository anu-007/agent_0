import asyncio
from pathlib import Path
from typing import List, Dict

from retrieval.embedder import Embedder
from retrieval.indexer import scan_codebase
from retrieval.store import VectorStore


DEFAULT_INDEX_DIR = Path(".agent0_index")


async def build_index(
    root: Path = None,
    index_dir: Path = DEFAULT_INDEX_DIR,
    embedder: Embedder = None,
) -> VectorStore:
    """Scan the codebase, embed it, and save the FAISS index."""
    embedder = embedder or Embedder()
    loop = asyncio.get_running_loop()

    # Ensure the store dimension is known even if the workspace is empty.
    dim = embedder.model.get_embedding_dimension()

    chunks = scan_codebase(root)
    store = VectorStore(dim)
    if chunks:
        texts = [f"{c['path']}\n{c['content']}" for c in chunks]
        embeddings = await loop.run_in_executor(None, embedder.encode, texts)
        store.add(chunks, embeddings)
    store.save(index_dir)
    return store


async def load_index(
    index_dir: Path = DEFAULT_INDEX_DIR,
) -> VectorStore:
    """Load a previously built FAISS index."""
    index_file = index_dir / "index.faiss"
    chunks_file = index_dir / "chunks.json"
    if not index_file.exists() or not chunks_file.exists():
        raise RuntimeError(f"Index not found at {index_dir}. Build it first.")
    store = VectorStore(0)
    store.load(index_dir)
    return store


def format_context(
    results: List[Dict],
    max_chars: int = 8000,
    max_chunks: int = 15,
) -> str:
    """Format retrieved chunks into a prompt string with budget and deduplication."""
    parts = ["Relevant codebase context:"]
    seen = set()
    used = 0

    for result in results[:max_chunks]:
        key = (
            f"{result['path']}:{result.get('start_line', 0)}-"
            f"{result.get('end_line', 0)}:{result.get('name', '')}"
        )
        if key in seen:
            continue
        seen.add(key)

        header = (
            f"\nFile: {result['path']}"
        )
        if result.get("name"):
            header += f" ({result['type']}: {result['name']}, lines {result.get('start_line', 0)}-{result.get('end_line', 0)})"
        else:
            header += f" (module, lines {result.get('start_line', 0)}-{result.get('end_line', 0)})"
        header += "\n```python\n"

        content = result["content"]
        footer = "\n```\n"
        total = len(header) + len(content) + len(footer)

        if used + total > max_chars:
            remaining = max_chars - used
            if remaining > len(header) + len(footer) + 100:
                content = content[: remaining - len(header) - len(footer)]
                parts.append(header + content + footer)
            break

        parts.append(header + content + footer)
        used += total

    return "\n".join(parts)


class Retriever:
    def __init__(self, store: VectorStore, embedder: Embedder):
        self.store = store
        self.embedder = embedder

    async def retrieve(self, query: str, k: int = 8) -> List[Dict]:
        loop = asyncio.get_running_loop()
        embedding = await loop.run_in_executor(
            None, self.embedder.encode, [f"{query}\n"]
        )
        return self.store.search(embedding, k=k)
