import json
import re
from typing import Any, Dict


def parse_tool_call(raw: str) -> Dict[str, Any]:
    raw = raw.strip()

    # Try to extract JSON from markdown fences
    match = re.search(r"```(?:json)?\n(.*?)```", raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}

    if not isinstance(data, dict):
        return {"error": "Tool call must be a JSON object"}

    if "tool" not in data or "args" not in data:
        return {"error": "Tool call must contain 'tool' and 'args' fields"}

    return {
        "tool": data["tool"],
        "args": data["args"],
        "thought": data.get("thought", ""),
    }
