````markdown
# 🏠 Find AppFolio Rental Listing URLs  

This project helps you **find AppFolio rental listing websites by state**.  

It does this by:  
1. Searching Google for AppFolio rental listing pages in a given state.  
2. Visiting each site.  
3. Checking how many times the phrase **“apply now”** appears (more = likely an active rental site).  
4. Printing a list of the good sites.  

---

## 📦 Requirements  

You’ll need:  
- **Python 3** installed on your computer  
  - Check with:  
    ```bash
    python3 --version
    ```  
- Two Python libraries:  
  ```bash
  pip3 install googlesearch-python requests
````

---

## 🚀 How to Use

1. **Download the script**
   Save the code from `find_appfolio.py` into a folder on your computer.

2. **Open the script** in a text editor (Notepad, VS Code, etc.) and look for this line at the bottom:

   ```python
   state = "Delaware"
   ```

   Change `"Delaware"` to the state you want to search (examples: `"Arizona"`, `"CA"`, `"Texas"`).

3. **Open your terminal (or command prompt)** and go to the folder where you saved the script.
   Example (if it’s on your Desktop):

   ```bash
   cd ~/Desktop
   ```

4. **Run the script**:

   ```bash
   python3 find_appfolio.py
   ```

---

## 📋 Example Output

When you run it, you’ll see something like this:

```text
[+] Found good site (1/10): https://example1.appfolio.com/listings
[+] Found good site (2/10): https://example2.appfolio.com/listings

Found 2 qualifying websites for Delaware:

https://example1.appfolio.com/listings
https://example2.appfolio.com/listings
```

This means the script found 2 websites in Delaware with active rental listings.

---

## ⚙️ Optional Settings

If you want to tweak how the script works, you can change these options inside the code:

* `target_count=10` → How many websites you want it to find before stopping.
* `min_occurrences=20` → How many times **“apply now”** must appear on the site for it to count as active.
* `results_per_page=10` → How many Google results to grab at once.
* `sleep_sec=1.0` → How many seconds to pause between checks (helps avoid being blocked).

Most people don’t need to change these — just update the **state** and run.

---

## 📝 Notes

* There’s a **hard cap of 1000 Google results** for safety.
* Some sites may time out or be blocked — those are skipped automatically.
* The script takes a little time if it’s checking lots of sites.
* Works best when you pick full state names like `"Arizona"` or `"Texas"`.

---

## ✅ Quick Start (One-Liner)

If you just want to test it quickly:

```bash
pip3 install googlesearch-python requests && python3 find_appfolio.py
```

---

## 💡 Why This is Useful

Many property managers use AppFolio to manage rental listings.
This script helps you **automatically discover active sites in a state** without manually searching page by page.

---

```

---

Do you also want me to add a **screenshot/GIF walkthrough** section (like “what you’ll see in Terminal”) so non-technical teammates get a visual too?
```
