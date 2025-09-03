"""Command-line interface for locating Buildium and AppFolio listings."""
from __future__ import annotations

import argparse
import sys

from scraper_utils import (
    appfolio_urls,
    managebuilding_urls,
)

BANNER = """\
Find Buildium & AppFolio Rental Listing URLs
-------------------------------------------
This tool searches the web for listing pages and qualifies them by content.
"""


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    p = argparse.ArgumentParser(description="Find listing portals by state")
    p.add_argument(
        "--state",
        type=str,
        help=(
            'State name or abbreviation (e.g., "Arizona" or "AZ"). '
            "If omitted, you will be prompted."
        ),
    )
    p.add_argument(
        "--target",
        type=int,
        default=10,
        help="How many qualifying sites to collect.",
    )
    p.add_argument(
        "--mb-min",
        type=int,
        default=21,
        help="Min price markers for Buildium.",
    )
    p.add_argument(
        "--af-min",
        type=int,
        default=20,
        help='Min "apply now" matches for AppFolio.',
    )
    p.add_argument(
        "--per-page",
        type=int,
        default=5,
        help="Search results per backend call.",
    )
    p.add_argument(
        "--sleep",
        type=float,
        default=5.0,
        help="Base delay (seconds) between requests.",
    )
    return p.parse_args()


def main() -> int:
    """Run the CLI application."""

    print(BANNER)

    args = parse_args()
    prompt = "Enter a state name or abbreviation (e.g., 'Texas' or 'TX'): "
    state = args.state or input(prompt).strip()
    if not state:
        print("No state provided. Exiting.")
        return 1

    # Run Buildium
    print(f"\n--- Searching Buildium (managebuilding.com) for: {state} ---\n")
    mb = managebuilding_urls(
        state=state,
        target=args.target,
        min_price_markers=args.mb_min,
    )

    if mb:
        print(f"\nFound {len(mb)} qualifying websites for Buildium — {state}:\n")
        for u in mb:
            print(u)
    else:
        print("\nNo qualifying Buildium sites found.\n")

    # Run AppFolio
    print(f"\n--- Searching AppFolio (appfolio.com/listings) for: {state} ---\n")
    af = appfolio_urls(
        state=state,
        target=args.target,
        min_apply_now=args.af_min,
    )

    if af:
        print(f"\nFound {len(af)} qualifying websites for AppFolio — {state}:\n")
        for u in af:
            print(u)
    else:
        print("\nNo qualifying AppFolio sites found.\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
