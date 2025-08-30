# scrape.py

import os
import json
import pandas as pd
from playwright.sync_api import sync_playwright
from datetime import datetime
import pytz
import gspread
from gspread_pandas import Spread, Client

# --- CONFIGURATION (EDIT THIS) ---
# Paste your Google Sheet ID here
SPREADSHEET_ID = '1MAaeQ7Aw74Xnk-rih9LnwfH_1ULt1TkcXhPW10Jxvnw' 
SHEET_TITLE = 'PSX Data Sheet' # The name of the tab in your sheet
PSX_URL = 'https://dps.psx.com.pk/indices'
KSE100_URL = 'https://www.khistocks.com/market-live/index-live/KSE100.html'

def get_google_sheets_client():
    """Authenticates with Google Sheets using credentials."""
    # This part is for running in GitHub Actions
    creds_json_str = os.getenv('GCP_SA_KEY')
    if creds_json_str:
        creds_dict = json.loads(creds_json_str)
        client = gspread.service_account_from_dict(creds_dict)
        return client
    # This part is for running locally
    else:
        # Assumes your downloaded JSON key file is named 'credentials.json'
        # and is in the same folder as this script.
        client = gspread.service_account(filename='credentials.json')
        return client

def is_market_hours():
    """Checks if the current time is within PSX market hours."""
    pakistan_tz = pytz.timezone("Asia/Karachi")
    now_pkt = datetime.now(pakistan_tz)
    if now_pkt.weekday() >= 5: return False
    current_time_in_minutes = now_pkt.hour * 60 + now_pkt.minute
    market_open, market_close = 9 * 60, 15 * 60 + 30
    return market_open <= current_time_in_minutes <= market_close

def scrape_psx_data():
    """Scrapes the PSX table into a pandas DataFrame."""
    print("Starting browser...")
    with sync_playwright() as p:
        # Launch browser with additional context options
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
            ]
        )
        context = browser.new_context(
            java_script_enabled=True,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36'
        )
        page = context.new_page()
        
        try:
            print(f"Navigating to {PSX_URL}...")
            page.goto(PSX_URL, timeout=120000, wait_until='domcontentloaded')
            
            # Handle cookie consent with multiple selectors
            try:
                consent_selectors = [
                    'button:has-text("Accept All")',
                    'button:has-text("Accept")',
                    'button#cookie-accept'
                ]
                for selector in consent_selectors:
                    if page.locator(selector).count() > 0:
                        page.click(selector, timeout=5000)
                        break
            except:
                pass
            
            print("Setting table view to show 100 entries...")
            # Retry dropdown selection with explicit waits
            page.wait_for_selector('select[name="DataTables_Table_0_length"]', state='attached', timeout=30000)
            dropdown = page.locator('select[name="DataTables_Table_0_length"]')
            dropdown.select_option('100')
            
            # Wait for table to load with more specific checks
            page.wait_for_function(
                """() => {
                    const table = document.querySelector('table#DataTables_Table_0');
                    return table && table.rows.length > 10;
                }""", 
                timeout=60000
            )
            
            # Additional wait for data to populate
            page.wait_for_timeout(2000)  # Allow final JS execution
            
            print("Extracting table data with Pandas...")
            html_content = page.content()
            df_list = pd.read_html(html_content)
            
            psx_df = next((df for df in df_list if 'SYMBOL' in df.columns), None)
            if psx_df is None:
                raise ValueError("Could not find the constituents table on the page.")

            print(f"Successfully extracted {len(psx_df)} rows.")
            return psx_df
            
        finally:
            browser.close()

def scrape_kse100_data():
    """Scrapes KSE100 constituents table from live website."""
    print("Starting KSE100 browser session...")
    KSE100_URL = 'https://www.khistocks.com/market-live/index-live/KSE100.html'
    
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        page = browser.new_page()
        
        try:
            print(f"Navigating to {KSE100_URL}...")
            page.goto(KSE100_URL, timeout=60000, wait_until='networkidle')
            
            # Handle cookie consent
            try:
                page.click('button:has-text("Accept All")', timeout=5000)
            except:
                pass
            
            # Wait for table to populate
            page.wait_for_selector('#tbl_const tr:has(td)', timeout=30000)
            
            # Get updated HTML content
            html_content = page.content()
            
            # Extract and process table
            tables = pd.read_html(html_content, attrs={'id': 'tbl_const'}, flavor='html5lib')
            if not tables:
                raise ValueError("No tables found in KSE100 page")
            
            kse100_df = tables[0].rename(columns={
                'Companies': 'Symbol',
                'Open': 'Open',
                'High': 'High', 
                'Low': 'Low',
                'Close': 'Close',
                'Avg.': 'Average',
                'Volume': 'Volume',
                'Trades': 'Trades',
                'Change / Net': 'Change'
            })
            
            # Clean numeric columns
            numeric_cols = ['Open', 'High', 'Low', 'Close', 'Average', 'Volume', 'Trades']
            kse100_df[numeric_cols] = kse100_df[numeric_cols].replace('[^0-9.]', '', regex=True).astype(float)
            
            print(f"Successfully extracted {len(kse100_df)} live KSE100 constituents")
            return kse100_df
            
        finally:
            browser.close()

def upload_to_gsheet(df, sheet_title=SHEET_TITLE):
    """Uploads a DataFrame to the specified worksheet in Google Sheet."""
    print(f"Connecting to Google Sheets ({sheet_title})...")
    client = get_google_sheets_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    
    try:
        worksheet = spreadsheet.worksheet(sheet_title)
    except gspread.WorksheetNotFound:
        print(f"Creating new worksheet: {sheet_title}")
        worksheet = spreadsheet.add_worksheet(title=sheet_title, rows=1000, cols=20)

    print("Clearing sheet and uploading new data...")
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist())

    timestamp = datetime.now(pytz.timezone("Asia/Karachi")).strftime('%Y-%m-%d %H:%M:%S')
    print(f"{sheet_title} updated successfully at {timestamp} PKT.")

# --- Main execution block ---
if is_market_hours():
    print("Market is open. Starting scrapers...")
    # Scrape and upload PSX data
    psx_data = scrape_psx_data()
    upload_to_gsheet(psx_data, SHEET_TITLE)
    
    # Scrape and upload KSE100 data
    kse100_data = scrape_kse100_data()
    upload_to_gsheet(kse100_data, 'KSE100 Constituents')
else:
    print("Outside market hours, skipping capture.")
