from llm_client import LLMClient
from sandbox import run_python_code

class CodingAgent:
    def __init__(self, llm: LLMClient):
        self.llm = llm

    def synthesize_and_run(self, instruction: str):
        prompt = f"You are a helpful Python coder. Implement the following task in a script. Include tests in a __main__ block that prints 'PASS' or 'FAIL'. Task: {instruction}"
        code = self.llm.complete(prompt)
        rc, out, err = run_python_code(code)
        return {"returncode": rc, "stdout": out, "stderr": err, "code": code}