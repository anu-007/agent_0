import hashlib
from pathlib import Path
from typing import List, Dict
from retrieval.chunker import chunk_file


DEFAULT_SKIP_DIRS = {
    "__pycache__",
    ".venv",
    "venv",
    ".git",
    "node_modules",
    ".pytest_cache",
    "dist",
    "build",
    "*.egg-info",
}


def should_skip(path: Path) -> bool:
    return any(part in DEFAULT_SKIP_DIRS for part in path.parts)


def file_hash(path: Path) -> str:
    """Return a SHA-256 hash of the file content."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scan_files_with_hashes(root: Path = None, glob: str = "**/*.py") -> Dict[str, str]:
    """Scan Python files and return a map of relative path -> content hash."""
    root = root or Path.cwd()
    manifest: Dict[str, str] = {}
    for path in root.rglob(glob):
        if should_skip(path):
            continue
        rel = str(path.relative_to(root))
        manifest[rel] = file_hash(path)
    return manifest


def scan_codebase(root: Path = None, glob: str = "**/*.py") -> List[Dict]:
    """Scan Python files under root and return logical AST chunks."""
    root = root or Path.cwd()
    chunks = []

    for path in root.rglob(glob):
        if should_skip(path):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if not content.strip():
            continue

        rel_path = str(path.relative_to(root))
        for chunk in chunk_file(path, content):
            chunk["path"] = rel_path
            chunks.append(chunk)
    return chunks
