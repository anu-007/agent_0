import re

# Matches python, python3, py (case-insensitive). Allows optional extra text
# (e.g. filename) on the same line as the language tag, then a newline before
# the code body.
PYTHON_FENCE_RE = re.compile(
    r"```(?:python3?|py)(?:[ \t]+[^\n]*)?\n(.*?)\n?```",
    re.IGNORECASE | re.DOTALL,
)

# Matches any fenced code block.
ANY_FENCE_RE = re.compile(
    r"```(?:\w+)?(?:[ \t]+[^\n]*)?\n(.*?)\n?```",
    re.DOTALL,
)


def extract_code(raw: str) -> str:
    """Extract code from markdown fences, or return the raw text if no fences."""
    raw = raw.strip()

    # Prefer all fenced Python blocks, joined together
    python_blocks = PYTHON_FENCE_RE.findall(raw)
    if python_blocks:
        return "\n\n".join(block.strip() for block in python_blocks)

    # Fall back to any fenced code blocks
    code_blocks = ANY_FENCE_RE.findall(raw)
    if code_blocks:
        return "\n\n".join(block.strip() for block in code_blocks)

    # If no fences, assume entire response is code
    return raw