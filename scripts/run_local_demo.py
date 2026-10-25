#!/usr/bin/env python3
"""Serve demo_app/ on localhost, run the whole pipeline against it, stop the server.

    python scripts/run_local_demo.py            # offline heuristics
    ANTHROPIC_API_KEY=... python scripts/run_local_demo.py
"""
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = "8765"


def main() -> int:
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", PORT, "--directory", os.path.join(ROOT, "demo_app")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1)
    try:
        cmd = [sys.executable, os.path.join(ROOT, "orchestrator.py"), "--project", os.path.join(ROOT, "projects", "local_demo"), "--security", "--force"]
        cmd += sys.argv[1:]
        return subprocess.call(cmd, cwd=ROOT)
    finally:
        server.terminate()


if __name__ == "__main__":
    sys.exit(main())
