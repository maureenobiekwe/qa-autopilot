"""Phase 6 - Reporting. Writes outputs/report.md and outputs/report.html."""
from __future__ import annotations

import html
import os
from typing import Any, Dict, Optional


def _verdict(execution: Optional[Dict[str, Any]], security: Optional[Dict[str, Any]]) -> str:
    if not execution:
        return "NOT RUN"
    if execution["failed"] or execution["total"] == 0:
        return "FAIL"
    if security and security.get("counts", {}).get("high"):
        return "PASS WITH SECURITY FINDINGS"
    return "PASS"


def markdown(workflow, trace, execution, security) -> str:
    out = [f"# QA Run Report\n\n**Goal:** {workflow['goal']}  \n**URL:** {workflow['base_url']}  \n**Domain:** {workflow['domain']}  \n**Planner:** {workflow['planner']}  \n**Verdict:** {_verdict(execution, security)}\n"]
    out.append("## Steps\n\n| # | Intent | Kind | Result |\n|---|---|---|---|")
    results = {s["n"]: s for s in (trace or {}).get("steps", [])}
    for step in workflow["steps"]:
        t = results.get(step["n"])
        res = "not reached" if not t else ("ok" if t["ok"] else f"failed: {t.get('error', 'assertion false')}")
        out.append(f"| {step['n']} | {step['intent']} | {step['kind']} | {res} |")
    if execution:
        out.append(f"\n## Execution\n\n{execution['passed']}/{execution['total']} passed in {execution['duration_s']}s. Self-heals used: {len(execution['healed'])}.\n")
        for f in execution["failures"]:
            out.append(f"- **{f['test']}**: {f['message']}")
    if security:
        out.append("\n## Security (passive)\n")
        if security.get("error"):
            out.append(f"Audit could not reach the site: {security['error']}")
        for f in security.get("findings", []):
            out.append(f"- **{f['severity'].upper()}** {f['title']}. {f['detail']}")
        if not security.get("findings") and not security.get("error"):
            out.append("No findings from passive checks.")
    return "\n".join(out) + "\n"


def html_report(md_text: str, trace, project_dir: str) -> str:
    body = "".join(f"<p>{html.escape(line)}</p>" if line.strip() else "" for line in md_text.splitlines())
    shots = ""
    for step in (trace or {}).get("steps", []):
        rel = step.get("screenshot")
        if rel and os.path.exists(os.path.join(project_dir, rel)):
            shots += f"<figure><img src='../{html.escape(rel)}' width='420'><figcaption>Step {step['n']}: {html.escape(step['intent'])}</figcaption></figure>"
    return (
        "<!doctype html><meta charset='utf-8'><title>QA Run Report</title>"
        "<style>body{font:15px/1.5 system-ui;max-width:900px;margin:2rem auto;padding:0 1rem}"
        "figure{display:inline-block;margin:.5rem}img{border:1px solid #ccc;border-radius:6px}</style>"
        f"{body}<h2>Screenshots</h2>{shots}"
    )


def write(project_dir: str, workflow, trace, execution, security) -> str:
    outputs = os.path.join(project_dir, "outputs")
    os.makedirs(outputs, exist_ok=True)
    md = markdown(workflow, trace, execution, security)
    with open(os.path.join(outputs, "report.md"), "w", encoding="utf-8") as fh:
        fh.write(md)
    with open(os.path.join(outputs, "report.html"), "w", encoding="utf-8") as fh:
        fh.write(html_report(md, trace, project_dir))
    return os.path.join(outputs, "report.md")
