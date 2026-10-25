"""Phase 5 - Passive security audit. Read-only: one GET, plus what the exploration already saw.

It never sends payloads, never brute-forces, never touches a host other than the project's base_url.
Run it only against systems you are authorised to test.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import urlparse

import requests

HEADER_CHECKS = [
    ("content-security-policy", "medium", "No Content-Security-Policy. Injected scripts are not restricted."),
    ("x-content-type-options", "low", "X-Content-Type-Options: nosniff is missing."),
    ("referrer-policy", "low", "No Referrer-Policy. Full URLs may leak to third parties."),
]
TOKEN_KEY = re.compile(r"token|jwt|auth|session|secret|password", re.I)


def _finding(sev: str, title: str, detail: str) -> Dict[str, str]:
    return {"severity": sev, "title": title, "detail": detail}


def audit(base_url: str, trace: Dict[str, Any] | None = None) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []
    parsed = urlparse(base_url)
    try:
        resp = requests.get(base_url, timeout=20, allow_redirects=True, headers={"User-Agent": "qa-autopilot-audit/1.0"})
    except requests.RequestException as exc:
        return {"base_url": base_url, "error": type(exc).__name__, "findings": []}
    headers = {k.lower(): v for k, v in resp.headers.items()}
    final = urlparse(resp.url)

    if final.scheme != "https":
        findings.append(_finding("high", "Site is served over HTTP", f"Final URL {resp.url} is not HTTPS. Credentials and tokens travel in clear text."))
    else:
        if "strict-transport-security" not in headers:
            findings.append(_finding("medium", "No HSTS header", "Strict-Transport-Security is missing, so downgrade attacks are possible."))
    if parsed.scheme == "https":
        try:
            plain = requests.get(base_url.replace("https://", "http://", 1), timeout=10, allow_redirects=False)
            location = plain.headers.get("Location", "")
            if plain.status_code < 300 or not location.startswith("https://"):
                findings.append(_finding("medium", "HTTP does not redirect to HTTPS", f"http:// returned {plain.status_code} without an https redirect."))
        except requests.RequestException:
            pass
    for header, sev, msg in HEADER_CHECKS:
        if header not in headers:
            findings.append(_finding(sev, f"Missing header: {header}", msg))
    if "x-frame-options" not in headers and "frame-ancestors" not in headers.get("content-security-policy", ""):
        findings.append(_finding("medium", "Clickjacking protection missing", "Neither X-Frame-Options nor CSP frame-ancestors is set."))
    if "server" in headers and re.search(r"\d", headers["server"]):
        findings.append(_finding("low", "Server version disclosed", f"Server header reveals: {headers['server']}"))

    for cookie in resp.cookies:
        flags = []
        if not cookie.secure and final.scheme == "https":
            flags.append("Secure")
        if not cookie.has_nonstandard_attr("HttpOnly"):
            flags.append("HttpOnly")
        if not (cookie.has_nonstandard_attr("SameSite") or cookie.has_nonstandard_attr("samesite")):
            flags.append("SameSite")
        if flags:
            sev = "high" if TOKEN_KEY.search(cookie.name) else "low"
            findings.append(_finding(sev, f"Cookie '{cookie.name}' missing {', '.join(flags)}", "Cookie flags protect the session from theft and CSRF."))

    if trace:
        for scope, keys in trace.get("storage_keys", {}).items():
            hits = [k for k in keys if TOKEN_KEY.search(k)]
            if hits:
                findings.append(_finding("high", f"Token-like keys in {scope}Storage", f"{', '.join(hits)}. Anything readable by JavaScript is stolen by a single XSS. Prefer httpOnly cookies."))

    order = {"high": 0, "medium": 1, "low": 2}
    findings.sort(key=lambda f: order[f["severity"]])
    return {"base_url": base_url, "status": resp.status_code, "findings": findings, "counts": {s: sum(1 for f in findings if f["severity"] == s) for s in order}}
