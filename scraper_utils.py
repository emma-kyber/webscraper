"""
Shared scraping utilities: resilient search + page qualification helpers
with caching, retry-on-429, jitter, UA rotation, and opt-in Google fallback.
"""

from __future__ import annotations

import os
import sys
import time
import random
from dataclasses import dataclass
from typing import List, Optional, Pattern, Set

import requests
from requests import exceptions
from bs4 import BeautifulSoup

# Optional SerpAPI (paid Google API) — set SERPAPI_KEY env var to enable
try:
    from serpapi import GoogleSearch, SerpApiError  # pip install google-search-results
except ImportError:
    GoogleSearch = None  # type: ignore
    SerpApiError = Exception  # type: ignore

# --- Search backends ---------------------------------------------------------

# Prefer the renamed DuckDuckGo package; fall back to legacy name if needed.
try:
    from ddgs import DDGS as DDGSEARCH  # pip install -U ddgs
except ImportError:
    try:
        from duckduckgo_search import DDGS as DDGSEARCH  # legacy
    except ImportError:
        DDGSEARCH = None  # type: ignore

# Optional SerpAPI (paid Google API) — set SERPAPI_KEY env var to enable
SERPAPI_KEY = os.getenv("SERPAPI_KEY")

# Optional googlesearch-python (fragile; only used if DISABLE_GOOGLE=0)
try:
    from googlesearch import search as GOOGLESEARCH  # pip install googlesearch-python
except ImportError:
    GOOGLESEARCH = None  # type: ignore

# Transparent caching to avoid re-fetching pages across runs (24h)
try:
    import requests_cache  # pip install requests-cache
    requests_cache.install_cache(
        "scraper_cache",
        backend="sqlite",
        expire_after=24 * 60 * 60,  # 24 hours
        allowable_methods=("GET",),
        allowable_codes=(200,),
    )
except ImportError:
    requests_cache = None  # type: ignore

# --- Tunables ----------------------------------------------------------------

USER_AGENTS = [
    # macOS Chrome
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    # Windows Chrome
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    # Ubuntu Firefox
    (
        "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:124.0) "
        "Gecko/20100101 Firefox/124.0"
    ),
    # macOS Safari
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15"
    ),
    # iPhone Safari
    (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1"
    ),
    # iPad Safari
    (
        "Mozilla/5.0 (iPad; CPU OS 16_4 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1"
    ),
    # Android Chrome
    (
        "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
    ),
    # Windows Edge
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 "
        "Edg/124.0.2478.67"
    ),
    # Linux Chrome
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    # Windows Firefox
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) "
        "Gecko/20100101 Firefox/124.0"
    ),
]

DEFAULT_HEADERS = {"User-Agent": random.choice(USER_AGENTS)}
TIMEOUT_SECS = 20.0
MAX_RESULTS_CAP = 1000
BACKOFFS = [10, 30, 60]  # used for search fallback retries
JITTER_RANGE = (0.5, 1.0)
PER_HOST_DELAY = 1.0
RETRY_STATUS = {429, 500, 502, 503, 504}

# Default to *disabling* Google scraping fallback (prevents 429s).
# Set DISABLE_GOOGLE=0 to enable googlesearch fallback.
DISABLE_GOOGLE = os.getenv("DISABLE_GOOGLE", "1") == "1"

# ----------------------------------------------------------------------------


@dataclass(frozen=True)
class SearchConfig:
    """Config for paginated crawling + throttling."""
    target_count: int = 10
    results_per_page: int = 5
    sleep_sec: float = 5.0


def _sleep_with_jitter(base: float) -> None:
    time.sleep(base + random.uniform(*JITTER_RANGE))


# --- Search helpers ----------------------------------------------------------

def _serpapi_search(query: str, num_results: int) -> List[str]:
    """Optional SerpAPI Google search if SERPAPI_KEY set; else []."""
    if not SERPAPI_KEY or GoogleSearch is None:
        return []
    try:
        params = {
            "engine": "google",
            "q": query,
            "num": min(num_results, 100),
            "api_key": SERPAPI_KEY,
        }
        results = GoogleSearch(params).get_dict()
        organic = results.get("organic_results", []) or []
        return [item.get("link") for item in organic if item.get("link")]
    except (SerpApiError, requests.RequestException, ValueError) as e:
        print(f"SerpAPI error: {e}", file=sys.stderr)
        return []


def _ddg_search(query: str, num_results: int) -> List[str]:
    """
    Robust DuckDuckGo search that works across ddgs/duckduckgo_search variants.
    Retries a few times with exponential backoff. Returns [] on failure.
    """
    if DDGSEARCH is None:
        return []

    tries = 3
    backoff = 2.0

    for attempt in range(1, tries + 1):
        ddg_obj = None
        try:
            ddg_obj = DDGSEARCH()
            hits_iter = ddg_obj.text(query, max_results=num_results)
            hits = list(hits_iter) if hits_iter is not None else []
            urls = [h.get("href") for h in hits if isinstance(h, dict) and h.get("href")]
            if urls:
                try:
                    if ddg_obj is not None and hasattr(ddg_obj, "close"):
                        ddg_obj.close()  # type: ignore[attr-defined]
                except (OSError, TypeError, AttributeError):
                    pass
                return urls
        except (RuntimeError, ValueError) as err:
            print(
                f"DDG search error (attempt {attempt}/{tries}): {err}",
                file=sys.stderr,
            )
        except Exception as err:  # pylint: disable=broad-exception-caught
            print(
                f"DDG unexpected error (attempt {attempt}/{tries}): {err}",
                file=sys.stderr,
            )
        finally:
            try:
                if ddg_obj is not None and hasattr(ddg_obj, "close"):
                    ddg_obj.close()  # type: ignore[attr-defined]
            except (OSError, TypeError, AttributeError):
                pass

        _sleep_with_jitter(backoff)
        backoff *= 2

    return []


def _google_search(query: str, num_results: int) -> List[str]:
    """Return up to num_results Google results for the query (googlesearch-python)."""
    if GOOGLESEARCH is None:
        return []
    return list(GOOGLESEARCH(query, num_results=num_results))


def get_candidates(query: str, num_results: int) -> List[str]:
    """
    Prefer resilient/clean backends to minimize 429s:
      1) SerpAPI (if configured)
      2) DuckDuckGo (ddgs)
      3) Google (googlesearch-python) ONLY if DISABLE_GOOGLE=0
    """
    # 0) SerpAPI (paid, reliable)
    sa = _serpapi_search(query, num_results)
    if sa:
        return sa

    # 1) DDG primary
    ddg = _ddg_search(query, num_results)
    if ddg:
        return ddg

    # 2) Optional Google fallback (disabled by default)
    if not DISABLE_GOOGLE:
        for attempt, backoff in enumerate(BACKOFFS + [None], start=1):
            try:
                g = _google_search(query, num_results)
                if g:
                    return g
            except Exception as err:  # pylint: disable=broad-exception-caught
                msg = str(err)
                is_429 = ("429" in msg) or ("Too Many Requests" in msg) or ("sorry/index" in msg)
                if is_429 and backoff is not None:
                    print(
                        f"Google 429 — backing off {backoff}s (attempt {attempt}/{len(BACKOFFS)})",
                        file=sys.stderr,
                    )
                    _sleep_with_jitter(backoff)
                    continue
                print(f"Google search failed ({err}).", file=sys.stderr)

            if backoff is not None:
                _sleep_with_jitter(backoff)
                continue

    # Nothing worked
    raise RuntimeError("No search backend returned results.")


# --- Fetching & parsing ------------------------------------------------------

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
    Returns 0 on any fetch/parse error. Retries on transient errors.
    """
    tries = 3
    backoff = 3.0
    for attempt in range(1, tries + 1):
        try:
            hdrs = dict(headers or {})
            hdrs.setdefault("User-Agent", random.choice(USER_AGENTS))
            hdrs.setdefault(
                "Accept",
                "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            )
            hdrs.setdefault("Accept-Language", "en-US,en;q=0.9")
            hdrs.setdefault("Connection", "close")

            time.sleep(PER_HOST_DELAY)
            resp = requests.get(url, headers=hdrs, timeout=timeout)
            status = getattr(resp, "status_code", 0)
            if status in RETRY_STATUS:
                if attempt < tries:
                    _sleep_with_jitter(backoff)
                    backoff *= 2
                    continue
                return 0

            resp.raise_for_status()
            content = visible_text(resp.text) if only_visible else resp.text
            return len(pattern.findall(content))
        except (
            exceptions.Timeout,
            exceptions.ConnectionError,
            exceptions.ChunkedEncodingError,
        ):
            if attempt < tries:
                _sleep_with_jitter(backoff)
                backoff *= 2
                continue
            return 0
        except (exceptions.HTTPError, exceptions.RequestException, UnicodeDecodeError):
            return 0


# --- Orchestration -----------------------------------------------------------

def search_and_filter(
    query: str,
    pattern: Pattern[str],
    min_occurrences: int,
    config: SearchConfig = SearchConfig(),
) -> List[str]:
    """
    Run a search with `query`, visit candidates, and keep URLs whose page
    matches `pattern` at least `min_occurrences` times. Stops at
    `config.target_count`.
    """
    seen: Set[str] = set()
    qualifying: List[str] = []

    num_results = config.results_per_page
    while len(qualifying) < config.target_count and num_results <= MAX_RESULTS_CAP:
        try:
            candidates = get_candidates(query, num_results=num_results)
        except Exception as err:  # pylint: disable=broad-exception-caught
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
                print(
                    "[+] Found good site "
                    f"({len(qualifying)}/{config.target_count}): {url}"
                )

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
    """Thin wrapper so callers don’t duplicate the call signature."""
    return search_and_filter(
        query=query,
        pattern=pattern,
        min_occurrences=min_occurrences,
        config=config,
    )


def print_results(title: str, urls: List[str]) -> None:
    """Consistent, shared printing."""
    print(f"\nFound {len(urls)} qualifying websites for {title}:\n")
    for url in urls:
        print(url)
