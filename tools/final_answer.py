from typing import Any, Dict
from tools.base import Tool


class FinalAnswerTool(Tool):
    name = "final_answer"
    description = "End the task and return the final result."
    parameters = {
        "type": "object",
        "properties": {
            "code": {"type": "string", "description": "Final code produced by the agent."},
            "success": {"type": "boolean", "description": "Whether the task succeeded."},
            "stdout": {"type": "string", "description": "Final stdout."},
            "stderr": {"type": "string", "description": "Final stderr."},
            "attempts": {"type": "integer", "description": "Number of attempts made."},
        },
        "required": ["code", "success", "stdout", "stderr", "attempts"],
    }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        return {"done": True, **kwargs}
