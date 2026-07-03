from typing import Any, Dict
from llm_client import LLMClient
from helpers.code_parser import extract_code
from tools.base import Tool


class RepairCodeTool(Tool):
    name = "repair_code"
    description = "Fix a Python script that failed when run."
    parameters = {
        "type": "object",
        "properties": {
            "instruction": {"type": "string", "description": "Original task description."},
            "code": {"type": "string", "description": "The failing Python script."},
            "stdout": {"type": "string", "description": "Stdout from the failing run."},
            "stderr": {"type": "string", "description": "Stderr from the failing run."},
        },
        "required": ["instruction", "code", "stdout", "stderr"],
    }

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def execute(self, instruction: str, code: str, stdout: str, stderr: str) -> Dict[str, Any]:
        prompt = (
            "You are a helpful Python coder. The following script was written for a task "
            "but failed when run. Fix the script so it satisfies the task and its tests pass. "
            "Return the complete corrected Python script, including the tests in __main__.\n\n"
            f"Task: {instruction}\n\n"
            f"Script:\n```python\n{code}\n```\n\n"
            f"Stdout:\n{stdout}\n\n"
            f"Stderr:\n{stderr}\n\n"
            "Return the complete corrected Python script."
        )
        raw = await self.llm.complete(prompt)
        fixed_code = extract_code(raw)
        return {
            "code": fixed_code,
            "stdout": "",
            "stderr": "",
            "returncode": 0,
        }
