"""Closed-loop learning. Reads a failed run, classifies why, stores lessons in knowledge/sites/.

The orchestrator calls this between retries. Lessons change what the explorer does next
(for example, locators that failed are added to the site's `avoid` list).
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict

from core.lib import knowledge

CLASSES = [
    ("locator", re.compile(r"No locator matched|strict mode violation|resolved to \d+ elements", re.I)),
    ("timeout", re.compile(r"Timeout|TimeoutError", re.I)),
    ("assertion", re.compile(r"AssertionError|expected text not on page|unexpected url", re.I)),
    ("network", re.compile(r"net::ERR|ECONNREFUSED|ERR_NAME_NOT_RESOLVED", re.I)),
]


def classify(text: str) -> str:
    for name, pattern in CLASSES:
        if pattern.search(text):
            return name
    return "unknown"


def analyze(project_dir: str, base_url: str, execution: Dict[str, Any], attempt: int) -> Dict[str, Any]:
    advice: Dict[str, Any] = {"attempt": attempt, "classes": [], "timeout_ms": 60000, "reexplore": True}
    for failure in execution.get("failures", []):
        blob = f"{failure['message']}\n{failure['detail']}"
        cls = classify(blob)
        advice["classes"].append(cls)
        if cls == "locator":
            tried = re.findall(r"(\w+)='?([^'|]+?)'?[:\s]+(?:matched \d+ elements|\w+Error)", blob)
            avoid = [f"{kind}={value.strip()}" for kind, value in tried if kind in ("css", "text", "id", "name")]
            knowledge.add_lesson(base_url, "A locator failed at run time; prefer role/label/test-id candidates for that element.", avoid)
        elif cls == "timeout":
            advice["timeout_ms"] = 90000
            knowledge.add_lesson(base_url, "Page or element was slow; use a 90s timeout.")
        elif cls == "assertion":
            knowledge.add_lesson(base_url, "An assertion failed. Check the expected text against the live page before retrying.")
            advice["reexplore"] = False  # a real product failure, not a test problem
        elif cls == "network":
            knowledge.add_lesson(base_url, "Network error reaching the site; check connectivity before blaming the test.")
            advice["reexplore"] = False
    for heal in execution.get("healed", []):
        knowledge.add_lesson(base_url, f"Self-heal used: {heal[:200]}")
    log_path = os.path.join(project_dir, "qa_session_logs.json")
    history = []
    if os.path.exists(log_path):
        with open(log_path, encoding="utf-8") as fh:
            history = json.load(fh)
    history.append({"attempt": attempt, "failures": execution.get("failures", []), "advice": advice})
    with open(log_path, "w", encoding="utf-8") as fh:
        json.dump(history, fh, indent=2)
    return advice
