import json
import re
from typing import Any, Dict


def parse_tool_call(raw: str) -> Dict[str, Any]:
    """Parse a JSON tool call from an LLM response.

    Handles fenced JSON blocks, surrounding explanatory text, and missing args.
    """
    if raw is None:
        return {"error": "LLM returned empty response"}
    raw = raw.strip()

    # Try to extract JSON from markdown fences
    match = re.search(r"```(?:json)?(?:\s+.*?)?\n?(.*?)```", raw, re.DOTALL)
    if match:
        raw = match.group(1).strip()

    # If the raw text still contains other text, try to isolate the first JSON object
    if not raw.startswith("{"):
        match = re.search(r"(\{.*\})", raw, re.DOTALL)
        if match:
            raw = match.group(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}

    if not isinstance(data, dict):
        return {"error": "Tool call must be a JSON object"}

    if "tool" not in data:
        return {"error": "Tool call must contain a 'tool' field"}

    args = data.get("args", {})
    if args is None:
        args = {}
    if not isinstance(args, dict):
        return {"error": "'args' must be a JSON object"}

    return {
        "tool": data["tool"],
        "args": args,
        "thought": data.get("thought", ""),
    }
