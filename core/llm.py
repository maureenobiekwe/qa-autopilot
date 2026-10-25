"""Thin LLM wrapper.

Online  -> Anthropic API (set ANTHROPIC_API_KEY).
Offline -> returns None so every agent falls back to its deterministic heuristic.
The pipeline therefore always runs; the LLM only makes it smarter.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

DEFAULT_MODEL = os.getenv("QA_MODEL", "claude-sonnet-5-5")


class LLM:
    def __init__(self, model: Optional[str] = None):
        self.model = model or DEFAULT_MODEL
        self.client = None
        key = os.getenv("ANTHROPIC_API_KEY")
        if key:
            try:
                import anthropic  # imported lazily so offline mode needs no SDK

                self.client = anthropic.Anthropic(api_key=key)
            except ImportError:
                self.client = None

    @property
    def online(self) -> bool:
        return self.client is not None

    def complete(self, system: str, user: str, max_tokens: int = 3000) -> Optional[str]:
        if not self.online:
            return None
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")

    def json(self, system: str, user: str, fallback: Any = None, max_tokens: int = 3000) -> Any:
        """Ask for JSON only. Returns `fallback` offline or if the reply cannot be parsed."""
        text = self.complete(system + "\nReply with valid JSON only. No prose, no code fences.", user, max_tokens)
        if text is None:
            return fallback
        return extract_json(text, fallback)


def extract_json(text: str, fallback: Any = None) -> Any:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"(\{.*\}|\[.*\])", text, re.S)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
    return fallback
