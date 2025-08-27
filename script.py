"""
Find AppFolio rental listing URLs by state.

Searches Google for AppFolio listing pages for a given state and counts
occurrences of "apply now" to guess whether a site is actively leasing.
"""

from __future__ import annotations

import time
from typing import List, Set

import requests
from requests import exceptions
from googlesearch import search


DEFAULT_HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT_SECS = 15.0
MAX_RESULTS_CAP = 1000  # Safety cap to avoid unbounded search growth


def _get_candidates(query: str, num_results: int) -> List[str]:
    """Return up to num_results Google results for the query."""
    return list(search(query, num_results=num_results))


def _site_is_qualifying(
    url: str,
    min_occurrences: int,
    headers: dict[str, str] | None = None,
    timeout: float = TIMEOUT_SECS,
) -> bool:
    """
    Return True if the site contains at least min_occurrences of 'apply now'.
    Any errors retrieving the page return False (skip silently).
    """
    try:
        response = requests.get(url, headers=headers or DEFAULT_HEADERS, timeout=timeout)
        # Optional if you want to skip non-2xx:
        # response.raise_for_status()
        text = response.text.lower()
        return text.count("apply now") >= min_occurrences
    except (
        exceptions.Timeout,
        exceptions.HTTPError,
        exceptions.ConnectionError,
        exceptions.RequestException,
        UnicodeDecodeError,
    ):
        return False


def google_urls(
    state: str,
    target_count: int = 10,
    min_occurrences: int = 20,
    results_per_page: int = 10,
    sleep_sec: float = 1.0,
) -> List[str]:
    """
    Look up AppFolio rental listing websites in Google for a given state.

    Args:
        state: The state to search for. Example: "Arizona" or "AZ".
        target_count: How many good websites to find before stopping.
        min_occurrences: Minimum number of "apply now" occurrences required.
        results_per_page: How many new Google results to pull per round.
        sleep_sec: Seconds to wait between checks (avoid overload).

    Returns:
        List of qualifying website URLs.
    """
    query = f'site:appfolio.com/listings "{state}"'
    seen: Set[str] = set()
    qualifying: List[str] = []

    num_results = results_per_page

    while len(qualifying) < target_count and num_results <= MAX_RESULTS_CAP:
        try:
            candidates = _get_candidates(query, num_results=num_results)
        except Exception as err:  # pylint: disable=broad-except
            print(f"Google search failed: {err}")
            break

        for url in candidates:
            if len(qualifying) >= target_count:
                break
            if url in seen:
                continue
            seen.add(url)

            if _site_is_qualifying(url, min_occurrences=min_occurrences, headers=DEFAULT_HEADERS):
                qualifying.append(url)
                print(f"[+] Found good site ({len(qualifying)}/{target_count}): {url}")

            time.sleep(sleep_sec)

        num_results += results_per_page
        time.sleep(sleep_sec)

    return qualifying[:target_count]


def main() -> None:
    """Run the search for a given state."""
    state = "Delaware"  # <-- Change this to "Arizona", "TX", etc.
    urls = google_urls(state, target_count=10, min_occurrences=20, results_per_page=10)

    print(f"\nFound {len(urls)} qualifying websites for {state}:\n")
    for url in urls:
        print(url)


if __name__ == "__main__":
    main()
