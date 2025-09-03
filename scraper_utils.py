"""Utility helpers for searching and scraping rental listing pages."""
from __future__ import annotations

import os
import random
import re
import time
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# Optional caching (SQLite in project root)
try:
    import requests_cache as REQUESTS_CACHE  # type: ignore
except ImportError:  # pragma: no cover
    REQUESTS_CACHE = None  # graceful fallback

# --- Optional search backends ---
# 1) DuckDuckGo (preferred)
try:
    from ddgs import DDGS  # type: ignore
except ImportError:  # pragma: no cover
    DDGS = None  # noqa: N816

# 2) Google scraping fallback (fragile; can be disabled)
try:
    from googlesearch import search as GOOGLE_SEARCH  # type: ignore
except ImportError:  # pragma: no cover
    GOOGLE_SEARCH = None

# 3) SerpAPI (paid, if SERPAPI_KEY provided)
try:
    from serpapi import GoogleSearch as SerpApiSearch  # type: ignore
except ImportError:  # pragma: no cover
    SerpApiSearch = None


# =========================
# Configuration + helpers
# =========================

UA_LIST: list[str] = [
    # Shuffle through a few realistic desktop UAs
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

ALLOWED_PATTERNS: list[tuple[str, str]] = [
    # host must end with this, AND path must contain this segment
    ("appfolio.com", "/listings"),
    ("managebuilding.com", "/Resident/public/rentals"),
]

BLOCKED_HOSTS = {
    # Common ad/redirector hosts that appear in search results
    "bing.com",
    "www.bing.com",
    "google.com",
    "www.google.com",
    "www.googleadservices.com",
}
BLOCKED_PATH_BITS = {"aclick", "aclk", "pagead"}


@dataclass
class SearchConfig:
    """Runtime configuration for the search helpers."""

    per_page: int = 5
    base_sleep: float = 5.0
    google_enabled: bool = False  # default off unless DISABLE_GOOGLE=0
    max_results_cap: int = 1000
    serpapi_key: str | None = None


def _sleep_with_jitter(base: float) -> None:
    time.sleep(base + random.uniform(0.15, 0.9))


def _headers() -> dict:
    return {"User-Agent": random.choice(UA_LIST)}


def get_session(use_cache: bool = True) -> requests.Session:
    """
    Return a configured requests (or requests-cache) Session.
    """
    if use_cache and REQUESTS_CACHE is not None:
        # 24h expiration to avoid re-downloading the same pages
        return REQUESTS_CACHE.CachedSession(
            "scraper_cache.sqlite",
            backend="sqlite",
            expire_after=60 * 60 * 24,
        )
    return requests.Session()


# =========================
# URL allow/deny + resolve
# =========================

def is_allowed_url(url: str) -> bool:
    """
    Enforce a simple allowlist (host+path) and blocklist for obvious ad redirects.
    """
    try:
        u = urlparse(url)
    except ValueError:
        return False

    host = (u.netloc or "").lower()
    path = u.path or ""

    if host in BLOCKED_HOSTS:
        return False
    if any(bit in path for bit in BLOCKED_PATH_BITS):
        return False

    return any(host.endswith(allowed_host) and needle in path
               for allowed_host, needle in ALLOWED_PATTERNS)


def normalize_and_check(url: str, session: requests.Session, timeout: int = 20) -> str | None:
    """
    Follow redirects, then re-apply allowlist on the FINAL landing URL.
    Return the final allowed URL or None if it should be skipped.
    """
    if not is_allowed_url(url):
        return None

    try:
        # GET is safer than HEAD for these sites
        resp = session.get(url, headers=_headers(), timeout=timeout, allow_redirects=True)
        final_url = resp.url
    except requests.RequestException:
        return None

    return final_url if is_allowed_url(final_url) else None


# =========================
# Page fetching + scoring
# =========================

def fetch_visible_text(url: str, session: requests.Session, timeout: int = 25) -> str:
    """
    Fetch a page and return the *visible* textual content.
    """
    resp = session.get(url, headers=_headers(), timeout=timeout)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text(separator="\n")
    # Normalize whitespace
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text).strip()
    return text


def count_pattern_on_page(url: str, pattern: re.Pattern[str], session: requests.Session) -> int:
    """
    Count regex pattern occurrences in visible text of the given URL.
    """
    try:
        text = fetch_visible_text(url, session=session)
    except requests.RequestException:
        return 0
    return len(pattern.findall(text))


# =========================
# Search backends
# =========================

def ddg_query(query: str, max_results: int) -> list[str]:
    """
    Search via DuckDuckGo; returns a list of URLs.
    """
    if DDGS is None:
        return []
    out: list[str] = []
    with DDGS() as ddg:
        for r in ddg.text(query, max_results=max_results):
            url = r.get("href") or r.get("url")
            if url:
                out.append(url)
    return out


def google_query(query: str, max_results: int) -> list[str]:
    """
    Search via googlesearch-python; returns a list of URLs.
    """
    if GOOGLE_SEARCH is None:
        return []
    # googlesearch-python returns a generator of URLs
    try:
        return list(GOOGLE_SEARCH(query, num_results=max_results))
    except (requests.RequestException, RuntimeError):
        return []


def serpapi_query(query: str, max_results: int, api_key: str | None) -> list[str]:
    """
    Search via SerpAPI (paid); returns a list of result URLs.
    """
    if SerpApiSearch is None or not api_key:
        return []
    params = {
        "engine": "google",
        "q": query,
        "num": min(100, max_results),
        "api_key": api_key,
    }
    try:
        search = SerpApiSearch(params)
        results = search.get_dict()
        items = results.get("organic_results", []) or []
        urls = [item.get("link") for item in items if item.get("link")]
        return urls[:max_results]
    except (requests.RequestException, RuntimeError):
        return []


def search_candidates(
    query: str,
    cfg: SearchConfig,
) -> list[str]:
    """
    Try multiple backends in order: SerpAPI -> DDG -> Google (if enabled).
    """
    max_results = cfg.per_page
    urls: list[str] = []

    # 1) SerpAPI (if configured)
    if cfg.serpapi_key:
        urls = serpapi_query(query, max_results=max_results, api_key=cfg.serpapi_key)

    # 2) DuckDuckGo
    if not urls:
        urls = ddg_query(query, max_results=max_results)

    # 3) Google scraping fallback (fragile; opt-in only)
    if not urls and cfg.google_enabled:
        urls = google_query(query, max_results=max_results)

    return urls


# =========================
# Orchestrators per PMS
# =========================

def managebuilding_queries_for_state(state: str) -> list[str]:
    """
    Build a few query variants to surface Buildium (managebuilding) listings.
    """
    return [
        f'site:managebuilding.com "Resident/public/rentals" "{state}"',
        f'site:managebuilding.com Resident/public/rentals {state}',
        f'"Resident/public/rentals" {state} managebuilding',
    ]


def appfolio_queries_for_state(state: str) -> list[str]:
    """
    Build a few query variants to surface AppFolio listings.
    """
    return [
        f"site:appfolio.com/listings {state}",
        f'"appfolio.com/listings" "{state}"',
        f'site:appfolio.com inurl:listings "{state}"',
    ]


def search_and_filter(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    queries: Iterable[str],
    target: int,
    min_count: int,
    pattern: re.Pattern[str],
    cfg: SearchConfig,
    session: requests.Session,
    verbose_prefix: str,
) -> list[str]:
    """
    Run queries in order, de-duplicate results, resolve redirects, enforce allowlist,
    then qualify pages by counting a regex pattern in visible text.
    """
    found: list[str] = []
    seen: set[str] = set()

    for q in queries:
        # Fetch a small page of search results
        candidates = search_candidates(q, cfg)
        if not candidates:
            _sleep_with_jitter(cfg.base_sleep)
            continue

        for url in candidates:
            if url in seen:
                continue
            seen.add(url)

            final_url = normalize_and_check(url, session=session)
            if not final_url:
                # Skip ad/redirector or non-allowed
                continue

            # Qualify by pattern count
            n = count_pattern_on_page(final_url, pattern=pattern, session=session)
            if n >= min_count:
                found.append(final_url)
                print(
                    f"[+] {verbose_prefix} found site "
                    f"({len(found)}/{target}): {final_url}"
                )
                if len(found) >= target:
                    return found

            _sleep_with_jitter(cfg.base_sleep)

        # brief pause between query variants
        _sleep_with_jitter(cfg.base_sleep)

    return found


def managebuilding_urls(
    state: str,
    target: int = 10,
    min_price_markers: int = 21,
    cfg: SearchConfig | None = None,
    session: requests.Session | None = None,
) -> list[str]:
    """
    Find Buildium (managebuilding.com) listings by counting visible price markers like $1234.
    """
    cfg = cfg or SearchConfig(
        per_page=5,
        base_sleep=5.0,
        google_enabled=(os.getenv("DISABLE_GOOGLE", "1").strip() == "0"),
        serpapi_key=os.getenv("SERPAPI_KEY") or None,
    )
    session = session or get_session(use_cache=True)

    price_re = re.compile(r"\$\s*\d{3,5}")  # simple $1234 style markers
    queries = managebuilding_queries_for_state(state)
    return search_and_filter(
        queries=queries,
        target=target,
        min_count=min_price_markers,
        pattern=price_re,
        cfg=cfg,
        session=session,
        verbose_prefix="Buildium",
    )


def appfolio_urls(
    state: str,
    target: int = 10,
    min_apply_now: int = 20,
    cfg: SearchConfig | None = None,
    session: requests.Session | None = None,
) -> list[str]:
    """
    Find AppFolio (appfolio.com/listings) pages by counting occurrences of 'apply now'.
    """
    cfg = cfg or SearchConfig(
        per_page=5,
        base_sleep=5.0,
        google_enabled=(os.getenv("DISABLE_GOOGLE", "1").strip() == "0"),
        serpapi_key=os.getenv("SERPAPI_KEY") or None,
    )
    session = session or get_session(use_cache=True)

    apply_re = re.compile(r"\bapply\s+now\b", re.IGNORECASE)
    queries = appfolio_queries_for_state(state)
    return search_and_filter(
        queries=queries,
        target=target,
        min_count=min_apply_now,
        pattern=apply_re,
        cfg=cfg,
        session=session,
        verbose_prefix="AppFolio",
    )
