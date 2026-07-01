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

        code = extract_code(await self.generate_code(instruction))

        rc, out, err = await self._run_in_sandbox(code)
        if rc != 0:
            for _ in range(max_retries):
                code = extract_code(await self.repair_code(code, err, instruction))
                rc, out, err = await self._run_in_sandbox(code)
                if rc == 0:
                    break

        success = False
        for _ in range(max_retries):
            tests = extract_code(await self.generate_tests(instruction, code))
            rc, out, err = await self._run_in_sandbox(tests)

            if rc == 0 and "PASS" in out and "FAIL" not in out:
                success = True
                break
            else:
                code = extract_code(await self.repair_code(code, err, instruction))
                rc, out, err = await self._run_in_sandbox(code)
                if rc != 0:
                    continue

        return {
            "code": code,
            "initial_success": rc == 0,
            "tests_passed": success,
            "stdout": out,
            "stderr": err,
        }

    async def _run_in_sandbox(self, code: str, timeout: int = 1000):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, run_python_code, code, timeout)
    
    async def generate_code(self, instruction: str):
        prompt = f"You are a helpful Python coder. Implement the following task in a script. Task: {instruction}"
        code = await self.llm.complete(prompt)
        return code

    async def generate_tests(self, instruction: str, code: str):
        prompt = f"You are a helpful Python tester. Implement the tests for following task in a script. Include tests in a __main__ block that prints 'PASS' or 'FAIL'. Task: {instruction} code: {code}"
        tests = await self.llm.complete(prompt)
        return tests
    
    async def repair_code(self, code: str, err: str, instruction: str):
        prompt = f"You are a helpful Python tester. given a task, error and the code generated for task fix the error and give the fixed code. Task: {instruction} code: {code} Error: {err}"
        code_fix = await self.llm.complete(prompt)
        return code_fix