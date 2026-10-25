"""Self-healing locators.

Every element mined from the page gets an ordered list of locator candidates,
most stable first. Generated tests call `resolve()`, which walks the list and
returns the first candidate that matches exactly one visible element. If the
primary locator breaks after a UI change, a fallback takes over and the heal
is logged so the feedback agent can learn from it.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

# Stability order. Test ids and roles survive redesigns; text and CSS do not.
STRATEGY_ORDER = ["test_id", "role", "label", "placeholder", "id", "name", "text", "css"]

HEAL_LOG = os.getenv("QA_HEAL_LOG", "outputs/heals.jsonl")


def build_candidates(el: Dict[str, Any]) -> List[Dict[str, str]]:
    """Turn a mined element dict into an ordered candidate list."""
    cands: List[Dict[str, str]] = []
    for attr in ("data-test", "data-testid", "data-qa", "data-cy"):
        if el.get(attr):
            cands.append({"kind": "test_id", "attr": attr, "value": el[attr]})
            break
    if el.get("role") and el.get("name"):
        cands.append({"kind": "role", "role": el["role"], "value": el["name"]})
    if el.get("label"):
        cands.append({"kind": "label", "value": el["label"]})
    if el.get("placeholder"):
        cands.append({"kind": "placeholder", "value": el["placeholder"]})
    if el.get("id"):
        cands.append({"kind": "id", "value": el["id"]})
    if el.get("html_name"):
        cands.append({"kind": "name", "tag": el.get("tag", "*"), "value": el["html_name"]})
    if el.get("text") and el.get("tag") in ("a", "button", "span", "div", "h1", "h2", "h3", "p"):
        cands.append({"kind": "text", "value": el["text"][:60]})
    if el.get("css"):
        cands.append({"kind": "css", "value": el["css"]})
    return cands


def _locator_for(page, cand: Dict[str, str]):
    kind = cand["kind"]
    if kind == "test_id":
        return page.locator(f'[{cand["attr"]}="{cand["value"]}"]')
    if kind == "role":
        return page.get_by_role(cand["role"], name=cand["value"], exact=True)
    if kind == "label":
        return page.get_by_label(cand["value"], exact=True)
    if kind == "placeholder":
        return page.get_by_placeholder(cand["value"], exact=True)
    if kind == "id":
        return page.locator(f'[id="{cand["value"]}"]')
    if kind == "name":
        return page.locator(f'{cand.get("tag", "*")}[name="{cand["value"]}"]')
    if kind == "text":
        return page.get_by_text(cand["value"], exact=True)
    return page.locator(cand["value"])


def resolve(page, candidates: List[Dict[str, str]], timeout_ms: int = 8000):
    """Return the first candidate resolving to exactly one visible element."""
    errors = []
    for index, cand in enumerate(candidates):
        try:
            loc = _locator_for(page, cand)
            loc.first.wait_for(state="visible", timeout=timeout_ms if index == 0 else 2500)
            if loc.count() == 1:
                if index > 0:
                    _log_heal(page.url, candidates[0], cand)
                return loc
            errors.append(f"{cand['kind']}={cand['value']!r} matched {loc.count()} elements")
        except Exception as exc:  # noqa: BLE001 - any failure means try the next strategy
            errors.append(f"{cand['kind']}={cand['value']!r}: {type(exc).__name__}")
    raise LookupError("No locator matched. Tried: " + " | ".join(errors))


def _log_heal(url: str, broken: Dict[str, str], used: Dict[str, str]) -> None:
    os.makedirs(os.path.dirname(HEAL_LOG) or ".", exist_ok=True)
    with open(HEAL_LOG, "a", encoding="utf-8") as fh:
        fh.write(json.dumps({"url": url, "broken": broken, "healed_with": used}) + "\n")
