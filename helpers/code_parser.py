import re

def extract_code(raw: str) -> str:
    raw = raw.strip()
    
    # Try to find fenced code
    match = re.search(r"```(?:\w+)?\n(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # If no fences, assume entire response is code
    return raw