"""Phase 2 - Goal planning. Natural-language goal -> workflow.json.

Online the LLM writes the plan using the domain blueprint as context.
Offline a rule-based splitter produces the same schema, so later phases never care which ran.

Step schema
    n        int      1-based
    kind     str      login | action | verify
    intent   str      what the step is, in plain words
    expect   str      optional, what should be true afterwards
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

from core.llm import LLM

SYSTEM = (
    "You are a senior QA engineer. Turn the goal into an ordered list of browser test steps. "
    "Each step: {\"kind\": \"login|action|verify\", \"intent\": \"short imperative\", \"expect\": \"observable result\"}. "
    "Use 'verify' steps for assertions. Keep steps atomic. Respect the domain rules provided."
)

LOGIN_WORDS = re.compile(r"\b(log ?in|sign ?in|authenticate)\b", re.I)
VERIFY_WORDS = re.compile(r"^(verify|check|confirm|assert|ensure|validate|expect)\b", re.I)


def _split_goal(goal: str) -> List[str]:
    parts = re.split(r",|;|\bthen\b|\band then\b|\.\s", goal, flags=re.I)
    cleaned: List[str] = []
    for part in parts:
        part = part.strip(" .")
        part = re.sub(r"^and\s+", "", part, flags=re.I)
        if part:
            cleaned.append(part)
    return cleaned


def heuristic_plan(goal: str, domain: Dict[str, Any]) -> List[Dict[str, Any]]:
    steps: List[Dict[str, Any]] = []
    for part in _split_goal(goal):
        if LOGIN_WORDS.search(part):
            kind = "login"
        elif VERIFY_WORDS.match(part):
            kind = "verify"
        else:
            kind = "action"
        steps.append({"kind": kind, "intent": part[0].lower() + part[1:], "expect": ""})
    if not any(s["kind"] == "verify" for s in steps) and domain.get("default_assertions"):
        steps.append({"kind": "verify", "intent": f"verify {domain['default_assertions'][0]}", "expect": ""})
    for i, step in enumerate(steps, 1):
        step["n"] = i
    return steps


def plan(goal: str, base_url: str, domain_name: str, domain: Dict[str, Any], llm: LLM) -> Dict[str, Any]:
    rules = "\n".join(f"- {r}" for r in domain.get("rules", []))
    user = (
        f"Goal: {goal}\nApp URL: {base_url}\nDomain: {domain_name}\nDomain rules:\n{rules}\n"
        "Return {\"steps\": [...]}."
    )
    data = llm.json(SYSTEM, user, fallback=None)
    steps = None
    if isinstance(data, dict) and isinstance(data.get("steps"), list):
        steps = [s for s in data["steps"] if isinstance(s, dict) and s.get("intent")]
        for i, s in enumerate(steps, 1):
            s["n"] = i
            s.setdefault("kind", "action")
            s.setdefault("expect", "")
    mode = "llm" if steps else "heuristic"
    if not steps:
        steps = heuristic_plan(goal, domain)
    return {"goal": goal, "base_url": base_url, "domain": domain_name, "planner": mode, "steps": steps}


def save(workflow: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(workflow, fh, indent=2)
