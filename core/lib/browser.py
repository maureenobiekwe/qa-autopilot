"""Playwright helpers shared by the agents: page launch and DOM mining."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Dict, List

# Runs in the page. Returns every visible interactive element with the attributes
# smart_locator needs to build ranked candidates.
MINE_JS = r"""
() => {
  const sel = 'a[href], button, input, select, textarea, [role=button], [role=link], [role=tab], [role=checkbox], [role=menuitem]';
  const seen = new Set();
  const out = [];
  const visible = (e) => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const cssPath = (e) => { if (e.id) return '#' + CSS.escape(e.id);
    const parts = []; while (e && e.nodeType === 1 && parts.length < 4) {
      let p = e.tagName.toLowerCase(); const par = e.parentElement;
      if (par) { const sib = [...par.children].filter(c => c.tagName === e.tagName);
        if (sib.length > 1) p += ':nth-of-type(' + (sib.indexOf(e) + 1) + ')'; }
      parts.unshift(p); e = par; } return parts.join(' > '); };
  const roleOf = (e) => { const r = e.getAttribute('role'); if (r) return r;
    const t = e.tagName.toLowerCase();
    if (t === 'a') return 'link'; if (t === 'button') return 'button'; if (t === 'select') return 'combobox';
    if (t === 'textarea') return 'textbox';
    if (t === 'input') { const ty = (e.type || 'text').toLowerCase();
      if (['button', 'submit', 'reset'].includes(ty)) return 'button';
      if (ty === 'checkbox') return 'checkbox'; if (ty === 'radio') return 'radio';
      return 'textbox'; } return ''; };
  const labelOf = (e) => { if (e.id) { const l = document.querySelector('label[for="' + CSS.escape(e.id) + '"]'); if (l) return l.innerText.trim(); }
    const wrap = e.closest('label'); if (wrap) return wrap.innerText.trim();
    return e.getAttribute('aria-label') || ''; };
  document.querySelectorAll(sel).forEach((e, i) => {
    if (seen.has(e) || !visible(e)) return; seen.add(e);
    const text = (e.innerText || e.value || '').trim().replace(/\s+/g, ' ');
    const role = roleOf(e);
    const label = labelOf(e);
    const name = (label || e.getAttribute('aria-label') || text || e.getAttribute('placeholder') || e.getAttribute('title') || '').trim();
    out.push({
      idx: out.length, tag: e.tagName.toLowerCase(), type: e.type || '', role, name: name.slice(0, 80),
      text: text.slice(0, 80), label: label.slice(0, 80), placeholder: e.getAttribute('placeholder') || '',
      id: e.id || '', html_name: e.getAttribute('name') || '',
      'data-test': e.getAttribute('data-test') || '', 'data-testid': e.getAttribute('data-testid') || '',
      'data-qa': e.getAttribute('data-qa') || '', 'data-cy': e.getAttribute('data-cy') || '',
      href: e.getAttribute('href') || '', css: cssPath(e),
    });
  });
  return out;
}
"""


@contextmanager
def launch(headed: bool = False, timeout_ms: int = 60000):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not headed)
        context = browser.new_context(viewport={"width": 1366, "height": 850})
        context.set_default_timeout(timeout_ms)
        page = context.new_page()
        try:
            yield page, context
        finally:
            context.close()
            browser.close()


def mine(page) -> List[Dict[str, Any]]:
    return page.evaluate(MINE_JS)
