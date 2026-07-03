import re

def extract_code(raw: str) -> str:
    raw = raw.strip()

    # Prefer all fenced Python blocks, joined together
    python_blocks = re.findall(r"```python\n(.*?)```", raw, re.DOTALL)
    if python_blocks:
        return "\n\n".join(block.strip() for block in python_blocks)

    # Fall back to any fenced code blocks
    code_blocks = re.findall(r"```(?:\w+)?\n(.*?)```", raw, re.DOTALL)
    if code_blocks:
        return "\n\n".join(block.strip() for block in code_blocks)

    # If no fences, assume entire response is code
    return raw