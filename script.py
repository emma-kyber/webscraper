"""
Find AppFolio rental listing URLs by state.

This script searches Google for AppFolio rental listing pages in a given state
and checks each site to see how many times "apply now" appears.
"""

import time
import requests
from googlesearch import search


def google_urls(state, target_count=10, min_occurrences=20,
                results_per_page=10, sleep_sec=1.0):
    """
    Look up AppFolio rental listing websites in Google for a given state.

    Args:
        state (str): The state to search for. Example: "Arizona" or "AZ".
        target_count (int): How many good websites to find before stopping.
        min_occurrences (int): Minimum number of "apply now" buttons required.
        results_per_page (int): How many new Google results to pull each round.
        sleep_sec (float): Seconds to wait between checks (avoid overload).

    Returns:
        list[str]: List of qualifying website URLs.
    """
    query = f'site:appfolio.com/listings "{state}"'
    headers = {"User-Agent": "Mozilla/5.0"}
    seen = set()
    qualifying = []

    num_results = results_per_page
    max_results_cap = 1000  # safety cap

    while len(qualifying) < target_count and num_results <= max_results_cap:
        try:
            candidates = list(search(query, num_results=num_results))
        except Exception as err:  # pylint: disable=broad-except
            print(f"Google search failed: {err}")
            break

        for url in candidates:
            if len(qualifying) >= target_count:
                break
            if url in seen:
                continue
            seen.add(url)

            try:
                response = requests.get(url, headers=headers, timeout=15)
                text = response.text.lower()
                if text.count("apply now") >= min_occurrences:
                    qualifying.append(url)
                    print(f"[+] Found good site ({len(qualifying)}/{target_count}): {url}")
            except Exception:  # pylint: disable=broad-except
                pass

            time.sleep(sleep_sec)

        num_results += results_per_page
        time.sleep(sleep_sec)

    return qualifying[:target_count]


def main():
    """Run the search for a given state."""
    state = "Delaware"  # <-- Change this to "Arizona", "TX", etc.
    urls = google_urls(state, target_count=10, min_occurrences=20, results_per_page=10)

    print(f"\nFound {len(urls)} qualifying websites for {state}:\n")
    for url in urls:
        print(url)


if __name__ == "__main__":
    main()
