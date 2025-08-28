# Find Buildium & AppFolio Rental Listing URLs

This project finds **active rental listing websites by state** for two major property management systems:

- **Buildium** — pages hosted on `managebuilding.com` are qualified by counting visible price markers like `$1234`.
- **AppFolio** — pages hosted on `appfolio.com` are qualified by counting how many times **"apply now"** appears.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Installation](#installation)
- [Usage](#usage)
- [Example Output](#example-output)
- [Optional Settings](#optional-settings)
- [Troubleshooting](#troubleshooting)
- [Notes](#notes)
- [Quick Start (One-Liner)](#quick-start-one-liner)

---

## How It Works

1. The script searches the web for Buildium and AppFolio listing pages using DuckDuckGo and, optionally, Google.
2. Each candidate URL is fetched and parsed with BeautifulSoup.
3. Pages are considered **good** when they contain a minimum number of price markers (`$1234`) for Buildium or the phrase **"apply now"** for AppFolio.
4. Results are cached with `requests-cache` to avoid redundant network calls.

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

## Optional Settings

Adjust these arguments in `script.py` when calling `managebuilding_urls()` or `appfolio_urls()`:

- `target_count=10` – stop after finding this many good sites.
- `min_occurrences=21` (Buildium) – minimum `$1234` markers.
- `min_occurrences=20` (AppFolio) – minimum "apply now" phrases.
- `results_per_page=10` – number of search results fetched per batch.
- `sleep_sec=1.0` – pause between requests to avoid rate limits.

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

