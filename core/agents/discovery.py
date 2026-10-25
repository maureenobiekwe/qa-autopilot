"""Phase 1 - Semantic discovery (--deep only). Crawls same-origin pages and builds sitemap.json."""
from __future__ import annotations

import json
from collections import deque
from typing import Any, Dict, List
from urllib.parse import urldefrag, urljoin, urlparse

from core.lib.browser import launch, mine

PAGE_SUMMARY_JS = """
() => ({
  title: document.title,
  headings: [...document.querySelectorAll('h1,h2')].slice(0, 6).map(h => h.innerText.trim()),
  forms: [...document.forms].map(f => ({
    action: f.getAttribute('action') || '',
    method: (f.method || 'get').toLowerCase(),
    fields: [...f.elements].filter(e => e.name || e.id).map(e => (e.name || e.id) + ':' + (e.type || e.tagName.toLowerCase())),
  })),
})
"""


def crawl(base_url: str, max_pages: int = 8, headed: bool = False) -> Dict[str, Any]:
    origin = urlparse(base_url).netloc
    queue = deque([base_url])
    seen, pages = set(), []
    with launch(headed) as (page, _ctx):
        while queue and len(pages) < max_pages:
            url = urldefrag(queue.popleft())[0]
            if url in seen:
                continue
            seen.add(url)
            try:
                resp = page.goto(url, wait_until="domcontentloaded")
            except Exception as exc:  # noqa: BLE001
                pages.append({"url": url, "error": type(exc).__name__})
                continue
            summary = page.evaluate(PAGE_SUMMARY_JS)
            elements = mine(page)
            links: List[str] = []
            for el in elements:
                if el["tag"] == "a" and el["href"]:
                    target = urldefrag(urljoin(page.url, el["href"]))[0]
                    if urlparse(target).netloc == origin and target not in seen:
                        links.append(target)
                        queue.append(target)
            pages.append(
                {
                    "url": page.url,
                    "status": resp.status if resp else None,
                    "interactive_elements": len(elements),
                    "links_found": len(set(links)),
                    **summary,
                }
            )
    return {"base_url": base_url, "pages": pages}


def save(sitemap: Dict[str, Any], path: str) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(sitemap, fh, indent=2)
