"""Phase checkpoints so a failed run resumes instead of starting over."""
from __future__ import annotations

import json
import os
from typing import Any, Dict

PHASES = ["discovery", "planning", "exploration", "generation", "execution", "security", "report"]


class Checkpoint:
    def __init__(self, project_dir: str):
        self.path = os.path.join(project_dir, ".checkpoint.json")
        self.state: Dict[str, Any] = {}
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as fh:
                self.state = json.load(fh)

    def done(self, phase: str) -> bool:
        return self.state.get(phase, {}).get("status") == "done"

    def mark(self, phase: str, status: str = "done", **info: Any) -> None:
        self.state[phase] = {"status": status, **info}
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(self.state, fh, indent=2)

    def clear(self) -> None:
        self.state = {}
        if os.path.exists(self.path):
            os.remove(self.path)
