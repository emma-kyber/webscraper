"""
Find Buildium (ManageBuilding) and AppFolio rental listing URLs by state.

- Buildium/ManageBuilding: qualifies pages by counting visible price markers like "$1234".
- AppFolio: qualifies pages by counting visible occurrences of "apply now".
"""

from __future__ import annotations

import re
import argparse
from typing import List, Tuple

from scraper_utils import SearchConfig, run_search, print_results

# Patterns
PRICE_REGEX = re.compile(r"\$\s*\d")  # "$" followed by at least one digit
APPLY_NOW_REGEX = re.compile(r"\bapply\s+now\b", re.IGNORECASE)


def managebuilding_urls(
    state: str,
    target_count: int = 10,
    min_occurrences: int = 21,
    results_per_page: int = 5,
    sleep_sec: float = 5.0,
) -> List[str]:
    """
    Look up ManageBuilding rental listing websites for a given state.
    We try multiple path/case variants to improve hit rate across DDG/Google.
    """
    queries = [
        f'site:managebuilding.com inurl:"Resident/Public/Rentals" "{state}"',
        f'site:managebuilding.com inurl:"resident/public/rentals" "{state}"',
        f'site:managebuilding.com inurl:"public/rentals" "{state}"',
        f'site:managebuilding.com "Resident/Public/Rentals" "{state}"',
        f'site:managebuilding.com "Public/Rentals" "{state}"',
    ]
    config = SearchConfig(
        target_count=target_count,
        results_per_page=results_per_page,
        sleep_sec=sleep_sec,
    )
    qualifying: List[str] = []
    for q in queries:
        if len(qualifying) >= target_count:
            break
        hits = run_search(
            query=q,
            pattern=PRICE_REGEX,
            min_occurrences=min_occurrences,
            config=config,
        )
        for u in hits:
            if u not in qualifying:
                qualifying.append(u)
        # stop early if we've got enough
        if len(qualifying) >= target_count:
            break
    return qualifying[:target_count]


def appfolio_urls(
    state: str,
    target_count: int = 10,
    min_occurrences: int = 20,
    results_per_page: int = 5,
    sleep_sec: float = 5.0,
) -> List[str]:
    """Look up AppFolio rental listing websites for a given state."""
    query = f'site:appfolio.com/listings "{state}"'
    config = SearchConfig(
        target_count=target_count,
        results_per_page=results_per_page,
        sleep_sec=sleep_sec,
    )
    return run_search(
        query=query,
        pattern=APPLY_NOW_REGEX,
        min_occurrences=min_occurrences,
        config=config,
    )


def find_urls_for_state(
    state: str,
    mb_min_prices: int = 21,
    af_min_apply_now: int = 20,
    target_count: int = 10,
    results_per_page: int = 5,
    sleep_sec: float = 5.0,
) -> Tuple[List[str], List[str]]:
    """Return (managebuilding_urls, appfolio_urls) for the given state."""
    mb = managebuilding_urls(
        state,
        target_count=target_count,
        min_occurrences=mb_min_prices,
        results_per_page=results_per_page,
        sleep_sec=sleep_sec,
    )
    af = appfolio_urls(
        state,
        target_count=target_count,
        min_occurrences=af_min_apply_now,
        results_per_page=results_per_page,
        sleep_sec=sleep_sec,
    )
    return mb, af


def main() -> None:
    parser = argparse.ArgumentParser(description="Find Buildium/AppFolio rental listing URLs by state.")
    parser.add_argument("state", nargs="?", help='State name or abbreviation (e.g., "Arizona" or "AZ")')
    parser.add_argument("--target", type=int, default=10, help="Target number of qualifying sites to collect.")
    parser.add_argument("--mb-min", type=int, default=21, help='Min "$1234" occurrences for ManageBuilding.')
    parser.add_argument("--af-min", type=int, default=20, help='Min "apply now" occurrences for AppFolio.')
    parser.add_argument("--per-page", type=int, default=5, help="Search results per page to request.")
    parser.add_argument("--sleep", type=float, default=5.0, help="Base sleep (seconds) between requests.")
    args = parser.parse_args()

    state = args.state or input("Enter state name or abbreviation: ").strip()
    mb_urls, af_urls = find_urls_for_state(
        state,
        mb_min_prices=args.mb_min,
        af_min_apply_now=args.af_min,
        target_count=args.target,
        results_per_page=args.per_page,
        sleep_sec=args.sleep,
    )

    print_results(f"Buildium — {state}", mb_urls)
    print_results(f"AppFolio — {state}", af_urls)


if __name__ == "__main__":
    main()
