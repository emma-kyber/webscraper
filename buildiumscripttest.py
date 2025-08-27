"""
Find ManageBuilding rental listing URLs by state based on visible price markers.
"""

from __future__ import annotations

import re
from typing import List

from scraper_utils import SearchConfig, run_search, print_results

# Count a dollar sign followed by at least one digit (visible text only)
PRICE_REGEX = re.compile(r"\$\s*\d")


def google_urls(
    state: str,
    target_count: int = 10,
    min_occurrences: int = 21,
    results_per_page: int = 10,
    sleep_sec: float = 1.0,
) -> List[str]:
    """Look up ManageBuilding rental listing websites in Google for a given state."""
    query = f'site:managebuilding.com inurl:"Resident/Public/Rentals" "{state}"'
    config = SearchConfig(target_count=target_count, results_per_page=results_per_page, sleep_sec=sleep_sec)
    return run_search(query=query, pattern=PRICE_REGEX, min_occurrences=min_occurrences, config=config)


def main() -> None:
    """Run the search for a given state."""
    state = "Delaware"  # <-- Change this to "Arizona", "TX", etc.
    urls = google_urls(state, target_count=10, min_occurrences=21, results_per_page=10)
    print_results(state, urls)


if __name__ == "__main__":
    main()
