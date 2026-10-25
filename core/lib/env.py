"""Tiny .env loader (no extra dependency).

Reads KEY=value lines from <repo>/.env into os.environ. Real environment variables win,
and empty values are skipped so a blank line in .env never overrides config.json.
"""
from __future__ import annotations

import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_env(path: str | None = None) -> None:
    path = path or os.path.join(ROOT, ".env")
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip("\"'")
            if key and value:
                os.environ.setdefault(key, value)
