import py_compile
import tempfile
from pathlib import Path
from typing import Any, Dict
from tools.base import Tool


class RunLinterTool(Tool):
    name = "run_linter"
    description = "Check Python code for syntax errors using py_compile."
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python code to check."},
        },
        "required": ["code"],
    }

    async def execute(self, code: str) -> Dict[str, Any]:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "lint.py"
            path.write_text(code, encoding="utf-8")
            try:
                py_compile.compile(str(path), doraise=True)
                return {"valid": True, "errors": ""}
            except py_compile.PyCompileError as e:
                return {"valid": False, "errors": str(e)}
