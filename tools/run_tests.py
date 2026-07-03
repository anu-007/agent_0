import asyncio
from typing import Any, Callable, Dict
from tools.base import Tool


class RunTestsTool(Tool):
    name = "run_tests"
    description = "Run a Python script in a sandbox and return the result."
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Python script to execute."},
        },
        "required": ["code"],
    }

    def __init__(self, runner: Callable[[str, int], Any]):
        self.runner = runner

    async def execute(self, code: str) -> Dict[str, Any]:
        loop = asyncio.get_running_loop()
        returncode, stdout, stderr = await loop.run_in_executor(
            None, self.runner, code, 5
        )
        return {
            "returncode": returncode,
            "stdout": stdout,
            "stderr": stderr,
        }
