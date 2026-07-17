from pathlib import Path
from typing import Any, Dict, Optional
from tools.base import Tool


class ReadFileTool(Tool):
    name = "read_file"
    description = "Read the contents of a file in the workspace."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path to the file."},
        },
        "required": ["path"],
    }

    def __init__(self, workspace: Optional[Path] = None):
        self.workspace = workspace or Path.cwd().resolve()

    def _safe_path(self, path: str) -> Path:
        target = (self.workspace / path).resolve()
        if not str(target).startswith(str(self.workspace)):
            raise ValueError("Path outside workspace")
        return target

    async def execute(self, path: str) -> Dict[str, Any]:
        try:
            target = self._safe_path(path)
            content = target.read_text(encoding="utf-8")
            return {"content": content, "error": ""}
        except Exception as e:
            return {"content": "", "error": str(e)}
