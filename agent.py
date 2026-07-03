import asyncio
from llm_client import LLMClient
from sandbox import run_python_code
from helpers.code_parser import extract_code

class CodingAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.history = []

    async def synthesize_and_run(self, instruction: str, max_retries: int = 3):
        self.history.append({"role": "user", "content": instruction})

        # Generate a single script that contains both the implementation
        # and a self-testing __main__ block.
        code = extract_code(await self.generate_code(instruction))

        last_stdout, last_stderr = "", ""
        for attempt in range(max_retries + 1):
            rc, last_stdout, last_stderr = await self._run_in_sandbox(code)
            if rc == 0 and "PASS" in last_stdout and "FAIL" not in last_stdout:
                return {
                    "code": code,
                    "success": True,
                    "attempts": attempt + 1,
                    "stdout": last_stdout,
                    "stderr": last_stderr,
                }

            if attempt < max_retries:
                code = extract_code(
                    await self.repair_code(code, last_stdout, last_stderr, instruction)
                )

        return {
            "code": code,
            "success": False,
            "attempts": max_retries + 1,
            "stdout": last_stdout,
            "stderr": last_stderr,
        }

    async def _run_in_sandbox(self, code: str, timeout: int = 1000):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, run_python_code, code, timeout)

    async def generate_code(self, instruction: str):
        prompt = (
            "You are a helpful Python coder. Implement the following task in a single "
            "self-contained Python script. Include a `if __name__ == '__main__':` block "
            "that runs assert-based tests and prints 'PASS' if all tests pass, otherwise "
            "prints 'FAIL'.\n\n"
            f"Task: {instruction}"
        )
        code = await self.llm.complete(prompt)
        return code

    async def repair_code(self, code: str, stdout: str, stderr: str, instruction: str):
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
        code_fix = await self.llm.complete(prompt)
        return code_fix