from typing import Dict, Any
from llm_client import LLMClient
from helpers.code_parser import extract_code
from tools.base import Tool


class GenerateCodeTool(Tool):
    name = "generate_code"
    description = "Generate a self-contained Python script for a given task, including tests in __main__."
    parameters = {
        "type": "object",
        "properties": {
            "instruction": {
                "type": "string",
                "description": "The programming task to implement.",
            }
        },
        "required": ["instruction"],
    }

    def __init__(self, llm: LLMClient):
        self.llm = llm

    async def execute(self, instruction: str) -> Dict[str, Any]:
        prompt = (
            "You are a helpful Python coder. Implement the following task in a single "
            "self-contained Python script. Include a `if __name__ == '__main__':` block "
            "that runs assert-based tests and prints 'PASS' if all tests pass, otherwise "
            "prints 'FAIL'.\n\n"
            f"Task: {instruction}"
        )
        raw = await self.llm.complete(prompt)
        code = extract_code(raw)
        return {
            "code": code,
            "stdout": "",
            "stderr": "",
            "returncode": 0,
        }