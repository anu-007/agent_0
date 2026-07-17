import json
from typing import Any, Dict, List, Optional
from llm_client import LLMClient
from retrieval import Retriever
from tools import create_default_registry
from tools.registry import ToolRegistry
from helpers.tool_parser import parse_tool_call


class CodingAgent:
    def __init__(
        self,
        llm: LLMClient,
        registry: Optional[ToolRegistry] = None,
        retriever: Optional[Retriever] = None,
    ):
        self.llm = llm
        self.registry = registry or create_default_registry(llm)
        self.retriever = retriever
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return (
            "You are a helpful coding assistant. You have access to the following tools. "
            "For each step, respond with a single JSON object in this exact format:\n"
            '{"thought": "your reasoning", "tool": "tool_name", "args": {"arg_name": "value"}}\n\n'
            "Available tools:\n"
            f"{self.registry.describe()}\n\n"
            "When the task is complete, call the `final_answer` tool with the final code, "
            "success status, stdout, stderr, and the number of attempts. "
            "If a test run fails, use the `repair_code` tool to fix it."
        )

    async def _retrieve_context(self, instruction: str) -> str:
        if not self.retriever:
            return ""
        try:
            results = await self.retriever.retrieve(instruction, k=5)
        except Exception as e:
            return f"[Could not retrieve context: {e}]"
        if not results:
            return ""
        parts = ["Relevant codebase context:"]
        for r in results:
            content = r.get("content", "")[:3000]
            parts.append(f"\nFile: {r['path']}\n```python\n{content}\n```")
        return "\n".join(parts)

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
                messages.append({"role": "assistant", "content": response})
                messages.append({
                    "role": "user",
                    "content": (
                        f"Invalid tool call: {tool_call['error']}. "
                        "Please respond with valid JSON using the required format."
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
        return await self.run(instruction, max_iterations=max_iterations)