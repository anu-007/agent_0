from llm_client import LLMClient
from sandbox import run_python_code

class CodingAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm
        self.history = []

    async def synthesize_and_run(self, instruction: str):
        self.history.append({"role": "user", "content": instruction})
        response = f"got prompt {instruction}"
        self.history.append({"role": "agent", "content": response})

        prompt = f"You are a helpful Python coder. Implement the following task in a script. Include tests in a __main__ block that prints 'PASS' or 'FAIL'. Task: {instruction}"
        code = await self.llm.complete(prompt)
        rc, out, err = run_python_code(code, 1000)
        return {"returncode": rc, "stdout": out, "stderr": err, "code": code}