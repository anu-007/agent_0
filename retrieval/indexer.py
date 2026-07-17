from pathlib import Path
from typing import List, Dict


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


def scan_codebase(root: Path = None, glob: str = "**/*.py") -> List[Dict]:
    """Scan Python files under root and return one chunk per file."""
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

        chunks.append({
            "path": str(path.relative_to(root)),
            "content": content,
        })
    return chunks
