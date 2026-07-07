import asyncio
import shlex
from functools import partial
from pathlib import Path
from typing import Any, Dict, Set
from tools.base import Tool
from sandbox import run_in_container


class RunShellTool(Tool):
    name = "run_shell"
    description = "Run a restricted shell command inside the Docker sandbox."
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
            loop = asyncio.get_running_loop()
            runner = partial(
                run_in_container,
                parts,
                timeout_sec=30,
                volumes=[f"{Path.cwd()}:/workspace:ro"],
                workdir="/workspace",
            )
            returncode, stdout, stderr = await loop.run_in_executor(None, runner)
            return {
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
            }
        except Exception as e:
            return {"returncode": -1, "stdout": "", "stderr": str(e)}
