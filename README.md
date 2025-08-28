# Find Buildium & AppFolio Rental Listing URLs

This project finds **active rental listing websites by state** for two major property management systems:

- **Buildium** — pages hosted on `managebuilding.com` are qualified by counting visible price markers like `$1234`.
- **AppFolio** — pages hosted on `appfolio.com` are qualified by counting how many times **"apply now"** appears.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Under the Hood](#under-the-hood)
- [Installation](#installation)
- [Usage](#usage)
- [Example Output](#example-output)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Notes](#notes)
- [Quick Start (One-Liner)](#quick-start-one-liner)

---

## How It Works

1. The script issues search queries for Buildium and AppFolio listing pages.
2. Candidate URLs are fetched and the **visible text** is extracted with BeautifulSoup.
3. Pages qualify when they contain many price markers (`$1234`) for Buildium or the phrase **"apply now"** for AppFolio.
4. Found URLs are returned once the target count is met and printed for easy copy‑paste.

---

## Under the Hood

The project is more than a simple scraper. Key implementation details:

- **Pluggable search backends.** Tries SerpAPI first (if `SERPAPI_KEY` is set), then DuckDuckGo, and finally falls back to Google if `DISABLE_GOOGLE=0`.
- **Transparent caching.** `requests-cache` stores page responses in `scraper_cache.sqlite` for 24 hours to avoid re-fetching the same content.
- **Rate‑limit resilience.** Each request rotates through multiple realistic User‑Agent strings, sleeps with jitter, and retries on transient HTTP errors or 429s.
- **Pattern qualification.** `count_pattern_on_page()` fetches a page and counts regex matches in the visible text, ignoring scripts and styles.
- **Search orchestration.** `search_and_filter()` loops over paginated search results until enough qualifying URLs are collected or a cap is reached.
- **Reusable configuration.** The `SearchConfig` dataclass centralizes throttling and pagination controls used across all helpers.
- **ManageBuilding variants.** `managebuilding_urls()` cycles through multiple path/case query patterns to surface more Buildium listings.
- **CLI wrapper.** `script.py` exposes a command‑line interface that calls `managebuilding_urls()` and `appfolio_urls()` for a given state and prints results.

---

## Installation

1. **Download the project** as a `.zip` or clone the repository.
2. Ensure you have Python 3 installed:
   ```bash
   python3 --version
   ```
3. Install dependencies:
   ```bash
   python3 -m pip install --upgrade pip
   python3 -m pip install -r requirements.txt
   ```

---

## Usage

1. (Recommended) Disable Google scraping to rely on DuckDuckGo:
   ```bash
   export DISABLE_GOOGLE=1
   ```
2. Run the scraper and enter a state name or abbreviation when prompted:
   ```bash
   python3 script.py
   ```

---

## Example Output

```text
[+] Found good site (1/10): https://example1.managebuilding.com/Resident/public/rentals
[+] Found good site (2/10): https://example2.managebuilding.com/Resident/public/rentals

Found 2 qualifying websites for Buildium — Delaware:

https://example1.managebuilding.com/Resident/public/rentals
https://example2.managebuilding.com/Resident/public/rentals


[+] Found good site (1/10): https://example1.appfolio.com/listings
[+] Found good site (2/10): https://example2.appfolio.com/listings

Found 2 qualifying websites for AppFolio — Delaware:

https://example1.appfolio.com/listings
https://example2.appfolio.com/listings
```

---

## Configuration

### CLI Arguments

You can tweak these parameters when running `script.py`:

- `--target` – number of qualifying sites to collect (default: 10).
- `--mb-min` – minimum `$1234` markers for Buildium pages (default: 21).
- `--af-min` – minimum "apply now" phrases for AppFolio pages (default: 20).
- `--per-page` – search results retrieved per batch (default: 5).
- `--sleep` – base delay between requests in seconds (default: 5.0).

### Environment Variables

- `DISABLE_GOOGLE` – set to `0` to enable Google scraping fallback (default: `1`).
- `SERPAPI_KEY` – optional key to use the SerpAPI Google backend.

---

## Troubleshooting

- **“This package has been renamed” warning** – uninstall the old DuckDuckGo library:
  ```bash
  python3 -m pip uninstall -y duckduckgo-search
  ```
- **“No search backend returned results”** – ensure `DISABLE_GOOGLE=1` is set, `ddgs` is installed, try the full state name (e.g., "Texas"), and run again.
- **Slow or rate-limited requests** – increase `--sleep` (e.g., `--sleep 6`) or reduce `--per-page` (e.g., `--per-page 5`).
- **Timeouts** – fetch retries automatically with jitter, but network issues may persist.

---

## Notes

- There is a hard cap of 1000 Google results for safety.
- Some sites may time out or block requests; those are skipped.
- Higher thresholds or many results will slow the script down.
- Use full state names like "Arizona" or "Texas" for best results.
- Buildium detection relies on visible text; CSS/JS is ignored.

---

## Quick Start (One-Liner)

```bash
export DISABLE_GOOGLE=1
python3 script.py
```

