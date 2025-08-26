# pip install googlesearch-python
from googlesearch import search


def google_urls(state, num_pages=5, results_per_page=10):
    """
    Run a Google search for 'site:appfolio.com/listings "STATE"' and return a list of URLs.

    :param state: The state to include in the search (string, e.g. "Arizona")
    :param num_pages: How many pages to scrape (default 5)
    :param results_per_page: Results per page (default 10)
    :return: List of URLs
    """
    query = f'site:appfolio.com/listings "{state}"'
    urls = []
    total_results = num_pages * results_per_page

    for url in search(query, num_results=total_results):
        urls.append(url)

    return urls


if __name__ == "__main__":
    state = "Arizona"  # <-- replace with any state
    urls = google_urls(state, num_pages=5)

    print(f"Found {len(urls)} URLs for {state}:\n")
    for u in urls:
        print(u)
