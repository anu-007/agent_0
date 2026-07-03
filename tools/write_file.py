from pathlib import Path
from typing import Any, Dict
from tools.base import Tool


class WriteFileTool(Tool):
    name = "write_file"
    description = "Write content to a file in the workspace."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Relative path to the file."},
            "content": {"type": "string", "description": "Content to write."},
        },
        "required": ["path", "content"],
    }

    def _safe_path(self, path: str) -> Path:
        base = Path.cwd().resolve()
        target = (base / path).resolve()
        if not str(target).startswith(str(base)):
            raise ValueError("Path outside workspace")
        return target

    async def execute(self, path: str, content: str) -> Dict[str, Any]:
        try:
            target = self._safe_path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return {"success": True, "error": ""}
        except Exception as e:
            return {"success": False, "error": str(e)}
