"""
Shared scraping utilities: Google search + page qualification helpers.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import List, Set, Pattern, Optional

import requests
from requests import exceptions
from bs4 import BeautifulSoup
from googlesearch import search

DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT_SECS = 15.0
MAX_RESULTS_CAP = 1000  # Safety cap to avoid unbounded search growth


@dataclass(frozen=True)
class SearchConfig:
    """Config for paginated Google crawling + throttling."""
    target_count: int = 10
    results_per_page: int = 10
    sleep_sec: float = 1.0


def get_candidates(query: str, num_results: int) -> List[str]:
    """Return up to num_results Google results for the query."""
    return list(search(query, num_results=num_results))


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
        response = requests.get(url, headers=headers or DEFAULT_HEADERS, timeout=timeout)
        content = visible_text(response.text) if only_visible else response.text
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
    Run a Google search with `query`, visit candidates, and keep URLs whose page
    matches `pattern` at least `min_occurrences` times. Stops at `config.target_count`.
    """
    seen: Set[str] = set()
    qualifying: List[str] = []

    num_results = config.results_per_page
    while len(qualifying) < config.target_count and num_results <= MAX_RESULTS_CAP:
        try:
            candidates = get_candidates(query, num_results=num_results)
        except Exception as err:  # pylint: disable=broad-except
            print(f"Google search failed: {err}")
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

            time.sleep(config.sleep_sec)

        num_results += config.results_per_page
        time.sleep(config.sleep_sec)

    return qualifying[:config.target_count]


def run_search(
    query: str,
    pattern: Pattern[str],
    min_occurrences: int,
    config: SearchConfig = SearchConfig(),
) -> List[str]:
    """Thin wrapper so callers don’t duplicate the search/filter call signature."""
    return search_and_filter(query=query, pattern=pattern, min_occurrences=min_occurrences, config=config)


def print_results(state: str, urls: List[str]) -> None:
    """Consistent, shared printing (avoids duplicate-code across scripts)."""
    print(f"\nFound {len(urls)} qualifying websites for {state}:\n")
    for url in urls:
        print(url)
