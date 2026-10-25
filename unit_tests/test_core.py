"""Offline unit tests. No browser, no network, no API key."""
import ast
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.agents import explorer, feedback_agent, generator, planner, reporter
from core.lib import knowledge
from core.lib.smart_locator import build_candidates
from core.llm import LLM, extract_json

ELEMENTS = [
    {"idx": 0, "tag": "input", "type": "text", "role": "textbox", "name": "Username", "text": "", "label": "", "placeholder": "Username", "id": "user-name", "html_name": "user-name", "data-test": "username", "css": "#user-name"},
    {"idx": 1, "tag": "input", "type": "password", "role": "textbox", "name": "Password", "text": "", "label": "", "placeholder": "Password", "id": "password", "html_name": "password", "data-test": "password", "css": "#password"},
    {"idx": 2, "tag": "input", "type": "submit", "role": "button", "name": "Login", "text": "Login", "label": "", "placeholder": "", "id": "login-button", "html_name": "login-button", "data-test": "login-button", "css": "#login-button"},
    {"idx": 3, "tag": "button", "type": "submit", "role": "button", "name": "Add to cart", "text": "Add to cart", "label": "", "placeholder": "", "id": "add-to-cart-backpack", "html_name": "add-to-cart-backpack", "data-test": "add-to-cart-backpack", "css": "#add"},
]


def test_extract_json_handles_fences_and_noise():
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert extract_json('Sure! {"a": [1,2]} done') == {"a": [1, 2]}
    assert extract_json("not json", fallback="x") == "x"


def test_llm_offline_returns_fallback(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    llm = LLM()
    assert not llm.online
    assert llm.json("s", "u", fallback={"ok": True}) == {"ok": True}


def test_heuristic_plan_classifies_steps():
    steps = planner.heuristic_plan("Log in, add the first item to the cart, verify the cart badge shows 1", {})
    assert [s["kind"] for s in steps] == ["login", "action", "verify"]
    assert [s["n"] for s in steps] == [1, 2, 3]


def test_plan_adds_default_assertion_when_goal_has_none():
    steps = planner.heuristic_plan("Log in and add item", {"default_assertions": ["the cart shows the item"]})
    assert steps[-1]["kind"] == "verify"


def test_domain_detection():
    assert knowledge.detect_domain("transfer funds between accounts and check the balance") == "banking"
    assert knowledge.detect_domain("add to cart and checkout") == "ecommerce"
    assert knowledge.detect_domain("zzz qqq") == "generic"


def test_candidates_are_ordered_most_stable_first():
    kinds = [c["kind"] for c in build_candidates(ELEMENTS[0])]
    assert kinds[0] == "test_id"
    assert kinds.index("role") < kinds.index("id") < kinds.index("css")


def test_login_actions_find_user_password_submit():
    acts = explorer.login_actions(ELEMENTS)
    assert [a["action"] for a in acts] == ["fill", "fill", "click"]
    assert acts[0]["value"] == "{{credentials.username}}"
    assert acts[1]["value"] == "{{credentials.password}}"


def test_heuristic_action_picks_matching_element():
    act = explorer.heuristic_action("add the first item to the cart", ELEMENTS)
    assert act["action"] == "click" and act["idx"] == 3
    assert explorer.heuristic_action("do something unrelated xyz", ELEMENTS)["action"] == "none"


def test_feedback_classifies_failures():
    assert feedback_agent.classify("LookupError: No locator matched. Tried: css='#x'") == "locator"
    assert feedback_agent.classify("playwright._impl._errors.TimeoutError: Timeout 60000ms") == "timeout"
    assert feedback_agent.classify("AssertionError: expected text not on page") == "assertion"
    assert feedback_agent.classify("net::ERR_NAME_NOT_RESOLVED") == "network"


def test_feedback_writes_lesson_and_log(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge, "SITES_DIR", str(tmp_path / "sites"))
    execution = {"failures": [{"test": "t", "message": "x", "detail": "LookupError: No locator matched. Tried: css='#gone': TimeoutError"}], "healed": []}
    advice = feedback_agent.analyze(str(tmp_path), "https://demo.example/", execution, 1)
    assert advice["classes"] == ["locator"] and advice["reexplore"] is True
    site = knowledge.load_site("https://demo.example/")
    assert site["lessons"]
    assert (tmp_path / "qa_session_logs.json").exists()


def test_assertion_failure_does_not_trigger_reexploration(tmp_path, monkeypatch):
    monkeypatch.setattr(knowledge, "SITES_DIR", str(tmp_path / "sites"))
    execution = {"failures": [{"test": "t", "message": "AssertionError", "detail": ""}], "healed": []}
    assert feedback_agent.analyze(str(tmp_path), "https://demo.example/", execution, 1)["reexplore"] is False


def test_generator_output_is_valid_python(tmp_path):
    workflow = {"goal": "Log in", "base_url": "https://x.test/", "steps": [{"n": 1, "intent": "log in", "kind": "login"}]}
    trace = {"steps": [{"n": 1, "intent": "log in", "actions": [
        {"action": "fill", "value": "{{credentials.username}}", "candidates": build_candidates(ELEMENTS[0])},
        {"action": "click", "value": "", "candidates": build_candidates(ELEMENTS[2])},
        {"action": "assert_text", "value": "products", "ok": True},
    ]}]}
    project = tmp_path / "projects" / "demo"
    path = generator.generate(str(project), workflow, trace)
    source = open(path, encoding="utf-8").read()
    ast.parse(source)
    assert "resolve(page" in source and "credentials.username" in source


def test_env_file_loads_but_skips_blanks_and_does_not_override(tmp_path, monkeypatch):
    from core.lib.env import load_env

    f = tmp_path / ".env"
    f.write_text("# c\nQA_TEST_A=hello\nQA_TEST_B=\nQA_TEST_C='quoted'\nQA_TEST_D=fromfile\n", encoding="utf-8")
    for k in ("QA_TEST_A", "QA_TEST_B", "QA_TEST_C"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("QA_TEST_D", "fromshell")
    load_env(str(f))
    assert os.environ["QA_TEST_A"] == "hello"
    assert "QA_TEST_B" not in os.environ
    assert os.environ["QA_TEST_C"] == "quoted"
    assert os.environ["QA_TEST_D"] == "fromshell"
    for k in ("QA_TEST_A", "QA_TEST_C"):
        monkeypatch.delenv(k, raising=False)


def test_env_credentials_never_written_to_config_json(tmp_path, monkeypatch):
    import orchestrator

    project = tmp_path / "p"
    project.mkdir()
    (project / "config.json").write_text(json.dumps({"base_url": "http://x.test", "goal": "g", "credentials": {}}), encoding="utf-8")
    monkeypatch.setenv("QA_USERNAME", "secret_user")
    monkeypatch.setenv("QA_PASSWORD", "secret_pass")
    args = orchestrator.build_parser().parse_args(["--project", str(project)])
    cfg = orchestrator.load_config(str(project), args)
    assert cfg["credentials"]["password"] == "secret_pass"
    assert "secret_pass" not in (project / "config.json").read_text(encoding="utf-8")


def test_report_verdicts():
    wf = {"goal": "g", "base_url": "u", "domain": "generic", "planner": "heuristic", "steps": [{"n": 1, "intent": "i", "kind": "action"}]}
    trace = {"steps": [{"n": 1, "ok": True}]}
    ok = {"total": 1, "passed": 1, "failed": 0, "duration_s": 1, "healed": [], "failures": []}
    bad = {**ok, "passed": 0, "failed": 1, "failures": [{"test": "t", "message": "boom"}]}
    assert "PASS" in reporter.markdown(wf, trace, ok, None)
    assert "FAIL" in reporter.markdown(wf, trace, bad, None)
    sec = {"findings": [{"severity": "high", "title": "T", "detail": "d"}], "counts": {"high": 1}}
    assert "SECURITY FINDINGS" in reporter.markdown(wf, trace, ok, sec)
