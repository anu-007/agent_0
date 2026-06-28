import subprocess
import tempfile
from pathlib import Path
from typing import Tuple

def run_python_code(code: str, timeout_sec: int) -> Tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "submission.py"
        path.write_text(code, encoding="utf-8")
        try:
            completed = subprocess.run(
                ["python", str(path)],
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=False,
            )
            return completed.returncode, completed.stdout, completed.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "TimeoutExpired"