import shlex
import subprocess
from typing import Any, Dict, Set
from tools.base import Tool


class RunShellTool(Tool):
    name = "run_shell"
    description = "Run a restricted shell command."
    parameters = {
        "type": "object",
        "properties": {
            "cmd": {"type": "string", "description": "Shell command to run."},
        },
        "required": ["cmd"],
    }

    allowed_commands: Set[str] = {
        "ls", "cat", "grep", "find", "python", "python3", "pytest", "ruff", "git"
    }

    async def execute(self, cmd: str) -> Dict[str, Any]:
        parts = shlex.split(cmd)
        if not parts or parts[0] not in self.allowed_commands:
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": f"Command not allowed: {parts[0] if parts else ''}",
            }
        try:
            completed = subprocess.run(
                parts,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            return {
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        except Exception as e:
            return {"returncode": -1, "stdout": "", "stderr": str(e)}
