"""
Shared scraping utilities: search + page qualification helpers
with rate-limit backoff, jitter, UA rotation, and DDG fallback.
"""

from __future__ import annotations

import random
import sys
import time
from dataclasses import dataclass
from typing import List, Set, Pattern, Optional

import requests
from requests import exceptions
from bs4 import BeautifulSoup
from googlesearch import search  # pip3 install googlesearch-python

# ---- Tunables ---------------------------------------------------------------

USER_AGENTS = [
    # A few modern desktop UAs
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
]
DEFAULT_HEADERS = {"User-Agent": random.choice(USER_AGENTS)}
TIMEOUT_SECS = 15.0
MAX_RESULTS_CAP = 1000  # Safety cap to avoid unbounded search growth
BACKOFFS = [5, 20, 45]  # Seconds to back off on repeated 429s
JITTER_RANGE = (0.25, 0.75)  # Add some randomness to sleeps

# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class SearchConfig:
    """Config for paginated crawling + throttling."""
    target_count: int = 10
    results_per_page: int = 8
    sleep_sec: float = 3.0


def _sleep_with_jitter(base: float) -> None:
    time.sleep(base + random.uniform(*JITTER_RANGE))


def _google_search(query: str, num_results: int) -> List[str]:
    # googlesearch-python doesn't expose headers; rely on backoff/fallback.
    return list(search(query, num_results=num_results))


def _ddg_search(query: str, num_results: int) -> List[str]:
    """
    DuckDuckGo fallback search.

    Prefers the renamed package `ddgs` (pip3 install ddgs).
    Falls back to `duckduckgo_search` if present.
    Returns a list of result URLs.
    """
    # Try the new package first
    try:
        from ddgs import DDGS  # pip3 install ddgs
        with DDGS() as ddgs:
            hits = ddgs.text(query, max_results=num_results)
            return [h.get("href") for h in hits if isinstance(h, dict) and h.get("href")]
    except Exception:
        pass

    # Fallback to the old package name if still installed
    try:
        from duckduckgo_search import DDGS  # legacy name
        with DDGS() as ddgs:
            hits = ddgs.text(query, max_results=num_results)
            return [h.get("href") for h in hits if isinstance(h, dict) and h.get("href")]
    except Exception:
        return []



def get_candidates(query: str, num_results: int) -> List[str]:
    """
    Try Google with exponential-style backoff on 429; then fall back to DDG.
    """
    for i, backoff in enumerate(BACKOFFS + [None]):  # last attempt has no further backoff
        try:
            return _google_search(query, num_results)
        except Exception as e:  # google blocked us or other error
            msg = str(e)
            is_429 = ("429" in msg) or ("Too Many Requests" in msg) or ("sorry/index" in msg)
            if is_429 and backoff is not None:
                print(
                    f"Google 429 — backing off {backoff}s (attempt {i+1}/{len(BACKOFFS)})",
                    file=sys.stderr,
                )
                _sleep_with_jitter(backoff)
                continue

            print(f"Google search failed ({e}). Trying DuckDuckGo…", file=sys.stderr)
            ddg = _ddg_search(query, num_results)
            if ddg:
                return ddg
            # If no fallback available or it returned empty, re-raise original error
            raise


def visible_text(html: str) -> str:
    """Return visible text by stripping scripts, styles, etc."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    return soup.get_text(" ", strip=True)


def count_pattern_on_page(
    url: str,
    pattern: Pattern[str],
    headers: Optional[dict[str, str]] = None,
    timeout: float = TIMEOUT_SECS,
    only_visible: bool = True,
) -> int:
    """
    Fetch a page and count occurrences of a compiled regex pattern.
    Returns 0 on any fetch/parse error.
    """
    try:
        h = dict(headers or {})
        h.setdefault("User-Agent", random.choice(USER_AGENTS))
        resp = requests.get(url, headers=h, timeout=timeout)
        resp.raise_for_status()
        content = visible_text(resp.text) if only_visible else resp.text
        return len(pattern.findall(content))
    except (
        exceptions.Timeout,
        exceptions.HTTPError,
        exceptions.ConnectionError,
        exceptions.RequestException,
        UnicodeDecodeError,
    ):
        return 0


def search_and_filter(
    query: str,
    pattern: Pattern[str],
    min_occurrences: int,
    config: SearchConfig = SearchConfig(),
) -> List[str]:
    """
    Run a search with `query`, visit candidates, and keep URLs whose page
    matches `pattern` at least `min_occurrences` times. Stops at `config.target_count`.
    """
    seen: Set[str] = set()
    qualifying: List[str] = []

    num_results = config.results_per_page
    while len(qualifying) < config.target_count and num_results <= MAX_RESULTS_CAP:
        try:
            candidates = get_candidates(query, num_results=num_results)
        except Exception as err:  # pylint: disable=broad-except
            print(f"Search failed: {err}", file=sys.stderr)
            break

        for url in candidates:
            if len(qualifying) >= config.target_count:
                break
            if url in seen:
                continue
            seen.add(url)

            occurrences = count_pattern_on_page(url, pattern)
            if occurrences >= min_occurrences:
                qualifying.append(url)
                print(f"[+] Found good site ({len(qualifying)}/{config.target_count}): {url}")

            _sleep_with_jitter(config.sleep_sec)

        num_results += config.results_per_page
        _sleep_with_jitter(config.sleep_sec)

    return qualifying[:config.target_count]


def run_search(
    query: str,
    pattern: Pattern[str],
    min_occurrences: int,
    config: SearchConfig = SearchConfig(),
) -> List[str]:
    """Thin wrapper so callers don’t duplicate the search/filter call signature."""
    return search_and_filter(
        query=query,
        pattern=pattern,
        min_occurrences=min_occurrences,
        config=config,
    )


def print_results(state: str, urls: List[str]) -> None:
    """Consistent, shared printing (avoids duplicate-code across scripts)."""
    print(f"\nFound {len(urls)} qualifying websites for {state}:\n")
    for url in urls:
        print(url)
