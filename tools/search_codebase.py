from pathlib import Path
from typing import Any, Dict, List, Optional
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

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = (workspace or Path.cwd()).resolve()

    async def execute(self, query: str) -> Dict[str, Any]:
        matches: List[Dict[str, Any]] = []
        for path in self.workspace.rglob("*.py"):
            if "__pycache__" in path.parts or ".venv" in path.parts:
                continue
            try:
                text = path.read_text(encoding="utf-8")
                lines = text.splitlines()
                for i, line in enumerate(lines, start=1):
                    if query in line:
                        matches.append({
                            "file": str(path.relative_to(self.workspace)),
                            "line": i,
                            "content": line.strip(),
                        })
            except Exception:
                continue
        return {"matches": matches}
