 PSX & KSE100 Automated Data Scraper

This project is a fully automated, serverless data pipeline that scrapes financial data from the Pakistan Stock Exchange (PSX) and live KSE100 constituents data from KhiStocks. The primary goal of this project was to provide a hands-free, real-time data source for my dad's custom financial analysis models in Excel, eliminating the need for tedious manual data entry.

The script runs on a schedule, fetches the data, cleans it, and uploads it directly to a Google Sheet, making it instantly accessible for analysis.

---
# Key Features

* **Automated Scraping**: Runs on a 15-minute schedule during market hours.
* **Dual Data Sources**: Fetches data from both the official PSX data portal and live data from KhiStocks.
* **Serverless Automation**: Uses GitHub Actions for scheduled, cloud-based execution, requiring no dedicated server.
* **Direct to Spreadsheet**: Uploads the cleaned data directly into designated tabs in a Google Sheet for easy access.
* **Resilient**: Built with Playwright to handle dynamic, JavaScript-heavy websites and user interactions.

---
# Tech Stack

* **Language**: Python
* **Browser Automation**: Playwright
* **Data Manipulation**: Pandas
* **Google Sheets Integration**: gspread & gspread-pandas
* **Automation Platform**: GitHub Actions

---
#  Local Setup and Installation

To run this project on your local machine, follow these steps:

**1. Clone the repository:**
```bash
git clone [https://github.com/your-username/psx_scraper.git](https://github.com/your-username/psx_scraper.git)
cd psx_scraper
````

**2. Create and activate a virtual environment:**

```bash
# For macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# For Windows
python -m venv .venv
.\.venv\Scripts\activate
```

**3. Install Python dependencies:**

```bash
pip install -r requirements.txt
```

**4. Install Playwright browser binaries:**

```bash
python -m playwright install chromium
```

**5. Set up Google Credentials:**

  * Follow the Google Cloud documentation to create a **Service Account** and download its JSON key file.
  * Rename the downloaded file to `credentials.json` and place it in the root of the project folder.
  * Open your Google Sheet and share it with the `client_email` found inside your `credentials.json` file, giving it **Editor** permissions.

**6. Configure the Script:**

  * Open the `scrape.py` file.
  * Find the `SPREADSHEET_ID` variable and replace the placeholder with your actual Google Sheet ID.

**7. Run the script locally:**

```bash
python scrape.py
```

-----

# Automation with GitHub Actions

This repository is configured to run automatically using GitHub Actions. The workflow is defined in `.github/workflows/psx_scraper.yml`.

For the automation to work, you must add your Google Service Account credentials as a secret to your GitHub repository:

1.  Navigate to your repository's `Settings` \> `Secrets and variables` \> `Actions`.
2.  Create a new repository secret named `GCP_SA_KEY`.
3.  Copy the **entire contents** of your `credentials.json` file and paste it as the value for the secret.

The workflow will then run on the schedule defined in the YAML file.

```
```
