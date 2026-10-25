#!/usr/bin/env python3
"""qa-autopilot entry point.

    python orchestrator.py --project projects/saucedemo_standard \
        --base_url https://www.saucedemo.com/ \
        --goal "Log in, add the first item to the cart, verify the cart badge shows 1"

Phases: discovery (--deep) -> planning -> exploration -> generation -> execution
        -> feedback/retry -> security (--security) -> report
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from core.agents import discovery, executor, explorer, feedback_agent, generator, planner, reporter, security_auditor  # noqa: E402
from core.lib import knowledge  # noqa: E402
from core.lib.env import load_env  # noqa: E402
from core.lib.checkpoint import Checkpoint  # noqa: E402
from core.llm import LLM  # noqa: E402

PHASE_CHOICES = ["planning", "exploration", "execution", "security"]


def load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path, data):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Goal in, tested and reported out.")
    p.add_argument("--project", required=True, help="Project directory, e.g. projects/my_app")
    p.add_argument("--goal", help="Test objective in plain language")
    p.add_argument("--base_url", help="Root URL of the app under test")
    p.add_argument("--deep", action="store_true", help="Crawl the site first and save sitemap.json")
    p.add_argument("--force", action="store_true", help="Ignore checkpoints and run every phase")
    p.add_argument("--headed", action="store_true", help="Show the browser")
    p.add_argument("--security", action="store_true", help="Run the passive security audit")
    p.add_argument("--phase", choices=PHASE_CHOICES, help="Run one phase only")
    p.add_argument("--max-retries", type=int, default=2, help="Feedback-loop retries after a failed run")
    return p


def load_config(project_dir: str, args) -> dict:
    path = os.path.join(project_dir, "config.json")
    cfg = load_json(path) if os.path.exists(path) else {}
    if args.base_url:
        cfg["base_url"] = args.base_url
    if args.goal:
        cfg["goal"] = args.goal
    cfg.setdefault("credentials", {})
    if not cfg.get("base_url") or not cfg.get("goal"):
        sys.exit("Need --base_url and --goal (or a config.json that has them).")
    dump_json(path, cfg)  # saved BEFORE the env override, so secrets never reach disk
    cfg = json.loads(json.dumps(cfg))
    cfg["credentials"]["username"] = os.getenv("QA_USERNAME", cfg["credentials"].get("username", ""))
    cfg["credentials"]["password"] = os.getenv("QA_PASSWORD", cfg["credentials"].get("password", ""))
    return cfg


def main() -> int:
    load_env()
    args = build_parser().parse_args()
    project_dir = os.path.abspath(args.project)
    os.makedirs(project_dir, exist_ok=True)
    cfg = load_config(project_dir, args)
    cp = Checkpoint(project_dir)
    if args.force:
        cp.clear()
    llm = LLM()
    print(f"[mode] {'LLM (' + llm.model + ')' if llm.online else 'offline heuristics (set ANTHROPIC_API_KEY for LLM planning)'}")

    def want(phase_name):
        return args.phase in (None, phase_name)

    workflow_path = os.path.join(project_dir, "workflow.json")
    trace_path = os.path.join(project_dir, "outputs", "trace.json")
    exec_path = os.path.join(project_dir, "execution.json")
    sec_path = os.path.join(project_dir, "outputs", "security.json")
    os.makedirs(os.path.join(project_dir, "outputs"), exist_ok=True)

    # Phase 1: discovery
    if args.deep and want("planning") and (args.force or not cp.done("discovery")):
        print("[1] semantic discovery")
        sitemap = discovery.crawl(cfg["base_url"], headed=args.headed)
        discovery.save(sitemap, os.path.join(project_dir, "sitemap.json"))
        cp.mark("discovery", pages=len(sitemap["pages"]))

    # Phase 2: planning
    if want("planning") and (args.force or not cp.done("planning") or not os.path.exists(workflow_path)):
        print("[2] planning")
        domain_name = knowledge.detect_domain(cfg["goal"], cfg["base_url"])
        domain = knowledge.load_domains().get(domain_name, {})
        workflow = planner.plan(cfg["goal"], cfg["base_url"], domain_name, domain, llm)
        planner.save(workflow, workflow_path)
        cp.mark("planning", steps=len(workflow["steps"]), planner=workflow["planner"])
        print(f"    domain={domain_name} planner={workflow['planner']} steps={len(workflow['steps'])}")
    workflow = load_json(workflow_path)

    trace = load_json(trace_path) if os.path.exists(trace_path) else None
    execution = None
    timeout_ms = 60000

    # Phases 3-5 with the closed feedback loop
    if want("exploration") or want("execution"):
        attempt = 0
        while True:
            if want("exploration") and (args.force or attempt > 0 or not cp.done("exploration") or trace is None):
                print(f"[3] exploration (attempt {attempt + 1})")
                trace = explorer.explore(project_dir, workflow, cfg, llm, args.headed, timeout_ms)
                dump_json(trace_path, trace)
                cp.mark("exploration", complete=trace["complete"])
                if not trace["complete"]:
                    bad = next((s for s in trace["steps"] if not s["ok"]), {})
                    print(f"    exploration stopped at step {bad.get('n')}: {bad.get('error', 'assertion false')}")
            if trace and trace["complete"]:
                test_file = generator.generate(project_dir, workflow, trace)
                cp.mark("generation", file=os.path.relpath(test_file, ROOT))
            if want("execution") and trace and trace["complete"]:
                print("[4] execution")
                execution = executor.run(project_dir, args.headed)
                dump_json(exec_path, execution)
                cp.mark("execution", passed=execution["passed"], failed=execution["failed"])
                print(f"    {execution['passed']}/{execution['total']} passed, {len(execution['healed'])} self-heals")
            if execution is None or execution["failed"] == 0 and (trace and trace["complete"]):
                break
            if attempt >= args.max_retries:
                break
            exec_for_feedback = execution or {"failures": [{"test": "exploration", "message": next((s.get("error", "") for s in trace["steps"] if not s["ok"]), ""), "detail": ""}], "healed": []}
            advice = feedback_agent.analyze(project_dir, cfg["base_url"], exec_for_feedback, attempt + 1)
            print(f"[feedback] classes={advice['classes']} reexplore={advice['reexplore']}")
            if not advice["reexplore"]:
                break
            timeout_ms = advice["timeout_ms"]
            attempt += 1
            execution = None
            args.force = False
        if trace is not None and not trace["complete"] and execution is None:
            feedback_agent.analyze(project_dir, cfg["base_url"], {"failures": [{"test": "exploration", "message": next((s.get("error", "") for s in trace["steps"] if not s["ok"]), ""), "detail": ""}], "healed": []}, attempt + 1)
    elif os.path.exists(exec_path):
        execution = load_json(exec_path)

    # Phase 5: security
    security = None
    if args.security and want("security"):
        print("[5] passive security audit")
        security = security_auditor.audit(cfg["base_url"], trace)
        dump_json(sec_path, security)
        print(f"    findings: {security.get('counts', security.get('error'))}")
    elif os.path.exists(sec_path):
        security = load_json(sec_path)

    # Phase 6: report
    report = reporter.write(project_dir, workflow, trace, execution, security)
    print(f"[report] {os.path.relpath(report, ROOT)}")
    failed = (execution or {}).get("failed", 0) or (trace is not None and not trace["complete"])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
