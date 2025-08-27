"""
Find AppFolio rental listing URLs by state based on "apply now" occurrences.
"""

from __future__ import annotations

import re
from typing import List

from scraper_utils import search_and_filter

# Match the phrase "apply now" (case-insensitive) in visible text.
APPLY_NOW_REGEX = re.compile(r"\bapply\s+now\b", flags=re.IGNORECASE)


def google_urls(
    state: str,
    target_count: int = 10,
    min_occurrences: int = 20,
    results_per_page: int = 10,
    sleep_sec: float = 1.0,
) -> List[str]:
    """
    Look up AppFolio rental listing websites in Google for a given state.
    """
    query = f'site:appfolio.com/listings "{state}"'
    return search_and_filter(
        query=query,
        pattern=APPLY_NOW_REGEX,
        min_occurrences=min_occurrences,
        target_count=target_count,
        results_per_page=results_per_page,
        sleep_sec=sleep_sec,
    )


def main() -> None:
    """Run the search for a given state."""
    state = "Delaware"  # <-- Change this to "Arizona", "TX", etc.
    urls = google_urls(state, target_count=10, min_occurrences=20, results_per_page=10)

    print(f"\nFound {len(urls)} qualifying websites for {state}:\n")
    for url in urls:
        print(url)


if __name__ == "__main__":
    main()
