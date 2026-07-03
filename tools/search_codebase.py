from pathlib import Path
from typing import Any, Dict, List
from tools.base import Tool


class SearchCodebaseTool(Tool):
    name = "search_codebase"
    description = "Search for a query string in .py files under the workspace."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Text to search for."},
        },
        "required": ["query"],
    }

    async def execute(self, query: str) -> Dict[str, Any]:
        matches: List[Dict[str, Any]] = []
        base = Path.cwd()
        for path in base.rglob("*.py"):
            if "__pycache__" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
                lines = text.splitlines()
                for i, line in enumerate(lines, start=1):
                    if query in line:
                        matches.append({
                            "file": str(path.relative_to(base)),
                            "line": i,
                            "content": line.strip(),
                        })
            except Exception:
                continue
        return {"matches": matches}
