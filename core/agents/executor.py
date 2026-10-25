"""Phase 4 - Execution. Runs the generated pytest file and writes execution.json."""
from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from typing import Any, Dict, List


def run(project_dir: str, headed: bool = False, timeout_s: int = 300) -> Dict[str, Any]:
    outputs = os.path.join(project_dir, "outputs")
    os.makedirs(outputs, exist_ok=True)
    junit = os.path.join(outputs, "junit.xml")
    heals = os.path.join(outputs, "heals.jsonl")
    if os.path.exists(heals):
        os.remove(heals)
    cmd = [sys.executable, "-m", "pytest", os.path.join("tests", "test_main.py"), "-q", "-p", "no:cacheprovider", f"--junitxml={junit}", "--tb=short"]
    if headed:
        cmd.append("--headed")
    proc = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True, timeout=timeout_s)
    failures: List[Dict[str, str]] = []
    passed = total = 0
    duration = 0.0
    if os.path.exists(junit):
        root = ET.parse(junit).getroot()
        for case in root.iter("testcase"):
            total += 1
            duration += float(case.get("time", 0))
            bad = case.find("failure")
            if bad is None:
                bad = case.find("error")
            if bad is None:
                passed += 1
            else:
                failures.append({"test": case.get("name", ""), "message": (bad.get("message") or "")[:500], "detail": (bad.text or "")[-1500:]})
    return {
        "exit_code": proc.returncode,
        "total": total,
        "passed": passed,
        "failed": len(failures),
        "duration_s": round(duration, 2),
        "failures": failures,
        "stdout_tail": proc.stdout[-1500:],
        "stderr_tail": proc.stderr[-800:],
        "healed": _read_heals(heals),
    }


def _read_heals(path: str) -> List[str]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        return [ln.strip() for ln in fh if ln.strip()]
