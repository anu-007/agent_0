import json
from pathlib import Path
from typing import List, Dict
import numpy as np
import faiss


class VectorStore:
    """FAISS-backed vector store with chunk metadata and cached embeddings."""

    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.chunks: List[Dict] = []

    def add(self, chunks: List[Dict], embeddings: np.ndarray):
        """Add chunks and their normalized embeddings to the index."""
        embeddings = np.asarray(embeddings, dtype=np.float32)
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        for chunk, embedding in zip(chunks, embeddings):
            chunk_copy = chunk.copy()
            chunk_copy["embedding"] = embedding.tolist()
            self.chunks.append(chunk_copy)

    def build_from_chunks(self, chunks: List[Dict]):
        """Rebuild the FAISS index from existing chunks that already have embeddings."""
        self.chunks = [c.copy() for c in chunks]
        if not self.chunks:
            return
        embeddings = np.asarray(
            [c["embedding"] for c in self.chunks], dtype=np.float32
        )
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)

    def remove_by_path(self, paths: List[str]):
        """Remove all chunks belonging to the given file paths."""
        self.chunks = [c for c in self.chunks if c["path"] not in paths]
        self.index.reset()
        if self.chunks:
            embeddings = np.asarray(
                [c["embedding"] for c in self.chunks], dtype=np.float32
            )
            faiss.normalize_L2(embeddings)
            self.index.add(embeddings)

    def search(self, query_embedding: np.ndarray, k: int = 5) -> List[Dict]:
        """Return the top-k most similar chunks."""
        query_embedding = np.asarray(query_embedding, dtype=np.float32)
        faiss.normalize_L2(query_embedding)
        scores, indices = self.index.search(query_embedding, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx].copy()
            chunk["score"] = float(score)
            results.append(chunk)
        return results

    def save(self, path: Path):
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path / "index.faiss"))
        (path / "chunks.json").write_text(
            json.dumps(self.chunks, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self, path: Path):
        self.index = faiss.read_index(str(path / "index.faiss"))
        self.chunks = json.loads(
            (path / "chunks.json").read_text(encoding="utf-8")
        )
        self.dim = self.index.d