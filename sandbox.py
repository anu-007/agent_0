import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import List, Tuple

IMAGE = "agent0-sandbox"
TAG = "latest"
MEMORY_LIMIT = "512m"
CPU_LIMIT = "1.0"


def _ensure_docker():
    if not shutil.which("docker"):
        raise RuntimeError(
            "docker CLI not found. Install Docker and start the daemon to use the sandbox."
        )


def _ensure_image():
    _ensure_docker()
    image_ref = f"{IMAGE}:{TAG}"
    result = subprocess.run(
        ["docker", "image", "inspect", image_ref],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Docker image {image_ref} not found. "
            f"Build it with: docker build -f Dockerfile.sandbox -t {image_ref} ."
        )


def run_in_container(
    cmd: List[str],
    timeout_sec: int = 30,
    network: bool = False,
    volumes: List[str] = None,
    workdir: str = None,
) -> Tuple[int, str, str]:
    """Run a command inside the Docker sandbox container.

    Args:
        cmd: Command and arguments to run inside the container.
        timeout_sec: Maximum time to allow the command to run.
        network: Whether to allow network access (default: False).
        volumes: Optional list of Docker -v mount strings (e.g. "/host:/container:ro").
        workdir: Optional working directory inside the container.

    Returns:
        Tuple of (returncode, stdout, stderr).
    """
    _ensure_image()

    docker_cmd = [
        "docker", "run", "--rm",
        "--network", "bridge" if network else "none",
        "--memory", MEMORY_LIMIT,
        "--cpus", CPU_LIMIT,
        "--pids-limit", "64",
        "--security-opt", "no-new-privileges",
    ]
    if volumes:
        for vol in volumes:
            docker_cmd.extend(["-v", vol])
    if workdir:
        docker_cmd.extend(["-w", workdir])
    docker_cmd.append(f"{IMAGE}:{TAG}")
    docker_cmd.extend(cmd)

    try:
        completed = subprocess.run(
            docker_cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            check=False,
        )
        return completed.returncode, completed.stdout, completed.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TimeoutExpired"


def run_python_code(code: str, timeout_sec: int) -> Tuple[int, str, str]:
    """Write code to a temp file and execute it inside the Docker sandbox.

    Returns:
        Tuple of (returncode, stdout, stderr).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "submission.py"
        path.write_text(code, encoding="utf-8")
        return run_in_container(
            ["python", "/sandbox/submission.py"],
            timeout_sec=timeout_sec,
            volumes=[f"{tmpdir}:/sandbox:ro"],
        )