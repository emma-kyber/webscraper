
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

1. **Download the scripts**  
   Save both `script.py` and `scraper_utils.py` into the same folder on your computer.
   Or, download the zip through github in the code dropdown.

3. **Open `script.py`** in a text editor (Notepad, VS Code, etc.) and look for this line at the bottom:  
   ```python
   state = "Delaware"

4. Change `"Delaware"` to the state you want to search (examples: `"Arizona"`, `"CA"`, `"Texas"`).

5. **Open your terminal (or command prompt)** and navigate to the folder where you saved the files.
   Example (if they’re on your Desktop):

   ```bash
   cd ~/Desktop/(folder_name)
   ```

   If they’re in a subfolder, right-click the folder and choose **Open Terminal** (or **Open in Terminal**).

6. **Requirements:**
   You’ll need:  

- **Python 3** installed on your computer  
  - Check your version with:  
    ```bash
    python3 -m pip install --upgrade pip
    python3 -m pip --version
    ```  

- Three Python libraries:  
    ```bash
    pip3 install googlesearch-python requests beautifulsoup4
    ```  

  Install each line individually in your terminal inside your scraper folder.

7. **Run the script**:

   ```bash
   python3 script.py
   ```

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
