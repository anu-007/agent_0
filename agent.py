import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from llm_client import LLMClient
from retrieval import Retriever
from retrieval.retriever import format_context
from tools import create_default_registry
from tools.registry import ToolRegistry
from helpers.code_parser import extract_code
from helpers.tool_parser import parse_tool_call


class CodingAgent:
    def __init__(
        self,
        llm: LLMClient,
        registry: Optional[ToolRegistry] = None,
        retriever: Optional[Retriever] = None,
        workspace: Optional[Path] = None,
        simple_mode: bool = False,
    ):
        self.llm = llm
        self.workspace = workspace or Path.cwd().resolve()
        self.registry = registry or create_default_registry(llm, workspace=self.workspace)
        self.retriever = retriever
        self.simple_mode = simple_mode
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        workspace = str(self.workspace)
        example = (
            "\nExample workflow for writing a new file:\n"
            '{"thought": "I will write the sum program to sum.py", "tool": "write_file", "args": {"path": "sum.py", "content": "def add(a, b):\\n    return a + b\\n\\nif __name__ == \\"__main__\\":\\n    assert add(2, 3) == 5\\n    print(\\"PASS\\")\\n"}}\n'
            '{"thought": "Now run the tests", "tool": "run_tests", "args": {"code": "def add(a, b):\\n    return a + b\\n\\nif __name__ == \\"__main__\\":\\n    assert add(2, 3) == 5\\n    print(\\"PASS\\")\\n"}}\n'
            '{"thought": "Tests passed, I am done", "tool": "final_answer", "args": {"code": "def add(a, b):\\n    return a + b\\n", "success": true, "stdout": "PASS\\n", "stderr": "", "attempts": 1}}\n'
        )
        return (
            "You are a helpful coding assistant working in a workspace. "
            f"Workspace: {workspace}\n\n"
            "You have access to the following tools. "
            "For each step, respond with a single JSON object in this exact format:\n"
            '{"thought": "your reasoning", "tool": "tool_name", "args": {"arg_name": "value"}}\n\n'
            "Available tools:\n"
            f"{self.registry.describe()}"
            f"{example}\n\n"
            "Important: when you generate or edit code, use `write_file` to save the result "
            f"under the workspace ({workspace}) so it is persisted. "
            "When the task is complete, call the `final_answer` tool with the final code, "
            "success status, stdout, stderr, and the number of attempts. "
            "If a test run fails, use the `repair_code` tool to fix it."
        )

    async def _retrieve_context(self, instruction: str) -> str:
        if not self.retriever:
            return ""
        try:
            results = await self.retriever.retrieve(instruction, k=8)
        except Exception as e:
            return f"[Could not retrieve context: {e}]"
        if not results:
            return ""
        return format_context(results, max_chars=8000, max_chunks=15)

    def _infer_path(self, instruction: str) -> str:
        match = re.search(r"workspace/([a-zA-Z0-9_]+\.py)", instruction)
        return match.group(1) if match else "solution.py"

    async def _try_direct_code(self, response: str, instruction: str) -> Optional[Dict[str, Any]]:
        """Fallback: if the LLM returned a code block instead of a JSON tool call,
        write it to the workspace and run it.
        """
        code = extract_code(response)
        if not code:
            return None

        path = self._infer_path(instruction)
        write_result = await self.registry.call(
            "write_file", {"path": path, "content": code}
        )
        if not write_result.get("success"):
            return {
                "code": code,
                "success": False,
                "stdout": "",
                "stderr": write_result.get("error", "write_file failed"),
                "attempts": 1,
            }

        run_result = await self.registry.call("run_tests", {"code": code})
        success = (
            run_result.get("returncode") == 0
            and "PASS" in run_result.get("stdout", "")
            and "FAIL" not in run_result.get("stdout", "")
        )
        return {
            "code": code,
            "success": success,
            "stdout": run_result.get("stdout", ""),
            "stderr": run_result.get("stderr", ""),
            "attempts": 1,
        }

    def _build_simple_prompt(self, instruction: str, context: str) -> str:
        parts = []
        if context:
            parts.append(context)
        parts.append(f"Task: {instruction}")
        parts.append(
            "Write or edit Python code to satisfy the task. "
            "Put the complete code in a markdown Python code block (```python ... ```)."
        )
        return "\n\n".join(parts)

    async def _run_simple(self, instruction: str, max_iterations: int = 10) -> Dict[str, Any]:
        """Simple loop for weak/local models that don't follow tool-calling format."""
        context = await self._retrieve_context(instruction)
        prompt = self._build_simple_prompt(instruction, context)

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": prompt},
        ]

        code = ""
        for iteration in range(max_iterations):
            response = await self.llm.chat(messages)
            code = extract_code(response)
            if not code:
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": "Please provide the Python code in a fenced code block.",
                })
                continue

            path = self._infer_path(instruction)
            write_result = await self.registry.call(
                "write_file", {"path": path, "content": code}
            )
            if not write_result.get("success"):
                return {
                    "code": code,
                    "success": False,
                    "stdout": "",
                    "stderr": write_result.get("error", "write_file failed"),
                    "attempts": iteration + 1,
                }

            run_result = await self.registry.call("run_tests", {"code": code})
            success = (
                run_result.get("returncode") == 0
                and "PASS" in run_result.get("stdout", "")
                and "FAIL" not in run_result.get("stdout", "")
            )
            if success:
                return {
                    "code": code,
                    "success": True,
                    "stdout": run_result.get("stdout", ""),
                    "stderr": run_result.get("stderr", ""),
                    "attempts": iteration + 1,
                }

            messages.append({"role": "assistant", "content": f"```python\n{code}\n```"})
            messages.append({
                "role": "user",
                "content": (
                    f"The code failed when run:\n"
                    f"stdout: {run_result.get('stdout', '')}\n"
                    f"stderr: {run_result.get('stderr', '')}\n"
                    "Please fix it and provide the corrected code in a fenced code block."
                ),
            })

        return {
            "code": code,
            "success": False,
            "stdout": "",
            "stderr": "Max iterations reached in simple mode",
            "attempts": max_iterations,
        }

    async def run(self, instruction: str, max_iterations: int = 10) -> Dict[str, Any]:
        context = await self._retrieve_context(instruction)
        user_message = instruction
        if context:
            user_message = f"{context}\n\nTask: {instruction}"

        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]

        for iteration in range(max_iterations):
            response = await self.llm.chat(messages)
            tool_call = parse_tool_call(response)

            if "error" in tool_call:
                direct = await self._try_direct_code(response, instruction)
                if direct:
                    if direct["success"]:
                        return direct
                    # Direct code failed; include the error and continue.
                    messages.append({"role": "assistant", "content": response})
                    messages.append({
                        "role": "user",
                        "content": (
                            f"The code you provided failed when run:\n"
                            f"stdout: {direct['stdout']}\n"
                            f"stderr: {direct['stderr']}\n"
                            "Please fix it. Respond with either a valid JSON tool call or a corrected Python code block."
                        ),
                    })
                    continue

                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": (
                        f"Invalid tool call: {tool_call['error']}. "
                        "Please respond with valid JSON using the required format or a Python code block."
                    ),
                })
                continue

            if tool_call["tool"] == "final_answer":
                return await self.registry.call(tool_call["tool"], tool_call["args"])

            observation = await self.registry.call(tool_call["tool"], tool_call["args"])

            messages.append({"role": "assistant", "content": json.dumps(tool_call)})
            observation_msg = f"Observation: {json.dumps(observation)}"
            if (
                tool_call["tool"] == "run_tests"
                and observation.get("returncode") == 0
                and "PASS" in observation.get("stdout", "")
            ):
                observation_msg += "\nHint: tests passed. Call final_answer when ready."
            messages.append({"role": "user", "content": observation_msg})

        return {
            "error": "Max iterations reached",
            "code": "",
            "success": False,
            "stdout": "",
            "stderr": "",
            "attempts": max_iterations,
        }

    async def synthesize_and_run(self, instruction: str, max_iterations: int = 10) -> Dict[str, Any]:
        if self.simple_mode:
            return await self._run_simple(instruction, max_iterations=max_iterations)
        return await self.run(instruction, max_iterations=max_iterations)