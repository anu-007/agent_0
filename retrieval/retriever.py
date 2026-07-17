import asyncio
from pathlib import Path
from typing import List, Dict

from retrieval.chunker import chunk_file
from retrieval.embedder import Embedder
from retrieval.indexer import scan_codebase, scan_files_with_hashes
from retrieval.manifest import Manifest
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


async def sync_index(
    root: Path = None,
    index_dir: Path = DEFAULT_INDEX_DIR,
    embedder: Embedder = None,
) -> VectorStore:
    """Update the index incrementally: re-embed only changed files.

    Args:
        root: Workspace root to scan.
        index_dir: Directory where the index, chunks, and manifest are stored.
        embedder: Embedder instance (created if None).

    Returns:
        A VectorStore with the up-to-date index.
    """
    embedder = embedder or Embedder()
    loop = asyncio.get_running_loop()
    dim = embedder.model.get_embedding_dimension()

    root = root or Path.cwd()
    index_dir = Path(index_dir)
    index_dir.mkdir(parents=True, exist_ok=True)

    manifest = Manifest(index_dir / "manifest.json").load()
    current_hashes = scan_files_with_hashes(root)

    index_file = index_dir / "index.faiss"
    chunks_file = index_dir / "chunks.json"

    old_chunks: List[Dict] = []
    if index_file.exists() and chunks_file.exists():
        try:
            store = VectorStore(dim)
            store.load(index_dir)
            old_chunks = store.chunks
            # Old format without stored embeddings -> force full rebuild.
            if old_chunks and "embedding" not in old_chunks[0]:
                print("Old index format detected; rebuilding.")
                old_chunks = []
                manifest = Manifest(index_dir / "manifest.json")
        except Exception as e:
            print(f"Could not load existing index: {e}. Rebuilding.")
            old_chunks = []
            manifest = Manifest(index_dir / "manifest.json")

    added, changed, deleted = manifest.diff(current_hashes)

    # If no files were ever indexed, treat everything as added.
    if not manifest.hashes:
        added = set(current_hashes.keys())
        changed = set()
        deleted = set()

    if not added and not changed and not deleted:
        print("Index is up to date.")
        if index_file.exists() and chunks_file.exists():
            try:
                store = VectorStore(dim)
                store.load(index_dir)
                return store
            except Exception:
                pass
        return VectorStore(dim)

    print(
        f"Index sync: {len(added)} added, {len(changed)} changed, {len(deleted)} deleted"
    )

    # Remove chunks for deleted or changed files.
    to_remove = list(deleted | changed)
    old_chunks = [c for c in old_chunks if c["path"] not in to_remove]

    # Chunk and embed added or changed files.
    files_to_embed = list(added | changed)
    new_chunks: List[Dict] = []
    texts: List[str] = []
    for rel_path in files_to_embed:
        path = root / rel_path
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if not content.strip():
            continue
        chunks = chunk_file(path, content)
        for chunk in chunks:
            chunk["path"] = rel_path
            new_chunks.append(chunk)
            texts.append(f"{chunk['path']}\n{chunk['content']}")

    if texts:
        embeddings = await loop.run_in_executor(None, embedder.encode, texts)
        for chunk, embedding in zip(new_chunks, embeddings):
            chunk["embedding"] = embedding.tolist()

    all_chunks = old_chunks + new_chunks

    store = VectorStore(dim)
    store.build_from_chunks(all_chunks)

    manifest.update(current_hashes)
    manifest.save()
    store.save(index_dir)

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
