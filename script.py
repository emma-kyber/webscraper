# Before you run this script, open your Terminal and install these two tools:
# pip3 install googlesearch-python requests

# These are the tools ("libraries") we need:
# - googlesearch lets us grab Google search results
# - requests lets us open web pages and look at their contents
# - time lets us pause between steps so we don’t overload websites
from googlesearch import search
import requests
import time


def google_urls(state, target_count=10, min_occurrences=20, results_per_page=10, sleep_sec=1.0):
    """
    This function looks up AppFolio rental listing websites in Google for a given state
    (like "Arizona" or "AR"). It then visits each website and checks how many times
    the phrase "apply now" shows up on the page.

    Why? Because lots of "apply now" buttons usually means it's an active rental site.

    You can control how picky the search is by changing the settings below.

    :param state: The state to search for. Example: "Arizona" or "AZ"
    :param target_count: How many good websites you want it to find before stopping
    :param min_occurrences: The minimum number of "apply now" buttons required
    :param results_per_page: How many new Google results to pull each round
    :param sleep_sec: How many seconds to wait between checks (prevents overload)
    :return: A list of website addresses (URLs) that qualify
    """
    # The actual Google search query we’ll use:
    query = f'site:appfolio.com/listings "{state}"'
    # Pretend to be a real web browser so sites don’t block us
    headers = {"User-Agent": "Mozilla/5.0"}
    # Keep track of websites we’ve already checked
    seen = set()
    # Save the ones that qualify
    qualifying = []

    num_results = results_per_page
    max_results_cap = 1000  # safety cap to avoid infinite searching

    # Keep searching until we have enough good websites
    while len(qualifying) < target_count and num_results <= max_results_cap:
        try:
            # Get a list of possible websites from Google
            candidates = list(search(query, num_results=num_results))
        except Exception as e:
            print(f"Google search failed: {e}")
            break

        # Look at each website one by one
        for url in candidates:
            if len(qualifying) >= target_count:
                break
            if url in seen:
                continue  # skip if we already checked this one
            seen.add(url)

            # Open the website and check for "apply now"
            try:
                resp = requests.get(url, headers=headers, timeout=15)
                text = resp.text.lower()
                if text.count("apply now") >= min_occurrences:
                    qualifying.append(url)
                    print(f"[+] Found good site ({len(qualifying)}/{target_count}): {url}")
            except Exception:
                # If the site is broken or too slow, just skip it
                pass

            # Pause a little between website visits
            time.sleep(sleep_sec)

        # If we still need more, ask Google for more results
        num_results += results_per_page
        time.sleep(sleep_sec)

    return qualifying[:target_count]


# This section actually runs the function when you start the script.
# Change "Delaware" below to whichever state you want.
if __name__ == "__main__":
    state = "Delaware"  # <-- Replace with a state, like "Arizona" or "TX"
    urls = google_urls(state, target_count=10, min_occurrences=20, results_per_page=10)

    print(f"\nFound {len(urls)} qualifying websites for {state}:\n")
    for u in urls:
        print(u)
