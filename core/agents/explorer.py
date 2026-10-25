"""Phase 3 - AI-driven exploration.

Walks the workflow in a real browser. For each step it mines the live DOM, decides
which element to act on (LLM when online, scoring heuristic offline), performs the
action, and records a trace with ranked locator candidates and a screenshot.
trace.json is the only input the generator needs.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

from core.lib import knowledge
from core.lib.browser import launch, mine
from core.lib.smart_locator import build_candidates
from core.llm import LLM

STOPWORDS = {
    "the", "a", "an", "to", "of", "on", "in", "and", "with", "for", "click", "press", "tap", "select",
    "choose", "open", "go", "button", "link", "item", "cheapest", "first", "that", "it",
}
USER_FIELD = re.compile(r"user|email|login|account|phone", re.I)
SUBMIT_WORDS = re.compile(r"log ?in|sign ?in|submit|continue|enter", re.I)

ACT_SYSTEM = (
    "You drive a browser for a QA test. Given one step and the interactive elements on the page, "
    "choose the single best action. Reply {\"action\": \"click|fill|select|check\", \"idx\": <element idx>, "
    "\"value\": \"text for fill/select or empty\"}. If the step cannot be done on this page reply {\"action\": \"none\"}."
)


def _tokens(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS and len(t) > 1]


def score_element(intent: str, el: Dict[str, Any]) -> float:
    want = set(_tokens(intent))
    if not want:
        return 0.0
    have = set(_tokens(" ".join(str(el.get(k, "")) for k in ("name", "text", "label", "placeholder", "id", "html_name", "data-test"))))
    if not have:
        return 0.0
    overlap = len(want & have)
    if overlap == 0:
        return 0.0
    return overlap / len(want) + (0.1 if el.get("role") in ("button", "link") else 0)


def _quoted(intent: str) -> Optional[str]:
    m = re.search(r"[\"'“”‘’]([^\"'“”‘’]+)[\"'“”‘’]", intent)
    return m.group(1) if m else None


def heuristic_action(intent: str, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    ranked = sorted(elements, key=lambda e: score_element(intent, e), reverse=True)
    if not ranked or score_element(intent, ranked[0]) <= 0:
        return {"action": "none"}
    best = ranked[0]
    value = _quoted(intent) or ""
    if best["tag"] == "select":
        return {"action": "select", "idx": best["idx"], "value": value}
    if best["role"] == "textbox" and value:
        return {"action": "fill", "idx": best["idx"], "value": value}
    if best["role"] == "checkbox":
        return {"action": "check", "idx": best["idx"], "value": ""}
    return {"action": "click", "idx": best["idx"], "value": ""}


def _find(elements, pred):
    return next((e for e in elements if pred(e)), None)


def login_actions(elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    user = _find(elements, lambda e: e["role"] == "textbox" and e["type"] != "password" and USER_FIELD.search(f"{e['name']} {e['id']} {e['html_name']} {e['placeholder']}"))
    if not user:
        user = _find(elements, lambda e: e["role"] == "textbox" and e["type"] != "password")
    pwd = _find(elements, lambda e: e["type"] == "password")
    submit = _find(elements, lambda e: e["role"] == "button" and SUBMIT_WORDS.search(f"{e['name']} {e['text']} {e['id']}"))
    acts = []
    if user:
        acts.append({"action": "fill", "idx": user["idx"], "value": "{{credentials.username}}"})
    if pwd:
        acts.append({"action": "fill", "idx": pwd["idx"], "value": "{{credentials.password}}"})
    if submit:
        acts.append({"action": "click", "idx": submit["idx"], "value": ""})
    return acts


def _resolve_value(value: str, cfg: Dict[str, Any]) -> str:
    def sub(m):
        cur: Any = cfg
        for part in m.group(1).split("."):
            cur = cur.get(part, "") if isinstance(cur, dict) else ""
        return str(cur)

    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", sub, value)


def _drop_avoided(cands: List[Dict[str, str]], avoid: List[str]) -> List[Dict[str, str]]:
    kept = [c for c in cands if f"{c['kind']}={c['value']}" not in avoid]
    return kept or cands


def _perform(page, act: Dict[str, Any], cands: List[Dict[str, str]], cfg: Dict[str, Any]) -> None:
    from core.lib.smart_locator import resolve

    loc = resolve(page, cands)
    value = _resolve_value(act.get("value", ""), cfg)
    if act["action"] == "fill":
        loc.fill(value)
    elif act["action"] == "select":
        loc.select_option(label=value) if value else loc.select_option(index=1)
    elif act["action"] == "check":
        loc.check()
    else:
        loc.click()


def _verify(page, step: Dict[str, Any]) -> Dict[str, Any]:
    text = _quoted(step["intent"]) or _quoted(step.get("expect", ""))
    if text:
        ok = text.lower() in page.inner_text("body").lower()
        return {"action": "assert_text", "value": text, "ok": ok}
    url_hint = re.search(r"\burl\b.*?(\/[\w\-./]+|[\w\-]+\.html)", step["intent"], re.I)
    if url_hint:
        frag = url_hint.group(1).strip("/")
        return {"action": "assert_url", "value": frag, "ok": frag in page.url}
    words = [w for w in _tokens(step["intent"]) if w not in {"verify", "check", "confirm", "ensure", "validate", "displayed", "shown", "visible"}]
    if words:
        key = words[0]
        ok = key in page.inner_text("body").lower()
        return {"action": "assert_text", "value": key, "ok": ok}
    return {"action": "assert_text", "value": "", "ok": True}


def explore(project_dir: str, workflow: Dict[str, Any], cfg: Dict[str, Any], llm: LLM, headed: bool = False, timeout_ms: int = 60000) -> Dict[str, Any]:
    base_url = workflow["base_url"]
    avoid = knowledge.load_site(base_url).get("avoid", [])
    shots = os.path.join(project_dir, "screenshots")
    os.makedirs(shots, exist_ok=True)
    trace: List[Dict[str, Any]] = []
    storage: Dict[str, List[str]] = {"local": [], "session": []}
    with launch(headed, timeout_ms) as (page, _ctx):
        page.goto(base_url, wait_until="domcontentloaded")
        for step in workflow["steps"]:
            entry: Dict[str, Any] = {"n": step["n"], "intent": step["intent"], "kind": step["kind"], "url": page.url, "actions": [], "ok": True}
            try:
                page.wait_for_load_state("domcontentloaded")
                elements = mine(page)
                if step["kind"] == "verify":
                    result = _verify(page, step)
                    entry["actions"].append(result)
                    entry["ok"] = result["ok"]
                else:
                    acts = login_actions(elements) if step["kind"] == "login" else []
                    if not acts:
                        choice = llm.json(ACT_SYSTEM, json.dumps({"step": step["intent"], "elements": elements[:70]}), fallback=None)
                        acts = [choice] if isinstance(choice, dict) and choice.get("action") not in (None, "none") else []
                        if not acts:
                            h = heuristic_action(step["intent"], elements)
                            acts = [h] if h["action"] != "none" else []
                    if not acts:
                        raise RuntimeError(f"no element on the page matches: {step['intent']}")
                    for act in acts:
                        el = next((e for e in elements if e["idx"] == act["idx"]), None)
                        if el is None:
                            raise RuntimeError("model picked an element that is not on the page")
                        cands = _drop_avoided(build_candidates(el), avoid)
                        _perform(page, act, cands, cfg)
                        entry["actions"].append({"action": act["action"], "value": act.get("value", ""), "candidates": cands, "element": {k: el[k] for k in ("tag", "role", "name")}})
                        page.wait_for_timeout(300)
                    page.wait_for_load_state("domcontentloaded")
            except Exception as exc:  # noqa: BLE001
                entry["ok"] = False
                entry["error"] = f"{type(exc).__name__}: {str(exc).splitlines()[0][:300]}"
            shot = os.path.join(shots, f"step_{step['n']:02d}.png")
            try:
                page.screenshot(path=shot)
                entry["screenshot"] = os.path.relpath(shot, project_dir)
            except Exception:  # noqa: BLE001
                pass
            entry["url_after"] = page.url
            trace.append(entry)
            if not entry["ok"]:
                break
        try:
            storage["local"] = page.evaluate("Object.keys(localStorage)")
            storage["session"] = page.evaluate("Object.keys(sessionStorage)")
        except Exception:  # noqa: BLE001
            pass
    return {"base_url": base_url, "steps": trace, "storage_keys": storage, "complete": all(s["ok"] for s in trace) and len(trace) == len(workflow["steps"])}
