
# Find Buildium & AppFolio Rental Listing URLs

This project helps you **find active rental listing websites by state** for two major property management systems:

- **Buildium** — qualifies sites by counting visible price markers like `$1234`.
- **AppFolio** — qualifies sites by counting how many times **“apply now”** appears.

---

## Table of Contents

- [How to Use](#how-to-use)  
- [Example Output](#example-output)  
- [Optional Settings](#optional-settings)  
- [Notes](#notes)  
- [Quick Start (One-Liner)](#quick-start-one-liner)  


---

## How to Use

**1. Download the folder**

Get the project folder as a .zip and unzip it anywhere on your computer.
You should see:
```bash
script.py
README.md
requirements.txt
scraper_utils.py
__pycache__
```

**2. Requirements**

   Open your terminal (or command prompt) and navigate to that folder.
   Example:
   ```bash
   cd ~/Desktop/webscraper-main
   ```

   Check if you have Python:
   ```bash
   python3 --version
   ```
   If you see a version number (e.g. Python 3.13.5), you’re good.
  
   If you don’t have Python 3, download and install it here: 
   https://www.python.org/downloads/
   
   
   Then run:
   ```bash
   python3 -m pip install --upgrade pip
   python3 -m pip install -r requirements.txt
   ```
This will install everything listed in requirements.txt:
```text
requests
googlesearch-python
beautifulsoup4
duckduckgo-search
```

**3. Run the scraper**
```bash
python3 script.py
```

You’ll be prompted to enter a state name or abbreviation (e.g. Arizona, CA, Texas).

---

## Example Output

When you run it, you’ll see something like this:

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

This means the script found **2 Buildium** sites and **2 AppFolio** sites in Delaware with active rental listings.

---

## Optional Settings

Inside `script.py`, you can tweak these options when calling `managebuilding_urls()` or `appfolio_urls()`:

* `target_count=10` → How many good websites to find before stopping.
* `min_occurrences=21` (ManageBuilding) → How many price markers (`$1234`) must appear on the page.
* `min_occurrences=20` (AppFolio) → How many **“apply now”** must appear on the page.
* `results_per_page=10` → How many Google results to fetch per batch.
* `sleep_sec=1.0` → How many seconds to pause between requests (helps avoid being blocked).

Most people don’t need to change these — just update the **state** and run.

---

## Notes

* There’s a **hard cap of 1000 Google results** for safety.
* Some sites may time out or be blocked — those are skipped automatically.
* The script takes longer if it checks lots of sites or if you increase thresholds.
* Works best when you use full state names like `"Arizona"` or `"Texas"`.
* Buildium uses **visible text parsing** (ignores JavaScript, styles, etc.), so `$` counts are more reliable.

---

## Quick Start (One-Liner)

If you just want to test it quickly:

```bash
pip3 install googlesearch-python requests beautifulsoup4 && python3 script.py
```
