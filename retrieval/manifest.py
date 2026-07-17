import json
from pathlib import Path
from typing import Dict, Set


class Manifest:
    """Tracks file hashes so the index can be updated incrementally."""

    def __init__(self, path: Path):
        self.path = path
        self.hashes: Dict[str, str] = {}

    def load(self) -> "Manifest":
        if self.path.exists():
            self.hashes = json.loads(self.path.read_text(encoding="utf-8"))
        return self

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.hashes, ensure_ascii=False), encoding="utf-8")

    def diff(self, current: Dict[str, str]) -> tuple[Set[str], Set[str], Set[str]]:
        """Return (added, changed, deleted) file paths."""
        old = set(self.hashes.keys())
        new = set(current.keys())

        added = new - old
        deleted = old - new
        changed = {p for p in old & new if self.hashes[p] != current[p]}

        return added, changed, deleted

    def update(self, current: Dict[str, str]):
        self.hashes = current
