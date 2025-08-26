#pip3 install googlesearch-python requests
from googlesearch import search
import requests
import time

def google_urls(state, target_count=10, min_occurrences=20, results_per_page=10, sleep_sec=1.0):
    """
    Find up to `target_count` AppFolio listings URLs that contain "apply now" >= min_occurrences times.
    Will keep requesting more Google results until enough matches are found (or a hard cap is reached).

    :param state: State string used in the Google query (e.g., "Arizona" or "AR")
    :param target_count: Number of qualifying URLs to return
    :param min_occurrences: Minimum count of "apply now" (case-insensitive) required
    :param results_per_page: How many additional results to pull per iteration
    :param sleep_sec: Delay between page fetches to be polite
    :return: List of qualifying URLs (length up to target_count)
    """
    query = f'site:appfolio.com/listings "{state}"'
    headers = {"User-Agent": "Mozilla/5.0"}
    seen = set()
    qualifying = []

    num_results = results_per_page
    max_results_cap = 1000  # hard cap for safety

    while len(qualifying) < target_count and num_results <= max_results_cap:
        try:
            candidates = list(search(query, num_results=num_results))
        except Exception as e:
            print(f"Search error: {e}")
            break

        # Only process new URLs we haven't seen yet
        for url in candidates:
            if len(qualifying) >= target_count:
                break
            if url in seen:
                continue
            seen.add(url)

            # Fetch the page and count "apply now"
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                text = resp.text.lower()
                if text.count("apply now") >= min_occurrences:
                    qualifying.append(url)
                    print(f"[+] Qualified ({len(qualifying)}/{target_count}): {url}")
            except Exception:
                # Skip pages that error or time out
                pass

            time.sleep(sleep_sec)  # be polite between requests

        # Pull more results next loop if we still need more
        num_results += results_per_page
        time.sleep(sleep_sec)

    return qualifying[:target_count]


if __name__ == "__main__":
    state = "Colorado"  # <-- replace with any state text (e.g., "Arizona" or "AR")
    urls = google_urls(state, target_count=10, min_occurrences=20, results_per_page=10)

    print(f"\nFound {len(urls)} qualifying URLs for {state}:\n")
    for u in urls:
        print(u)
