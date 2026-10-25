"""Knowledge bank: domain blueprints (YAML) and per-site lessons (JSON)."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List
from urllib.parse import urlparse

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOMAINS_DIR = os.path.join(ROOT, "knowledge", "domains")
SITES_DIR = os.path.join(ROOT, "knowledge", "sites")


def load_domains() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    if not os.path.isdir(DOMAINS_DIR):
        return out
    for name in sorted(os.listdir(DOMAINS_DIR)):
        if name.endswith((".yaml", ".yml")):
            with open(os.path.join(DOMAINS_DIR, name), encoding="utf-8") as fh:
                out[name.rsplit(".", 1)[0]] = yaml.safe_load(fh) or {}
    return out


def detect_domain(goal: str, url: str = "") -> str:
    """Pick the domain whose keywords overlap the goal the most. Falls back to 'generic'."""
    text = f"{goal} {url}".lower()
    best, best_score = "generic", 0
    for name, blueprint in load_domains().items():
        score = sum(1 for kw in blueprint.get("keywords", []) if kw in text)
        if score > best_score:
            best, best_score = name, score
    return best


def _site_path(base_url: str) -> str:
    host = urlparse(base_url).netloc.replace(":", "_") or "unknown"
    return os.path.join(SITES_DIR, f"{host}.json")


def load_site(base_url: str) -> Dict[str, Any]:
    path = _site_path(base_url)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    return {"host": urlparse(base_url).netloc, "lessons": [], "avoid": [], "stable_patterns": []}


def save_site(base_url: str, data: Dict[str, Any]) -> None:
    os.makedirs(SITES_DIR, exist_ok=True)
    with open(_site_path(base_url), "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def add_lesson(base_url: str, lesson: str, avoid: List[str] | None = None) -> None:
    site = load_site(base_url)
    if lesson not in site["lessons"]:
        site["lessons"].append(lesson)
    for item in avoid or []:
        if item not in site["avoid"]:
            site["avoid"].append(item)
    save_site(base_url, site)
