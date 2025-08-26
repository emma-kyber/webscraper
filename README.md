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
    ```

---

## 🚀 How to Use  

1. **Download the script**  
   Save the code from `find_appfolio.py` into a folder on your computer.  

2. **Open the script**
3. In a text editor (Notepad, VS Code, etc.) and look for this line at the bottom:  
   ```python
   state = "Delaware"
4. Change `"Delaware"` to the state you want to search (examples: `"Arizona"`, `"CA"`, `"Texas"`).

Open your terminal (or command prompt) and go to the folder where you saved the script.  
Example (if it’s on your Desktop):

```bash
cd ~/Desktop

