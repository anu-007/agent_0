#!/usr/bin/env python3
"""Start script: rebuild the Docker sandbox image and run the agent."""

import shutil
import subprocess
import sys
from pathlib import Path

IMAGE = "agent0-sandbox"
TAG = "latest"
DOCKERFILE = Path(__file__).with_name("Dockerfile.sandbox")
MAIN = Path(__file__).with_name("main.py")


def run(cmd: list[str]) -> None:
    print("$ " + " ".join(cmd))
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)


def main() -> None:
    if not shutil.which("docker"):
        print("Error: docker CLI not found. Install Docker and start the daemon.", file=sys.stderr)
        sys.exit(1)

    # Rebuild the sandbox image every time so code changes are picked up.
    run([
        "docker", "build",
        "-f", str(DOCKERFILE),
        "-t", f"{IMAGE}:{TAG}",
        str(Path(__file__).parent),
    ])

    # Forward all arguments to main.py.
    run([sys.executable, str(MAIN)] + sys.argv[1:])


if __name__ == "__main__":
    main()
