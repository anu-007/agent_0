import re
from typing import List, Optional

from llm_client import LLMClient


class Planner:
    """Decompose a high-level task into a concrete list of subtasks."""

    def __init__(self, llm: LLMClient, max_steps: int = 5):
        self.llm = llm
        self.max_steps = max_steps

    def _prompt(self, task: str, context: str) -> str:
        parts = [
            "You are a planning assistant. Break the following task into a short, "
            "ordered list of concrete subtasks. Each subtask should be simple enough "
            "for a coding agent to implement in one go.",
            "",
            f"Task: {task}",
        ]
        if context:
            parts.extend(["", f"Relevant context:\n{context}"])
        parts.extend([
            "",
            f"Return at most {self.max_steps} numbered steps. If the task is simple, "
            "return a single step. Do not include explanations, only the numbered list.",
        ])
        return "\n".join(parts)

    def _parse_steps(self, raw: str) -> List[str]:
        steps = []
        for line in raw.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            # Remove leading numbering like "1." or "1)" or "-"
            line = re.sub(r"^(\d+[\.\)\-]\s*|-\s*)", "", line)
            if line:
                steps.append(line)
        return steps

    async def plan(self, task: str, context: str = "") -> List[str]:
        prompt = self._prompt(task, context)
        response = await self.llm.complete(prompt, max_tokens=1024)
        steps = self._parse_steps(response)
        if not steps:
            # Fallback: treat the whole task as one step.
            return [task]
        return steps[: self.max_steps]
