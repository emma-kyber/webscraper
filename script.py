"""
Find ManageBuilding and AppFolio rental listing URLs by state.

- ManageBuilding: qualifies pages by counting visible price markers like "$1234".
- AppFolio: qualifies pages by counting visible occurrences of "apply now".
"""

from __future__ import annotations

import re
from typing import List, Tuple

from scraper_utils import SearchConfig, run_search, print_results

# Patterns
PRICE_REGEX = re.compile(r"\$\s*\d")                         # "$" followed by at least one digit
APPLY_NOW_REGEX = re.compile(r"\bapply\s+now\b", re.IGNORECASE)


def managebuilding_urls(
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


def appfolio_urls(
    state: str,
    target_count: int = 10,
    min_occurrences: int = 20,
    results_per_page: int = 10,
    sleep_sec: float = 1.0,
) -> List[str]:
    """Look up AppFolio rental listing websites in Google for a given state."""
    query = f'site:appfolio.com/listings "{state}"'
    config = SearchConfig(target_count=target_count, results_per_page=results_per_page, sleep_sec=sleep_sec)
    return run_search(query=query, pattern=APPLY_NOW_REGEX, min_occurrences=min_occurrences, config=config)


def find_urls_for_state(
    state: str,
    mb_min_prices: int = 21,
    af_min_apply_now: int = 20,
) -> Tuple[List[str], List[str]]:
    """Return (managebuilding_urls, appfolio_urls) for the given state."""
    mb = managebuilding_urls(state, min_occurrences=mb_min_prices)
    af = appfolio_urls(state, min_occurrences=af_min_apply_now)
    return mb, af


def main() -> None:
    """Run the search for a given state and print both lists."""
    state = "Delaware"  # <-- Change to "Arizona", "TX", etc.
    mb_urls, af_urls = find_urls_for_state(state)

    print_results(f"ManageBuilding — {state}", mb_urls)
    print_results(f"AppFolio — {state}", af_urls)


if __name__ == "__main__":
    main()
