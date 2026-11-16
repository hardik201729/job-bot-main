#!/usr/bin/env python3
# ========================================
# HARDIK'S JOB APPLICATION BOT - v4.4 FINAL
# UPDATED: Added 2-stage follow-ups for HR and Referral contacts
# ========================================

"""
KEY UPDATES IN v4.4:
1. ADDED 2-stage follow-up system for HR contacts (Follow-up 1 after 3 days, Follow-up 2 after 5 more days)
2. ADDED 2-stage follow-up system for Referral contacts (Follow-up 1 after 3 days, Follow-up 2 after 5 more days)
3. ADDED new email templates for Follow-up 2 (HR) and Follow-ups 1 & 2 (Referral)
4. ADDED safe column addition to preserve existing data when adding new columns
5. UPDATED Contacts sheet: Added "Followup2 Date" column at end
6. UPDATED Referral Contacts sheet: Added "Email Date", "Followup1 Date", "Followup2 Date", "Response Date" columns at end
7. ADDED check_and_send_referral_followups() function
8. ADDED send_referral_followup_email() function

PREVIOUS UPDATES (v4.3):
- HARDCODED match score to 83% in emails (for impact)
- REMOVED LinkedIn connection requests - now logs to "LinkedIn Contacts" sheet
- ADDED "LinkedIn Contacts" sheet with Status=0 for separate LinkedIn bot
- Email bot and LinkedIn bot are now SEPARATE workflows
"""

import logging
from datetime import datetime, timedelta
import time
import os
import pickle
import random
import hashlib
import re
import json

# Base directory for resolving relative paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ========================================
# SETUP LOGGING
# ========================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

print("=" * 70)
print(">>> HARDIK'S JOB APPLICATION BOT v4.4 FINAL")
print("=" * 70)
print("\n[OK] Full workflow: Scrape -> Match -> Find HRs -> Send Emails -> Follow-ups")
print("[INFO] LinkedIn contacts logged to sheet for separate LinkedIn bot")
print("[INFO] 2-stage follow-ups enabled for HR and Referral contacts")
print("[INFO] Jobs: LinkedIn (logged-in Chrome, falls back to public feed) + Wellfound + job-alert emails\n")

# ========================================
# IMPORT CONFIGURATION
# ========================================

from config import (
    LINKEDIN_EMAIL, LINKEDIN_PASSWORD,
    YOUR_EMAIL, GMAIL_APP_PASSWORD,
    APOLLO_API_KEY,
    YOUR_NAME, YOUR_PHONE, YOUR_LINKEDIN,
    RESUME_DRIVE_FILE_ID, RESUME_FILENAME,
    FULLSTACK_RESUME_DRIVE_FILE_ID, FULLSTACK_RESUME_FILENAME,
    FULLSTACK_KEYWORDS,
    MY_SKILLS, TITLE_ALIASES,
    SENIOR_KEYWORDS, JUNIOR_KEYWORDS, MY_EXPERIENCE_YEARS,
    JOB_ROLES, LOCAL_LOCATIONS, REMOTE_LOCATION, REMOTE_LOCATIONS, JOB_TIME_FILTER,
    APOLLO_LOCATION_MAP, APOLLO_DEFAULT_LOCATION,
    BLACKLIST_COMPANIES, BLACKLIST_PATTERNS,
    TOP_JOBS_TO_APPLY, MIN_MATCH_SCORE,
    EMAILS_PER_COMPANY, LINKEDIN_REQUESTS_PER_COMPANY, MAX_LINKEDIN_REQUESTS_PER_DAY,
    HR_FOLLOWUP1_DAYS, HR_FOLLOWUP2_DAYS,
    REFERRAL_FOLLOWUP1_DAYS, REFERRAL_FOLLOWUP2_DAYS,
    FOLLOWUP_DAYS,
    MIN_DELAY, MAX_DELAY, AUTO_RELOGIN_TIMEOUT,
    HR_TITLES,
    REFERRALS_PER_COMPANY, REFERRAL_ROLES_BASE, REFERRAL_SENIORITY_ORDER,
    MAX_APOLLO_CREDITS_PER_RUN, TARGET_TITLE_KEYWORDS, EXCLUDE_TITLE_KEYWORDS,
    MAX_EXPERIENCE_TIER1, MAX_EXPERIENCE_TIER2,
    ALLOWED_PM_PREFIXES,
    USE_SELENIUM_SCRAPER, LINKEDIN_GEO_IDS,
    WELLFOUND_ENABLED, WELLFOUND_ROLES, WELLFOUND_LOCATIONS, WELLFOUND_INCLUDE_REMOTE,
    JOB_ALERT_EMAILS_ENABLED, JOB_ALERT_LOOKBACK_DAYS,
    SHEETS_NAME,
)

logger.info("Configuration loaded")
logger.info(f"   Total job roles: {len(JOB_ROLES)}")
logger.info(f"   Target jobs to apply: {TOP_JOBS_TO_APPLY}")
logger.info(f"   Min match score: {MIN_MATCH_SCORE}%")

# ========================================
# IMPORT LIBRARIES
# ========================================

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import *
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher
import smtplib
import imaplib
import email as email_lib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from mail_threads import MailGuard, apply_thread_headers
import requests
import PyPDF2
import threading

logger.info("[OK] Libraries imported")

# ========================================
# ORGANIZATION CACHE (OPTIMIZATION 1)
# ========================================

# Global cache for organization domains (reduces API calls)
ORGANIZATION_CACHE = {}

# ========================================
# GOOGLE AUTHENTICATION
# ========================================

logger.info(">> Setting up local database (data/jobbot.db)...")

# Google Sheets replaced by a local SQLite store with the same API.
# View everything with:  venv/bin/python dashboard.py
from local_store import open_spreadsheet

spreadsheet = open_spreadsheet()
logger.info("[OK] Local database ready")


def setup_sheet(sheet_name, headers):
    """Create or setup a worksheet with headers - PRESERVES EXISTING DATA"""
    try:
        sheet = spreadsheet.worksheet(sheet_name)
        existing_headers = sheet.row_values(1)

        # If headers match exactly, nothing to do
        if existing_headers == headers:
            logger.info(f"   [OK] {sheet_name} (headers OK)")
            return sheet

        # Check if new headers are a superset (existing headers are prefix of new headers)
        # This means we're just adding columns at the end
        if headers[:len(existing_headers)] == existing_headers:
            # Just need to add new column headers
            new_columns = headers[len(existing_headers):]
            if new_columns:
                logger.info(f"   [+] Adding {len(new_columns)} new column(s) to {sheet_name}: {new_columns}")
                # Add new headers at the end of row 1
                for i, col_name in enumerate(new_columns):
                    col_index = len(existing_headers) + i + 1
                    sheet.update_cell(1, col_index, col_name)
            logger.info(f"   [OK] {sheet_name} (columns added safely)")
            return sheet

        # If existing headers are a superset of new headers, keep as-is
        if existing_headers[:len(headers)] == headers:
            logger.info(f"   [OK] {sheet_name} (extra columns kept)")
            return sheet

        # Headers are completely different - this is a new sheet or major change
        # Only clear if sheet is empty (just has headers) to be safe
        all_values = sheet.get_all_values()
        if len(all_values) <= 1:
            sheet.clear()
            sheet.append_row(headers)
            logger.info(f"   [OK] Setup {sheet_name} (empty sheet reset)")
        else:
            # Sheet has data but headers don't match - log warning but don't clear
            logger.warning(
                f"   [!] {sheet_name}: Headers mismatch but has {len(all_values) - 1} rows of data - NOT clearing")
            logger.warning(f"       Expected: {headers}")
            logger.warning(f"       Found: {existing_headers}")
        return sheet
    except:
        sheet = spreadsheet.add_worksheet(title=sheet_name, rows=1000, cols=len(headers))
        sheet.append_row(headers)
        logger.info(f"   [OK] Created {sheet_name}")
        return sheet


def ensure_columns_exist(sheet, expected_headers):
    """
    Safely add missing columns to the END of an existing sheet.
    This preserves all existing data.
    """
    try:
        existing_headers = sheet.row_values(1)

        if existing_headers == expected_headers:
            return False  # No changes needed

        # Check if we just need to add columns at the end
        if expected_headers[:len(existing_headers)] == existing_headers:
            new_columns = expected_headers[len(existing_headers):]
            if new_columns:
                logger.info(f"   [+] Adding columns: {new_columns}")
                for i, col_name in enumerate(new_columns):
                    col_index = len(existing_headers) + i + 1
                    sheet.update_cell(1, col_index, col_name)
                return True

        return False
    except Exception as e:
        logger.error(f"   [!] Error ensuring columns: {e}")
        return False


# NEW: Sheet for jobs BEFORE deduplication (for debugging)
jobs_before_dedup_sheet = setup_sheet("Jobs (Before Dedup)", [
    "Date", "Job ID", "Search Name", "Title", "Company", "Location",
    "Job Type", "URL"
])

jobs_sheet = setup_sheet("Jobs (After Dedup)", [
    "Date", "Job ID", "Search Name", "Title", "Company", "Location",
    "Job Type", "URL", "Match Score", "Applied", "Apply Date"
])

# UPDATED: Separate LinkedIn and Email status columns
applications_sheet = setup_sheet("Applications", [
    "Timestamp", "Date", "Job ID", "Title", "Company", "Location", "Job Type",
    "URL", "Match Score", "Search Name", "Recruiter 1", "Email 1", "LinkedIn 1",
    "Recruiter 2", "Email 2", "Recruiter 3", "Email 3", "Hiring Team",
    "Hiring Email", "LinkedIn Status", "Email Status", "Email Date", "LinkedIn Date",
    "Followup Date", "Response", "Response Date", "Notes"
])

# UPDATED v4.4: Added Followup2 Date column at end
contacts_sheet = setup_sheet("Contacts", [
    "Date", "Name", "Title", "Email", "LinkedIn", "Location",
    "Source", "Company", "Job", "LinkedIn Status", "Email Status",
    "Email Date", "Followup Date", "Response", "Response Date", "Followup2 Date"
])

# NEW: LinkedIn Contacts sheet for separate LinkedIn connection bot
linkedin_contacts_sheet = setup_sheet("LinkedIn Contacts", [
    "Date", "Name", "Title", "LinkedIn", "Company", "JobTitle",
    "Location", "Status", "Notes"
])

# REFERRAL TRACKING SHEETS
referral_applications_sheet = setup_sheet("Referral Applications", [
    "Timestamp", "Date", "Job ID", "Title", "Company", "Location", "Job Type",
    "URL", "Match Score", "Search Name", "Contact 1", "Email 1", "LinkedIn 1",
    "Contact 2", "Email 2", "Contact 3", "Email 3", "Contact 4", "Email 4",
    "Contact 5", "Email 5", "Emails Sent", "LinkedIn Logged", "Notes"
])

# UPDATED v4.4: Added Email Date, Followup1 Date, Followup2 Date, Response Date columns at end
referral_contacts_sheet = setup_sheet("Referral Contacts", [
    "Date", "Name", "Title", "Role", "Email", "LinkedIn", "Location",
    "Source", "Company", "Job", "LinkedIn Status", "Email Status", "Response",
    "Email Date", "Followup1 Date", "Followup2 Date", "Response Date"
])

linkedin_referral_contacts_sheet = setup_sheet("LinkedIn Referral Contacts", [
    "Date", "Name", "Title", "Role", "LinkedIn", "Company", "Job Title",
    "Location", "Status", "Notes"
])

# UPDATED v4.4: Added HR Followups and Referral Followups columns
daily_sheet = setup_sheet("Daily Stats", [
    "Date", "Jobs Scraped", "Duplicates", "Blacklisted", "New Jobs",
    "Jobs Matched", "Top Score", "Avg Score", "LinkedIn Logged",
    "Emails Sent", "Referral Emails Sent", "Referral LinkedIn Logged",
    "HR Followups", "Referral Followups", "Errors"
])

error_log_sheet = setup_sheet("Error Log", [
    "Timestamp", "Type", "Function", "Details", "Job/Company"
])

# OPTIMIZATION 1: Organization Cache sheet
organization_cache_sheet = setup_sheet("Organization Cache", [
    "Company Name", "Domain", "Last Updated", "Status"
])

# Every Apollo credit the bot spends (shown on the dashboard)
apollo_credits_sheet = setup_sheet("Apollo Credits", [
    "Timestamp", "Date", "Run ID", "Type", "Company", "Person", "Credits"
])

RUN_ID = datetime.now().strftime('%Y%m%d-%H%M%S')
APOLLO_CREDITS_USED = 0


def apollo_credits_left():
    return MAX_APOLLO_CREDITS_PER_RUN - APOLLO_CREDITS_USED


def record_apollo_credit(kind, company="", person=""):
    """Count and log one Apollo credit."""
    global APOLLO_CREDITS_USED
    APOLLO_CREDITS_USED += 1
    now = datetime.now()
    try:
        apollo_credits_sheet.append_row([now.strftime('%Y-%m-%d %H:%M:%S'), now.strftime('%Y-%m-%d'),
                                         RUN_ID, kind, company, person, 1])
    except Exception as e:
        logger.debug(f"credit log error: {e}")
    logger.info(f"         [CREDITS] {APOLLO_CREDITS_USED}/{MAX_APOLLO_CREDITS_PER_RUN} used this run ({kind})")

logger.info("[OK] All sheets setup complete")

# ========================================
# EXTRACT RESUME TEXT
# ========================================

logger.info("[INFO] Downloading resumes...")

def _load_resume(drive_id, filename):
    """Use the local PDF in resumes/ if present; otherwise download it from Google Drive."""
    path = os.path.join(BASE_DIR, 'resumes', filename)
    if not os.path.exists(path):
        if not drive_id:
            raise FileNotFoundError(f"{path} not found and no Drive file ID set")
        response = requests.get(f'https://drive.google.com/uc?export=download&id={drive_id}')
        response.raise_for_status()
        if not response.content.startswith(b'%PDF'):
            raise ValueError("Drive download is not a PDF (check sharing settings / file ID)")
        with open(path, 'wb') as f:
            f.write(response.content)
    pdf = PyPDF2.PdfReader(path)
    return "".join((page.extract_text() or "") for page in pdf.pages)

try:
    RESUME_TEXT = _load_resume(RESUME_DRIVE_FILE_ID, RESUME_FILENAME)
    logger.info(f"[OK] Resume text extracted ({len(RESUME_TEXT)} chars)")
except Exception as e:
    logger.error(f"[X] Resume error: {e}")
    RESUME_TEXT = ""

if FULLSTACK_RESUME_FILENAME == RESUME_FILENAME:
    FULLSTACK_RESUME_TEXT = RESUME_TEXT
else:
    try:
        FULLSTACK_RESUME_TEXT = _load_resume(FULLSTACK_RESUME_DRIVE_FILE_ID, FULLSTACK_RESUME_FILENAME)
        logger.info(f"[OK] Secondary resume loaded ({len(FULLSTACK_RESUME_TEXT)} chars)")
    except Exception as e:
        logger.error(f"[X] Secondary resume error: {e}")
        FULLSTACK_RESUME_TEXT = RESUME_TEXT

# ========================================
# IMPORT EMAIL TEMPLATES
# ========================================

from email_templates import (
    EMAIL_TEMPLATE_HTML, EMAIL_TEMPLATE_PLAIN,
    FOLLOWUP_EMAIL_HTML, LINKEDIN_MESSAGE,
    REFERRAL_EMAIL_HTML, REFERRAL_EMAIL_PLAIN,
    HR_FOLLOWUP2_EMAIL_HTML,
    REFERRAL_FOLLOWUP1_EMAIL_HTML, REFERRAL_FOLLOWUP2_EMAIL_HTML,
    FULLSTACK_EMAIL_TEMPLATE_HTML, FULLSTACK_EMAIL_TEMPLATE_PLAIN,
    FULLSTACK_FOLLOWUP_EMAIL_HTML, FULLSTACK_FOLLOWUP2_EMAIL_HTML,
    FULLSTACK_REFERRAL_EMAIL_HTML, FULLSTACK_REFERRAL_EMAIL_PLAIN,
    FULLSTACK_LINKEDIN_MESSAGE,
)

logger.info("[OK] Email templates loaded")


# ========================================
# HELPER FUNCTIONS
# ========================================

def is_blacklisted_company(company_name):
    """Check if company is in blacklist"""
    if not company_name:
        return False

    company_lower = company_name.lower().strip()

    for blacklisted in BLACKLIST_COMPANIES:
        if company_lower == blacklisted.lower().strip():
            return True

    for pattern in BLACKLIST_PATTERNS:
        if pattern.lower() in company_lower:
            return True

    return False


def is_fullstack_job(job_title):
    """
    Check if job title indicates a full stack role.
    Returns True if any fullstack keyword is found in the title.
    """
    if not job_title:
        return False
    
    title_lower = job_title.lower().strip()
    
    for keyword in FULLSTACK_KEYWORDS:
        if keyword in title_lower:
            return True
    
    return False


def get_resume_for_job(job_title):
    """
    Get the appropriate resume filename based on job title.
    Returns (filename, resume_type) tuple.
    """
    if is_fullstack_job(job_title):
        return FULLSTACK_RESUME_FILENAME, "fullstack"
    return RESUME_FILENAME, "frontend"


def generate_job_id(title, company, url=""):
    """Generate unique job ID using SHA256 hash"""
    try:
        s = f"{title}_{company}_{url}".lower().replace(' ', '_')
        return hashlib.sha256(s.encode()).hexdigest()[:16]
    except Exception as e:
        logger.error(f"Error generating job ID: {e}")
        import time
        s = f"{title}_{company}_{time.time()}"
        return hashlib.sha256(s.encode()).hexdigest()[:16]


def extract_job_id_from_url(url):
    """
    Extract LinkedIn job ID from URL.
    Handles both formats:
    1. /jobs/view/1234567890 (direct job URL)
    2. ?currentJobId=1234567890 (search URL with job ID param)
    """
    try:
        url_str = str(url)
        # Pattern 1: /jobs/view/1234567890
        match = re.search(r'jobs/view/(\d+)', url_str)
        if match:
            return match.group(1)
        # Pattern 2: ?currentJobId=1234567890 or &currentJobId=1234567890
        match = re.search(r'[?&]currentJobId=(\d+)', url_str)
        if match:
            return match.group(1)
        return "N/A"
    except:
        return "N/A"


def extract_location_for_apollo(job_location, job_type):
    """Determine best location to search for HRs in Apollo"""
    try:
        if job_type and 'remote' in job_type.lower():
            return APOLLO_DEFAULT_LOCATION

        for key, value in APOLLO_LOCATION_MAP.items():
            if key in job_location:
                return value

        return APOLLO_DEFAULT_LOCATION
    except:
        return APOLLO_DEFAULT_LOCATION


def log_to_sheet(sheet, data):
    """Add row to Google Sheet with retry logic"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            sheet.append_row(data)
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            else:
                logger.error(f"Error logging to sheet after {max_retries} attempts: {e}")
                return False


def log_to_sheet_batch(sheet, data_rows):
    """
    Add multiple rows to Google Sheet in a single API call with retry logic
    Args:
        sheet: gspread worksheet object
        data_rows: list of lists, where each inner list is a row
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if len(data_rows) > 0:
                sheet.append_rows(data_rows, value_input_option='RAW')
                return True
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Batch write attempt {attempt + 1} failed, retrying in 3s...")
                time.sleep(3)
                continue
            else:
                logger.error(f"Error batch logging to sheet after {max_retries} attempts: {e}")
                return False


def log_error(error_type, function_name, details, job_company=""):
    """Log error to Error Log sheet"""
    try:
        log_to_sheet(error_log_sheet, [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            error_type,
            function_name,
            str(details),
            job_company
        ])
    except:
        pass


def random_delay(min_sec=MIN_DELAY, max_sec=MAX_DELAY):
    """Random delay to avoid rate limits"""
    delay = random.randint(min_sec, max_sec)
    logger.info(f"      [WAIT] Waiting {delay}s...")
    time.sleep(delay)


# IMPROVED: More precise contact checking
def check_contacted(email, company=""):
    """
    Check if we've already contacted this email for this company
    Returns: (already_contacted: bool, status: str)
    """
    try:
        # Search for exact email match
        all_values = contacts_sheet.get_all_values()

        # Skip header row
        for row in all_values[1:]:
            if len(row) >= 8:  # Make sure row has enough columns
                row_email = row[3].strip().lower() if len(row) > 3 else ""
                row_company = row[7].strip().lower() if len(row) > 7 else ""

                # Check if email matches
                if row_email == email.strip().lower():
                    # If company provided, check if same company
                    if company:
                        if row_company == company.strip().lower():
                            return True, "Previously contacted for this company"
                    else:
                        return True, "Previously contacted"

        return False, "New contact"
    except Exception as e:
        logger.debug(f"Error checking contact: {e}")
        return False, "Check failed"


# ========================================
# BROWSER SETUP
# ========================================

def create_driver():
    """Create Chrome WebDriver with optimized settings"""
    options = Options()
    # Always use Google Chrome (not Brave or another Chromium browser)
    chrome_app = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    if os.path.exists(chrome_app):
        options.binary_location = chrome_app
    # Separate Chrome profile for the bot so the LinkedIn login is remembered between runs
    options.add_argument(f"--user-data-dir={os.path.join(BASE_DIR, 'data', 'chrome-profile')}")
    options.add_argument('--start-maximized')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # Don't wait for LinkedIn's never-ending background requests
    options.page_load_strategy = 'eager'

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.set_page_load_timeout(45)
    return driver


def safe_find(driver, by, value, timeout=10):
    """Safe element finder with timeout"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except:
        return None


def wait_for_user_confirmation(timeout_seconds):
    """Wait for user to manually handle LinkedIn verification"""
    logger.info(f"[SETUP] Waiting up to {timeout_seconds // 60} minutes for verification...")
    logger.info("   Press ENTER in this terminal once you've completed verification")

    user_input = []

    def get_input():
        user_input.append(input())

    input_thread = threading.Thread(target=get_input, daemon=True)
    input_thread.start()
    input_thread.join(timeout=timeout_seconds)

    if user_input:
        logger.info("[OK] User confirmed - continuing...")
        return True
    else:
        logger.warning("[SETUP] Timeout reached without user confirmation")
        return False


# ========================================
# LINKEDIN LOGIN
# ========================================

def _linkedin_logged_in(driver):
    url = driver.current_url
    return ('linkedin.com' in url and not any(k in url for k in ('/login', '/checkpoint', '/challenge', '/uas/', '/authwall', '/signup'))
            and any(k in url for k in ('/feed', '/jobs', '/in/', '/mynetwork', '/messaging', '/notifications')))


def _find_first(driver, selectors, timeout=4):
    for by, value in selectors:
        el = safe_find(driver, by, value, timeout=timeout)
        if el:
            return el
    return None


def _manual_login(driver):
    """Let the user sign in by hand in the open Chrome window."""
    logger.warning("[!] Please sign in to LinkedIn yourself in the Chrome window that opened.")
    logger.info("   Then come back to this terminal and press ENTER.")
    if not wait_for_user_confirmation(AUTO_RELOGIN_TIMEOUT):
        return False
    if not _linkedin_logged_in(driver):
        try:
            driver.get("https://www.linkedin.com/feed/")
        except TimeoutException:
            pass
        time.sleep(4)
    if _linkedin_logged_in(driver):
        logger.info("[OK] Login successful (manual)")
        return True
    logger.error(f"[X] Still not logged in (page: {driver.current_url})")
    return False


def linkedin_login_with_retry(driver, max_attempts=3):
    """Login to LinkedIn: reuse saved session, else auto-fill, else manual sign-in."""
    # Saved session (Chrome profile in data/chrome-profile keeps you signed in between runs)
    try:
        driver.get("https://www.linkedin.com/feed/")
        time.sleep(4)
        if _linkedin_logged_in(driver):
            logger.info("[OK] Already logged in (saved session)")
            return True
    except Exception as e:
        logger.debug(f"Session check failed: {e}")

    for attempt in range(max_attempts):
        try:
            logger.info(f"   >> Login attempt {attempt + 1}/{max_attempts}...")
            driver.get("https://www.linkedin.com/login")
            time.sleep(3)

            if _linkedin_logged_in(driver):
                logger.info("[OK] Already logged in")
                return True

            username = _find_first(driver, [
                (By.ID, 'username'), (By.NAME, 'session_key'),
                (By.CSS_SELECTOR, 'input[autocomplete="username"]'), (By.CSS_SELECTOR, 'input[type="email"]')])
            password = _find_first(driver, [
                (By.ID, 'password'), (By.NAME, 'session_password'),
                (By.CSS_SELECTOR, 'input[type="password"]')])

            if not (username and password):
                logger.warning(f"[!] Login form not recognised (page: {driver.current_url})")
                return _manual_login(driver)

            username.clear()
            username.send_keys(LINKEDIN_EMAIL)
            password.clear()
            password.send_keys(LINKEDIN_PASSWORD)
            password.send_keys(Keys.RETURN)
            time.sleep(6)

            if _linkedin_logged_in(driver):
                logger.info("[OK] Login successful")
                return True

            if any(k in driver.current_url for k in ('checkpoint', 'challenge')):
                logger.warning("[!] LinkedIn verification required (code / captcha).")
                logger.info("   Complete it in the Chrome window, then press ENTER here.")
                if wait_for_user_confirmation(AUTO_RELOGIN_TIMEOUT):
                    driver.get("https://www.linkedin.com/feed/")
                    time.sleep(4)
                    if _linkedin_logged_in(driver):
                        logger.info("[OK] Login successful after verification")
                        return True
                return _manual_login(driver)

            logger.warning(f"[!] Login attempt {attempt + 1} failed (page: {driver.current_url})")

        except Exception as e:
            logger.error(f"[X] Login error on attempt {attempt + 1}: {e}")

        if attempt < max_attempts - 1:
            time.sleep(5)

    return _manual_login(driver)


# ========================================
# ENHANCED JOB SCRAPER
# ========================================

def wait_for_url_change(driver, old_url, timeout=8):
    """
    Wait for URL to change after clicking a job card
    Returns True if URL changed, False if timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        current_url = driver.current_url
        if current_url != old_url:
            return True
        time.sleep(0.5)
    return False


def get_job_cards(driver):
    """Get job cards using multiple selectors"""
    try:
        selectors = [
            'li[data-occludable-job-id]',
            'li.ember-view.occludable-update',
            '.jobs-search-results-list li',
            'li.jobs-search-results__list-item',
        ]

        for selector in selectors:
            cards = driver.find_elements(By.CSS_SELECTOR, selector)
            if len(cards) > 0:
                logger.info(f"   [OK]Ã…[OK] Found {len(cards)} job cards")
                return cards

        logger.warning("   [!] No job cards found")
        return []

    except Exception as e:
        logger.error(f"   [X]¢â‚¬â„¢ Error finding cards: {e}")
        return []


def extract_text_from_element(driver, selectors):
    """Extract text from element using multiple selectors"""
    for selector in selectors:
        try:
            elem = driver.find_element(By.CSS_SELECTOR, selector)
            if elem:
                text = elem.text.strip()
                if not text:
                    html = elem.get_attribute('innerHTML')
                    matches = re.findall(r'<!---->(.*?)<!---->', html)
                    if matches:
                        text = matches[0].strip()

                if text:
                    return text
        except:
            continue
    return None


def extract_job_details_enhanced(driver):
    """Extract job details with comprehensive selectors"""
    details = {
        'title': None,
        'company': None,
        'location': 'N/A',
        'job_type': 'N/A'
    }

    time.sleep(4)

    # TITLE
    title_selectors = [
        '.job-details-jobs-unified-top-card__job-title a',
        '.job-details-jobs-unified-top-card__job-title h1',
        'h1.job-details-jobs-unified-top-card__job-title a',
        'h1.t-24.t-bold a',
        '.job-details-jobs-unified-top-card__job-title',
        'h1.job-details-jobs-unified-top-card__job-title',
        '.t-24.job-details-jobs-unified-top-card__job-title',
        '.t-24.t-bold.inline a',
        'a[data-control-name="job_card_title_link"]',
        '.jobs-unified-top-card__job-title',
        '.jobs-unified-top-card__job-title a',
    ]

    details['title'] = extract_text_from_element(driver, title_selectors)

    # COMPANY
    company_selectors = [
        '.job-details-jobs-unified-top-card__company-name a',
        'div.job-details-jobs-unified-top-card__company-name a',
        '.job-details-jobs-unified-top-card__company-name',
        'div.job-details-jobs-unified-top-card__company-name',
        'a.job-details-jobs-unified-top-card__company-name',
        '.jobs-unified-top-card__company-name a',
        '.jobs-unified-top-card__company-name',
        'span.jobs-unified-top-card__company-name',
        'a.app-aware-link[data-test-app-aware-link]',
    ]

    details['company'] = extract_text_from_element(driver, company_selectors)

    # LOCATION
    location_selectors = [
        '.job-details-jobs-unified-top-card__tertiary-description-container span.tvm__text',
        '.job-details-jobs-unified-top-card__primary-description',
        '.job-details-jobs-unified-top-card__bullet',
        '.jobs-unified-top-card__bullet',
        '.jobs-unified-top-card__primary-description',
        '.job-details-jobs-unified-top-card__primary-description-container',
    ]

    for selector in location_selectors:
        try:
            loc_elem = driver.find_element(By.CSS_SELECTOR, selector)
            if loc_elem:
                location_text = loc_elem.text.strip()

                if not location_text:
                    html = loc_elem.get_attribute('innerHTML')
                    matches = re.findall(r'<!---->(.*?)<!---->', html)
                    if matches and len(matches) > 0:
                        location_text = matches[0].strip()

                if location_text:
                    separators = ['.', '*', '\n', ' ']
                    for sep in separators:
                        if sep in location_text:
                            parts = location_text.split(sep)
                            if parts[0].strip():
                                details['location'] = parts[0].strip()
                                break

                    if details['location'] == 'N/A':
                        lines = location_text.split('\n')
                        if lines[0].strip():
                            details['location'] = lines[0].strip()

                    if details['location'] != 'N/A':
                        break
        except:
            continue

    # JOB TYPE
    job_type_selectors = [
        '.job-details-jobs-unified-top-card__workplace-type',
        '.jobs-unified-top-card__workplace-type',
        '.job-details-jobs-unified-top-card__job-insight',
        '.jobs-unified-top-card__job-insight',
        '.job-details-fit-level-preferences button span strong',
        '.job-details-preferences-module button span',
    ]

    for selector in job_type_selectors:
        try:
            type_elem = driver.find_element(By.CSS_SELECTOR, selector)
            if type_elem:
                job_type_text = type_elem.text.strip()

                if not job_type_text:
                    html = type_elem.get_attribute('innerHTML')
                    matches = re.findall(r'<!---->(.*?)<!---->', html)
                    if matches:
                        for match in matches:
                            match_lower = match.lower()
                            if any(keyword in match_lower for keyword in ['remote', 'on-site', 'onsite', 'hybrid']):
                                job_type_text = match.strip()
                                break

                if job_type_text and any(
                        keyword in job_type_text.lower() for keyword in ['remote', 'on-site', 'onsite', 'hybrid']):
                    details['job_type'] = job_type_text
                    break
        except:
            continue

    # Fallback detection
    if details['job_type'] == 'N/A' and details['location'] != 'N/A':
        location_lower = details['location'].lower()
        if 'remote' in location_lower:
            details['job_type'] = 'Remote'
        elif 'hybrid' in location_lower:
            details['job_type'] = 'Hybrid'
        elif 'on-site' in location_lower or 'onsite' in location_lower:
            details['job_type'] = 'On-site'

    # JOB DESCRIPTION
    description_selectors = [
        '#job-details',
        '.jobs-description__content',
        '.jobs-description-content__text',
        '.jobs-box__html-content',
        'article.jobs-description__container',
        '.job-details-jobs-unified-top-card__job-description',
        'div[class*="jobs-description"]',
    ]

    description_text = ""
    for selector in description_selectors:
        try:
            desc_elem = driver.find_element(By.CSS_SELECTOR, selector)
            if desc_elem:
                description_text = desc_elem.text.strip()
                if description_text and len(description_text) > 50:
                    break
        except:
            continue

    details['description'] = description_text

    return details


# ========================================
# JOB COLLECTION VIA LINKEDIN'S PUBLIC JOBS FEED
# (no login, no browser - same listings LinkedIn shows logged-out visitors)
# ========================================

_GUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/157.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
_GUEST_SEARCH = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
_GUEST_DETAIL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"


def _guest_get(url, params=None, tries=4):
    import html as _html  # noqa: F401
    for attempt in range(tries):
        try:
            r = requests.get(url, params=params, headers=_GUEST_HEADERS, timeout=20)
            if r.status_code == 200:
                return r.text
            if r.status_code in (429, 999) or r.status_code >= 500:
                wait = 30 * (attempt + 1)
                logger.warning(f"      [!] LinkedIn rate limit ({r.status_code}), waiting {wait}s...")
                time.sleep(wait)
                continue
            return None
        except Exception as e:
            logger.debug(f"      guest request error: {e}")
            time.sleep(5)
    return None


def _clean(text):
    import html as _html
    return _html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or ""))).strip()


def _parse_guest_cards(page_html):
    cards = []
    for block in re.split(r"<li>", page_html)[1:]:
        m = re.search(r'urn:li:jobPosting:(\d+)', block)
        if not m:
            continue
        title = re.search(r'base-search-card__title[^>]*>(.*?)</h3>', block, re.S)
        company = re.search(r'base-search-card__subtitle[^>]*>(.*?)</h4>', block, re.S)
        location = re.search(r'job-search-card__location[^>]*>(.*?)</span>', block, re.S)
        cards.append({
            "id": m.group(1),
            "title": _clean(title.group(1)) if title else "",
            "company": _clean(company.group(1)) if company else "",
            "location": _clean(location.group(1)) if location else "",
        })
    return cards


def _guest_job_details(job_id):
    page = _guest_get(_GUEST_DETAIL.format(job_id))
    if not page:
        return {"description": "", "employment_type": "", "seniority": ""}
    desc = re.search(r'show-more-less-html__markup[^>]*>(.*?)</div>', page, re.S)
    criteria = dict((_clean(k), _clean(v)) for k, v in re.findall(
        r'description__job-criteria-subheader[^>]*>(.*?)</h3>.*?description__job-criteria-text[^>]*>(.*?)</span>', page, re.S))
    return {
        "description": _clean(desc.group(1)) if desc else "",
        "employment_type": criteria.get("Employment type", ""),
        "seniority": criteria.get("Seniority level", ""),
    }


def scrape_all_jobs():
    """Collect jobs for every role/location from LinkedIn's public jobs feed."""
    logger.info("\n" + "=" * 70)
    logger.info("STEP 1: COLLECTING JOBS FROM LINKEDIN (public jobs feed)")
    logger.info("=" * 70)

    time_filter_param = {"24_hours": "r86400", "7_days": "r604800"}.get(JOB_TIME_FILTER, "r604800")
    logger.info(f"[INFO] Time filter: {JOB_TIME_FILTER}")

    configs = []
    for role_cfg in JOB_ROLES:
        role = role_cfg['role']
        if role_cfg.get('local_jobs', 0) > 0 and LOCAL_LOCATIONS:
            per_loc = max(1, role_cfg['local_jobs'] // len(LOCAL_LOCATIONS))
            for loc in LOCAL_LOCATIONS:
                configs.append({'role': role, 'search_name': f"{role} - {loc.split(',')[0].strip()}",
                                'location': loc, 'jobs': per_loc, 'job_type': 'any'})
        if role_cfg.get('remote_jobs', 0) > 0:
            for rloc in (REMOTE_LOCATIONS or [REMOTE_LOCATION]):
                configs.append({'role': role, 'search_name': f"{role} - Remote {rloc}",
                                'location': rloc, 'jobs': role_cfg['remote_jobs'], 'job_type': 'remote'})

    logger.info(f"Total searches to run: {len(configs)}")
    all_jobs, blacklisted = [], 0
    details_cache = {}

    for idx, cfg in enumerate(configs):
        try:
            logger.info(f"\n[{idx + 1}/{len(configs)}] {cfg['search_name']}  (target {cfg['jobs']})")
            collected, start, empty_pages = 0, 0, 0
            seen_here = set()
            while collected < cfg['jobs'] and start < 250:
                params = {"keywords": cfg['role'], "location": cfg['location'],
                          "f_TPR": time_filter_param, "f_E": "2,3,4", "start": start}
                if cfg['job_type'] == 'remote':
                    params["f_WT"] = "2"
                page = _guest_get(_GUEST_SEARCH, params)
                cards = _parse_guest_cards(page) if page else []
                if not cards:
                    empty_pages += 1
                    if empty_pages >= 2:
                        break
                    start += 10
                    continue
                start += len(cards)

                for card in cards:
                    if collected >= cfg['jobs']:
                        break
                    if card['id'] in seen_here or not card['title'] or not card['company']:
                        continue
                    seen_here.add(card['id'])
                    if is_blacklisted_company(card['company']):
                        blacklisted += 1
                        continue

                    if card['id'] not in details_cache:
                        details_cache[card['id']] = _guest_job_details(card['id'])
                        time.sleep(random.uniform(2.5, 4.0))  # gentle pace avoids LinkedIn rate limits
                    det = details_cache[card['id']]

                    url = f"https://www.linkedin.com/jobs/view/{card['id']}/"
                    job_type = 'Remote' if 'remote' in (card['location'] + ' ' + card['title']).lower() else (det['employment_type'] or 'Not specified')
                    location = card['location'] or (f"{cfg['location']} (Remote)" if cfg['job_type'] == 'remote' else cfg['location'])
                    all_jobs.append({
                        'job_id': generate_job_id(card['title'], card['company'], url),
                        'url_id': card['id'],
                        'search_name': cfg['search_name'],
                        'role': cfg['role'],
                        'title': card['title'],
                        'company': card['company'],
                        'location': location,
                        'job_type': job_type,
                        'description': det['description'],
                        'url': url,
                        'date': datetime.now().strftime('%Y-%m-%d'),
                    })
                    collected += 1
                    if collected % 5 == 0:
                        logger.info(f"   -> {collected}/{cfg['jobs']} jobs...")
                time.sleep(random.uniform(2.5, 4.0))

            logger.info(f"   -> Collected {collected} jobs")
        except Exception as e:
            logger.error(f"   [X] Error in search {idx + 1}: {e}")
            log_error("Search Error", "scrape_all_jobs", str(e), cfg['search_name'])

    logger.info(f"\n[OK] COLLECTION COMPLETE")
    logger.info(f"   Total jobs collected: {len(all_jobs)}")
    logger.info(f"   Blacklisted: {blacklisted}")
    return (pd.DataFrame(all_jobs) if all_jobs else pd.DataFrame()), blacklisted


# ========================================
# EXTRA SOURCES (16 Nov): Wellfound public role pages + job-alert emails
# Both return rows in the same shape as scrape_all_jobs(), so everything downstream is unchanged.
# ========================================

_WF_INDIA = re.compile(r"india|bengaluru|bangalore|delhi|gurugram|gurgaon|noida|pune|hyderabad|mumbai|chennai|"
                       r"kolkata|ahmedabad|jaipur|kochi|indore|chandigarh|hsr layout|koramangala", re.I)
_WF_REMOTE_OK = re.compile(r"india|asia|apac|worldwide|anywhere|global", re.I)


def _job_row(title, company, location, job_type, description, url, url_id, role, search_name):
    return {
        'job_id': generate_job_id(title, company, url), 'url_id': url_id, 'search_name': search_name,
        'role': role, 'title': title, 'company': company, 'location': location, 'job_type': job_type,
        'description': description, 'url': url, 'date': datetime.now().strftime('%Y-%m-%d'),
    }


def scrape_wellfound_jobs():
    """Wellfound public role pages (no login; /role/ pages are allowed by wellfound.com/robots.txt)."""
    if not WELLFOUND_ENABLED:
        return []
    logger.info("\n" + "=" * 70)
    logger.info("STEP 1b: COLLECTING JOBS FROM WELLFOUND (public role pages)")
    logger.info("=" * 70)
    max_age = {"24_hours": 1, "7_days": 7}.get(JOB_TIME_FILTER, 7)
    cutoff = time.time() - max_age * 86400
    pages = [(r, f"https://wellfound.com/role/l/{r}/{loc}", loc) for r in WELLFOUND_ROLES for loc in WELLFOUND_LOCATIONS]
    if WELLFOUND_INCLUDE_REMOTE:
        pages += [(r, f"https://wellfound.com/role/r/{r}", "remote") for r in WELLFOUND_ROLES]
    rows, seen, skipped = [], set(), {"old": 0, "remote_elsewhere": 0, "not_india": 0, "blacklisted": 0}
    for role_slug, url, where in pages:
        try:
            r = requests.get(url, headers=_GUEST_HEADERS, timeout=25)
            m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', r.text, re.S) if r.status_code == 200 else None
            if not m:
                logger.warning(f"   [!] Wellfound {where}/{role_slug}: HTTP {r.status_code}, no data")
                continue
            data = json.loads(m.group(1))["props"]["pageProps"].get("apolloState", {}).get("data", {})
            company_of = {}
            for v in data.values():
                if v.get("__typename") == "StartupResult":
                    for ref in v.get("highlightedJobListings") or []:
                        company_of[str(ref.get("__ref", "")).split(":")[-1]] = v.get("name", "")
            found = 0
            for v in data.values():
                if v.get("__typename") != "JobListingSearchResult" or v.get("id") in seen:
                    continue
                seen.add(v.get("id"))
                title, company = (v.get("title") or "").strip(), company_of.get(str(v.get("id")), "")
                if not title or not company:
                    continue
                if (v.get("liveStartAt") or 0) < cutoff:
                    skipped["old"] += 1
                    continue
                if is_blacklisted_company(company):
                    skipped["blacklisted"] += 1
                    continue
                locs = ", ".join(v.get("locationNames") or [])
                kind = ((v.get("remoteConfig") or {}).get("kind") or "").upper()
                accepted = v.get("acceptedRemoteLocationNames") or []
                is_remote = kind in ("REMOTE", "ONSITE_OR_REMOTE") or bool(v.get("remote"))
                in_india = bool(_WF_INDIA.search(locs))
                if where == "remote":
                    # remote jobs must accept India / worldwide; an empty list = no restriction stated
                    if not is_remote or (accepted and not any(_WF_REMOTE_OK.search(a) for a in accepted)):
                        skipped["remote_elsewhere"] += 1
                        continue
                elif not in_india:
                    skipped["not_india"] += 1
                    continue
                yrs = v.get("yearsExperienceMin")
                desc = (v.get("description") or "")
                if yrs is not None:
                    desc = f"Minimum {int(yrs)} years of experience required.\n" + desc
                comp = v.get("compensation") or ""
                if comp:
                    desc += f"\nCompensation: {comp}"
                location = (locs + ", India") if in_india and "india" not in locs.lower() else (locs or "Remote")
                job_type = "Remote" if (is_remote and kind != "ONSITE_OR_REMOTE") else ("Remote / On-site" if is_remote else "On-site")
                if is_remote and where == "remote":
                    location = f"Remote ({', '.join(accepted) or 'no restriction stated'})"
                rows.append(_job_row(title, company, location, job_type, desc,
                                     f"https://wellfound.com/jobs/{v['id']}-{v.get('slug') or 'job'}",
                                     f"wf{v['id']}", title, f"Wellfound - {role_slug} - {where}"))
                found += 1
            logger.info(f"   Wellfound {role_slug} / {where}: {found} jobs")
        except Exception as e:
            logger.error(f"   [X] Wellfound {where}/{role_slug}: {e}")
            log_error("Search Error", "scrape_wellfound_jobs", str(e), url)
        time.sleep(random.uniform(2.0, 3.5))
    logger.info(f"[OK] Wellfound: {len(rows)} jobs (skipped: {skipped})")
    return rows


_ALERT_QUERY = ('from:(jobalerts-noreply@linkedin.com OR jobs-noreply@linkedin.com OR naukri.com OR '
                'indeed.com OR indeedemail.com OR wellfound.com)')
_ALERT_LINKS = [
    ("LinkedIn", re.compile(r"linkedin\.com/(?:comm/)?jobs/view/(\d+)", re.I)),
    ("Naukri", re.compile(r"naukri\.com/job-listings-[\w-]*?-(\d{9,})", re.I)),
    ("Indeed", re.compile(r"indeed\.(?:com|co\.in)/(?:rc/clk|viewjob|pagead/clk|applystart)[^\"'\s]*?[?&]jk=([0-9a-f]{8,})", re.I)),
    ("Wellfound", re.compile(r"wellfound\.com/jobs/(\d+)(-[\w-]+)?", re.I)),
]


def _alert_anchors(html_body):
    """(href, anchor text, text right after) for every link in an alert email."""
    from html.parser import HTMLParser

    class P(HTMLParser):
        def __init__(self):
            super().__init__()
            self.items, self.href, self.buf, self.tail_for = [], None, [], None

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                self.href, self.buf = dict(attrs).get("href", ""), []

        def handle_endtag(self, tag):
            if tag == "a" and self.href is not None:
                self.items.append([self.href, " ".join("".join(self.buf).split()), []])
                self.href = None

        def handle_data(self, d):
            if self.href is not None:
                self.buf.append(d)
            elif self.items and d.strip() and len(self.items[-1][2]) < 3:
                self.items[-1][2].append(" ".join(d.split()))

    p = P()
    p.feed(html_body or "")
    return [(h, t, tail) for h, t, tail in p.items]


def scrape_job_alert_emails():
    """Jobs from LinkedIn / Naukri / Indeed / Wellfound alert emails in Gmail (read-only)."""
    if not JOB_ALERT_EMAILS_ENABLED:
        return []
    logger.info("\n" + "=" * 70)
    logger.info("STEP 1c: COLLECTING JOBS FROM JOB-ALERT EMAILS (Gmail, read-only)")
    logger.info("=" * 70)
    rows, seen, per_source = [], set(), {}
    try:
        conn = mail_guard()._imap()
        q = f"{_ALERT_QUERY} newer_than:{int(JOB_ALERT_LOOKBACK_DAYS)}d"
        status, data = conn.search(None, "X-GM-RAW", '"' + q.replace('"', '\\"') + '"')
        ids = data[0].split() if status == "OK" and data and data[0] else []
        logger.info(f"   Alert emails found: {len(ids)}")
        for mid in ids[-60:]:
            status, msg_data = conn.fetch(mid, "(BODY.PEEK[])")
            if status != "OK" or not msg_data or not msg_data[0]:
                continue
            msg = email_lib.message_from_bytes(msg_data[0][1])
            body = ""
            for part in msg.walk():
                if part.get_content_type() == "text/html":
                    body += (part.get_payload(decode=True) or b"").decode(part.get_content_charset() or "utf-8", "ignore")
            for href, text, tail in _alert_anchors(body):
                for src, pat in _ALERT_LINKS:
                    m = pat.search(href)
                    if not m or (src, m.group(1)) in seen:
                        continue
                    seen.add((src, m.group(1)))
                    title, company, location, desc = text, (tail[0] if tail else ""), (tail[1] if len(tail) > 1 else ""), ""
                    if src == "LinkedIn":
                        url = f"https://www.linkedin.com/jobs/view/{m.group(1)}/"
                        page = _guest_get(_GUEST_DETAIL.format(m.group(1)))
                        if page:
                            t = re.search(r'topcard__title[^>]*>(.*?)</h2>', page, re.S)
                            c = re.search(r'topcard__org-name-link[^>]*>(.*?)</a>', page, re.S)
                            l = re.search(r'topcard__flavor--bullet[^>]*>(.*?)</span>', page, re.S)
                            title = _clean(t.group(1)) if t else title
                            company = _clean(c.group(1)) if c else company
                            location = _clean(l.group(1)) if l else location
                            desc = _guest_job_details(m.group(1))["description"]
                        time.sleep(random.uniform(2.5, 4.0))
                    elif src == "Naukri":
                        url = href.split("?")[0]
                    elif src == "Indeed":
                        url = f"https://in.indeed.com/viewjob?jk={m.group(1)}"
                    else:
                        url = f"https://wellfound.com/jobs/{m.group(1)}{m.group(2) or ''}"
                    if not title or len(title) > 120 or not company or len(company) > 80:
                        continue
                    if is_blacklisted_company(company):
                        continue
                    if location and "remote" in location.lower():
                        job_type = "Remote"
                    else:
                        job_type = "Not specified"
                    rows.append(_job_row(title, company, location or "India", job_type, desc, url,
                                         f"{src[:2].lower()}{m.group(1)}", title, f"{src} job alert"))
                    per_source[src] = per_source.get(src, 0) + 1
                    break
    except Exception as e:
        logger.error(f"   [X] Job-alert emails: {e}")
        log_error("Search Error", "scrape_job_alert_emails", str(e), "")
    logger.info(f"[OK] Job-alert emails: {len(rows)} jobs {per_source or ''}")
    return rows


def scrape_all_jobs_selenium(max_configs=None):
    """
    Logged-in LinkedIn search in Chrome (new /jobs/search-results/ page, rewritten 16 Nov).
    - Region is passed as geoId (the new page ignores location=...).
    - The new page drops f_WT, so remote searches add "remote" to the query and only keep cards
      LinkedIn itself labels "(Remote)".
    - Job IDs come from the card's componentkey (no clicking); descriptions from the public job page.
    Returns (DataFrame, blacklisted). An empty DataFrame means "fall back to the public feed".
    """
    logger.info("\n" + "=" * 70)
    logger.info("STEP 1: COLLECTING JOBS FROM LINKEDIN (logged-in search in Chrome)")
    logger.info("=" * 70)
    time_filter_param = {"24_hours": "r86400", "7_days": "r604800"}.get(JOB_TIME_FILTER, "r604800")

    configs = []
    for role_cfg in JOB_ROLES:
        role = role_cfg['role']
        if role_cfg.get('local_jobs', 0) > 0 and LOCAL_LOCATIONS:
            per_loc = max(1, role_cfg['local_jobs'] // len(LOCAL_LOCATIONS))
            for loc in LOCAL_LOCATIONS:
                configs.append({'role': role, 'query': role, 'search_name': f"{role} - {loc.split(',')[0].strip()}",
                                'location': loc, 'jobs': per_loc, 'job_type': 'any'})
        if role_cfg.get('remote_jobs', 0) > 0:
            for rloc in (REMOTE_LOCATIONS or [REMOTE_LOCATION]):
                configs.append({'role': role, 'query': f"{role} remote", 'search_name': f"{role} - Remote {rloc}",
                                'location': rloc, 'jobs': role_cfg['remote_jobs'], 'job_type': 'remote'})
    if max_configs:
        configs = configs[:max_configs]

    try:
        driver = create_driver()
    except Exception as e:
        logger.error(f"[X] Could not start Chrome: {e}")
        return pd.DataFrame(), 0
    all_jobs, blacklisted, seen_ids, details_cache = [], 0, set(), {}
    try:
        if not linkedin_login_with_retry(driver):
            logger.error("[X] LinkedIn login failed")
            return pd.DataFrame(), 0
        logger.info(f"Total searches to run: {len(configs)}")
        for idx, cfg in enumerate(configs):
            try:
                geo = _linkedin_geo_id(cfg['location'])
                logger.info(f"\n[{idx + 1}/{len(configs)}] {cfg['search_name']}  (target {cfg['jobs']}, geoId {geo})")
                url = ("https://www.linkedin.com/jobs/search-results/?keywords=" + requests.utils.quote(cfg['query'])
                       + f"&f_TPR={time_filter_param}" + (f"&geoId={geo}" if geo else ""))
                try:
                    driver.get(url)
                except TimeoutException:
                    pass
                time.sleep(random.uniform(5, 7))
                if driver.window_handles:
                    driver.switch_to.window(driver.window_handles[-1])
                if not _linkedin_logged_in(driver) and 'search-results' not in driver.current_url:
                    logger.warning(f"   [!] Not on the results page ({driver.current_url}), re-checking login...")
                    if not linkedin_login_with_retry(driver):
                        break
                    driver.get(url)
                    time.sleep(6)

                collected, page, skipped_onsite = 0, 1, 0
                while collected < cfg['jobs'] and page <= 6:
                    cards = _selenium_job_cards(driver)
                    if not cards:
                        logger.warning(f"   [!] No job cards on page {page}")
                        break
                    for c in cards:
                        if collected >= cfg['jobs']:
                            break
                        if c['id'] in seen_ids:
                            continue
                        seen_ids.add(c['id'])
                        if cfg['job_type'] == 'remote' and '(remote)' not in c['location'].lower():
                            skipped_onsite += 1
                            continue
                        if is_blacklisted_company(c['company']):
                            blacklisted += 1
                            continue
                        if c['id'] not in details_cache:
                            details_cache[c['id']] = _guest_job_details(c['id'])
                            time.sleep(random.uniform(2.0, 3.5))
                        det = details_cache[c['id']]
                        loc_l = c['location'].lower()
                        job_type = ('Remote' if '(remote)' in loc_l else 'Hybrid' if '(hybrid)' in loc_l
                                    else 'On-site' if '(on-site)' in loc_l else (det['employment_type'] or 'Not specified'))
                        url_job = f"https://www.linkedin.com/jobs/view/{c['id']}/"
                        all_jobs.append({
                            'job_id': generate_job_id(c['title'], c['company'], url_job), 'url_id': c['id'],
                            'search_name': cfg['search_name'], 'role': cfg['role'], 'title': c['title'],
                            'company': c['company'], 'location': c['location'] or cfg['location'], 'job_type': job_type,
                            'description': det['description'], 'url': url_job, 'date': datetime.now().strftime('%Y-%m-%d'),
                        })
                        collected += 1
                    if collected >= cfg['jobs'] or not _selenium_next_page(driver):
                        break
                    page += 1
                logger.info(f"   -> Collected {collected} jobs" + (f" (skipped {skipped_onsite} not labelled Remote)" if skipped_onsite else ""))
            except Exception as e:
                logger.error(f"   [X] Error in search {idx + 1}: {e}")
                log_error("Search Error", "scrape_all_jobs_selenium", str(e), cfg['search_name'])
            time.sleep(random.uniform(3, 5))
    finally:
        try:
            driver.quit()
        except Exception:
            pass
    logger.info(f"\n[OK] COLLECTION COMPLETE (Chrome): {len(all_jobs)} jobs, {blacklisted} blacklisted")
    return (pd.DataFrame(all_jobs) if all_jobs else pd.DataFrame()), blacklisted


_GEO_CACHE = {}


def _linkedin_geo_id(location):
    """LinkedIn region id for a location name (the new search page needs geoId, not location=)."""
    key = location.strip().lower()
    if key in LINKEDIN_GEO_IDS:
        return LINKEDIN_GEO_IDS[key]
    if key not in _GEO_CACHE:
        page = _guest_get("https://www.linkedin.com/jobs/search", {"keywords": "Product Manager", "location": location}) or ""
        m = re.search(r'name="geoId" value="(\d+)"', page)
        _GEO_CACHE[key] = m.group(1) if m else ""
    return _GEO_CACHE[key]


def _selenium_job_cards(driver):
    """Job cards on the new results page: [{id, title, company, location}] (scrolls so all 25 load)."""
    last = -1
    for _ in range(8):
        els = driver.find_elements(By.CSS_SELECTOR, '[componentkey^="job-card-component-ref-"]')
        if len(els) == last:
            break
        last = len(els)
        if els:
            driver.execute_script("arguments[0].scrollIntoView({block: 'end'});", els[-1])
            time.sleep(1.5)
    cards, seen = [], set()
    for e in driver.find_elements(By.CSS_SELECTOR, '[componentkey^="job-card-component-ref-"]'):
        try:
            jid = (e.get_attribute("componentkey") or "").rsplit("-", 1)[-1]
            lines = [x.strip() for x in (e.text or "").split("\n") if x.strip() and x.strip() != "·"]
        except Exception:
            continue
        if not jid.isdigit() or jid in seen or len(lines) < 3:
            continue
        seen.add(jid)
        first = re.sub(r"\s*\(Verified job\)\s*$", "", lines[0]).strip()
        rest = lines[2:] if len(lines) > 3 and lines[1].strip() == first else lines[1:]
        cards.append({"id": jid, "title": first, "company": rest[0] if rest else "",
                      "location": rest[1] if len(rest) > 1 else ""})
    return cards


def _selenium_next_page(driver):
    for b in driver.find_elements(By.CSS_SELECTOR, "button"):
        try:
            if b.text.strip() == "Next" and b.is_enabled():
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", b)
                time.sleep(random.uniform(4, 6))
                return True
        except Exception:
            continue
    return False


def scrape_all_jobs_selenium_old_layout():

    """OLD browser-based scraper for LinkedIn's previous job page (selectors no longer match). Unused."""
    logger.info("\n" + "=" * 70)
    logger.info("STEP 1: SCRAPING JOBS FROM LINKEDIN")
    logger.info("=" * 70)

    # Validate JOB_TIME_FILTER
    valid_time_filters = {
        "24_hours": "r86400",  # 86400 seconds = 24 hours
        "7_days": "r604800"  # 604800 seconds = 7 days (1 week)
    }

    global JOB_TIME_FILTER
    if JOB_TIME_FILTER not in valid_time_filters:
        logger.warning(f"[!] Invalid JOB_TIME_FILTER value: '{JOB_TIME_FILTER}'")
        logger.warning(f"[!] Valid options: '24_hours' or '7_days'")
        logger.warning(f"[!] Defaulting to '7_days'")
        JOB_TIME_FILTER = "7_days"

    time_filter_param = valid_time_filters[JOB_TIME_FILTER]
    logger.info(f"[INFO] Using time filter: {JOB_TIME_FILTER} (LinkedIn param: {time_filter_param})")

    driver = create_driver()
    all_jobs = []
    blacklisted = 0

    try:
        if not linkedin_login_with_retry(driver):
            logger.error("[X]¢â‚¬â„¢ Failed to login to LinkedIn")
            driver.quit()
            return pd.DataFrame(), 0

        configs = []
        for role_cfg in JOB_ROLES:
            role = role_cfg['role']

            if role_cfg['local_jobs'] > 0:
                jobs_per_location = role_cfg['local_jobs'] // len(LOCAL_LOCATIONS)
                for loc in LOCAL_LOCATIONS:
                    loc_name = loc.split(',')[0].strip()
                    configs.append({
                        'role': role,
                        'search_name': f"{role} - {loc_name}",
                        'location': loc,
                        'jobs': jobs_per_location,
                        'job_type': 'any'
                    })

            if role_cfg['remote_jobs'] > 0:
                configs.append({
                    'role': role,
                    'search_name': f"{role} - Remote {REMOTE_LOCATION}",
                    'location': REMOTE_LOCATION,
                    'jobs': role_cfg['remote_jobs'],
                    'job_type': 'remote'
                })

        logger.info(f"Total searches to run: {len(configs)}")

        for idx, cfg in enumerate(configs):
            try:
                logger.info(f"\n[{idx + 1}/{len(configs)}] {cfg['search_name']}")
                logger.info(f"   Target: {cfg['jobs']} jobs")

                url = f"https://www.linkedin.com/jobs/search/?keywords={cfg['role'].replace(' ', '%20')}"
                url += f"&location={cfg['location'].replace(' ', '%20').replace(',', '%2C')}"
                if cfg['job_type'] == 'remote':
                    url += "&f_WT=2"
                url += f"&f_TPR={time_filter_param}"  # Use configurable time filter
                # Add experience level filter: Entry level (2) OR Associate (3) OR Mid-Senior (4)
                url += "&f_E=2%2C3"

                try:
                    driver.current_url
                    if 'linkedin.com' in driver.current_url:
                        if 'login' in driver.current_url or 'checkpoint' in driver.current_url:
                            logger.warning("   [!] Session expired, re-logging in...")
                            if not linkedin_login_with_retry(driver):
                                logger.error("   [X]¢â‚¬â„¢ Re-login failed")
                                continue
                except:
                    logger.warning("   [!] Browser session died, recreating...")
                    driver = create_driver()
                    if not linkedin_login_with_retry(driver):
                        logger.error("   [X]¢â‚¬â„¢ Re-login failed")
                        continue

                driver.get(url)
                time.sleep(5)

                # Initialize pagination variables
                target_jobs = cfg['jobs']
                collected = 0
                failed = 0
                url_unchanged = 0
                current_page = 1
                max_pages = 6

                logger.info(f"   -> Target: {target_jobs} jobs | Max pages: {max_pages}")

                # Pagination loop - collect jobs from multiple pages
                while collected < target_jobs and current_page <= max_pages:
                    logger.info(f"   -> Page {current_page}: Scrolling to load jobs...")

                    # Scroll current page to load all job cards
                    prev_card_count = 0
                    no_change_count = 0
                    max_scrolls = 100

                    for scroll in range(max_scrolls):
                        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                        time.sleep(2)

                        if scroll % 25 == 0:
                            current_cards = len(get_job_cards(driver))
                            if current_cards == prev_card_count:
                                no_change_count += 1
                                if no_change_count >= 3:
                                    logger.info(
                                        f"      -> Loaded all cards on page {current_page} ({current_cards} cards)")
                                    break
                            else:
                                no_change_count = 0
                                prev_card_count = current_cards

                    # Get job cards from current page
                    cards = get_job_cards(driver)

                    if len(cards) == 0:
                        logger.warning(f"   [!] No job cards found on page {current_page}")
                        break

                    logger.info(f"   -> Processing {len(cards)} cards on page {current_page}...")

                    # Process each job card
                    for card_idx, card in enumerate(cards):
                        # Check if we've reached target
                        if collected >= target_jobs:
                            logger.info(f"      -> Target reached! Collected {collected}/{target_jobs} jobs")
                            break

                        try:
                            # Get current URL BEFORE clicking
                            old_url = driver.current_url

                            # Scroll card into view
                            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                            time.sleep(1)

                            # Try clicking the card (with fallback methods)
                            clicked = False

                            # Method 1: JavaScript click
                            try:
                                driver.execute_script("arguments[0].click();", card)
                                if wait_for_url_change(driver, old_url, timeout=8):
                                    clicked = True
                            except:
                                pass

                            # Method 2: Regular click (if JavaScript didn't work)
                            if not clicked:
                                try:
                                    card.click()
                                    if wait_for_url_change(driver, old_url, timeout=8):
                                        clicked = True
                                except:
                                    pass

                            # Method 3: One more retry with extra wait (if both previous methods failed)
                            if not clicked:
                                logger.debug(f"      [!] Card {card_idx + 1}: First attempts failed, retrying...")
                                time.sleep(2)  # Extra wait before final retry
                                try:
                                    driver.execute_script("arguments[0].click();", card)
                                    if wait_for_url_change(driver, old_url, timeout=8):
                                        clicked = True
                                except:
                                    pass

                            # If all methods failed, skip this card
                            if not clicked:
                                logger.info(
                                    f"      [SKIP] Card {card_idx + 1}: URL did not change after 8s wait (tried 3 times)")
                                url_unchanged += 1
                                continue

                            # Wait for job details to fully load
                            time.sleep(5)

                            # Extract details
                            details = extract_job_details_enhanced(driver)

                            # Verify we got valid details
                            if not details['title'] or not details['company']:
                                failed += 1
                                if failed % 5 == 0:
                                    logger.warning(f"      [!] Failed {failed} extractions")
                                continue

                            if details['location'] == 'N/A':
                                if cfg['job_type'] == 'remote':
                                    details['location'] = f'{REMOTE_LOCATION} (Remote)'
                                else:
                                    details['location'] = cfg['location']

                            if details['job_type'] == 'N/A':
                                if cfg['job_type'] == 'remote':
                                    details['job_type'] = 'Remote'
                                else:
                                    details['job_type'] = 'Not specified'

                            if is_blacklisted_company(details['company']):
                                logger.debug(f"      [!] {details['company']} - Blacklisted")
                                blacklisted += 1
                                continue

                            current_url = driver.current_url
                            job_id = generate_job_id(details['title'], details['company'], current_url)
                            url_id = extract_job_id_from_url(current_url)

                            all_jobs.append({
                                'job_id': job_id,
                                'url_id': url_id if url_id != "N/A" else job_id[:8],
                                'search_name': cfg['search_name'],
                                'role': cfg['role'],
                                'title': details['title'],
                                'company': details['company'],
                                'location': details['location'],
                                'job_type': details['job_type'],
                                'description': details.get('description', ''),
                                'url': current_url,
                                'date': datetime.now().strftime('%Y-%m-%d')
                            })

                            collected += 1

                            if (collected % 5) == 0:
                                logger.info(f"      -> Collected {collected}/{target_jobs} jobs (Page {current_page})")

                        except Exception as e:
                            failed += 1
                            continue

                    # After processing cards on this page, check if we should continue to next page
                    if collected >= target_jobs:
                        logger.info(f"   -> Target reached! Collected {collected}/{target_jobs} jobs")
                        break

                    if current_page >= max_pages:
                        logger.info(f"   -> Reached max pages ({max_pages}). Collected {collected}/{target_jobs} jobs")
                        break

                    # Try to navigate to next page
                    logger.info(f"   -> Checking for next page...")
                    next_page_found = False

                    try:
                        # Look for "Next" button
                        next_selectors = [
                            'button[aria-label="View next page"]',
                            'button.artdeco-pagination__button--next',
                            f'button[aria-label*="Page {current_page + 1}"]',
                        ]

                        for selector in next_selectors:
                            try:
                                next_button = driver.find_element(By.CSS_SELECTOR, selector)
                                if next_button and next_button.is_enabled():
                                    logger.info(f"      -> Clicking Next button to load page {current_page + 1}...")
                                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});",
                                                          next_button)
                                    time.sleep(1)
                                    driver.execute_script("arguments[0].click();", next_button)
                                    time.sleep(5)  # Wait for new page to load
                                    next_page_found = True
                                    current_page += 1
                                    logger.info(f"      -> Successfully loaded page {current_page}")
                                    break
                            except Exception as e:
                                continue
                    except Exception as e:
                        logger.debug(f"      [!] Error checking pagination: {e}")

                    if not next_page_found:
                        logger.info(f"   -> No more pages available. Collected {collected}/{target_jobs} jobs")
                        break

                # Summary for this search
                logger.info(f"   -> Collection complete for this search")
                logger.info(f"      -> Collected: {collected} jobs")
                if failed > 0:
                    logger.info(f"      -> Failed extractions: {failed}")
                if url_unchanged > 0:
                    logger.info(f"      -> Skipped (URL unchanged): {url_unchanged}")

                time.sleep(3)

            except Exception as e:
                logger.error(f"   [X] Error in search {idx + 1}: {e}\n")
                log_error("Search Error", "scrape_all_jobs", str(e), cfg['search_name'])

                continue

        driver.quit()
        logger.info(f"\n[OK] SCRAPING COMPLETE")
        logger.info(f"   Total jobs collected: {len(all_jobs)}")
        logger.info(f"   Blacklisted: {blacklisted}")

    except Exception as e:
        logger.error(f"[X]¢â‚¬â„¢ Error: {e}")
        import traceback
        traceback.print_exc()
        driver.quit()

    return pd.DataFrame(all_jobs) if all_jobs else pd.DataFrame(), blacklisted


# ========================================
# IMPROVED DEDUPLICATION WITH DEBUG LOGGING
# ========================================

def deduplicate_jobs_improved(df):
    """
    Deduplicate jobs and log all jobs before dedup for debugging
    """
    logger.info("\n" + "=" * 70)
    logger.info("DEDUPLICATING JOBS")
    logger.info("=" * 70)

    # FIRST: Log all jobs BEFORE deduplication
    logger.info("   -> Logging all jobs to 'Jobs (Before Dedup)' sheet...")

    # Collect all rows first
    rows_to_log = []
    for idx, job in df.iterrows():
        rows_to_log.append([
            job['date'],
            job['job_id'],
            job['search_name'],
            job['title'],
            job['company'],
            job['location'],
            job['job_type'],
            job['url']
        ])

    # Write all rows in a single API call
    log_to_sheet_batch(jobs_before_dedup_sheet, rows_to_log)
    logger.info(f"   [OK] Logged {len(rows_to_log)} jobs in batch")
    original_count = len(df)

    # IMPROVED: Extract LinkedIn Job ID from URL for better deduplication
    # LinkedIn URLs can have different formats:
    # 1. /jobs/view/1234567890 (direct job URL)
    # 2. ?currentJobId=1234567890 (search URL with job ID param)
    logger.info("   -> Extracting LinkedIn Job IDs from URLs...")
    
    def extract_linkedin_job_id(url):
        """Extract LinkedIn job ID from URL for deduplication"""
        try:
            url_str = str(url)
            # Pattern 1: /jobs/view/1234567890
            match = re.search(r'/jobs/view/(\d+)', url_str)
            if match:
                return match.group(1)
            # Pattern 2: ?currentJobId=1234567890 or &currentJobId=1234567890
            match = re.search(r'[?&]currentJobId=(\d+)', url_str)
            if match:
                return match.group(1)
            # Fallback to full URL if not a LinkedIn job URL
            return url
        except:
            return url
    
    # Create a new column with extracted job IDs
    df['linkedin_job_id'] = df['url'].apply(extract_linkedin_job_id)
    
    # Check for duplicate LinkedIn Job IDs
    logger.info("   -> Analyzing duplicates by LinkedIn Job ID...")
    job_id_counts = df['linkedin_job_id'].value_counts()
    duplicated_job_ids = job_id_counts[job_id_counts > 1]

    if len(duplicated_job_ids) > 0:
        logger.info(f"   -> Found {len(duplicated_job_ids)} LinkedIn Job IDs that appear multiple times:")
        for job_id, count in duplicated_job_ids.head(5).items():
            logger.info(f"      * Job ID {job_id} appears {count} times")
            # Show which searches found this job
            searches = df[df['linkedin_job_id'] == job_id]['search_name'].unique()
            logger.info(f"        Found in: {', '.join(searches[:3])}")

    # Remove duplicates based on LinkedIn Job ID (not full URL)
    df_dedup = df.drop_duplicates(subset=['linkedin_job_id'], keep='first')
    
    # Drop the temporary column
    df_dedup = df_dedup.drop(columns=['linkedin_job_id'])

    duplicates_removed = original_count - len(df_dedup)

    logger.info(f"✓ DEDUPLICATION COMPLETE")
    logger.info(f"   Original jobs: {original_count}")
    logger.info(f"   Duplicates removed (by LinkedIn Job ID): {duplicates_removed}")
    logger.info(f"   Unique jobs remaining: {len(df_dedup)}")

    if duplicates_removed > original_count * 0.7:
        logger.warning("   [!] WARNING: Over 70% of jobs were duplicates!")
        logger.warning("   This likely means the same jobs appear in multiple searches.")
        logger.warning("   Check 'Jobs (Before Dedup)' sheet for details.")

    return df_dedup, duplicates_removed


# ========================================
# FILTER ALREADY APPLIED JOBS
# ========================================

def filter_already_applied_jobs(df):
    """
    Remove jobs that have already been applied to from the dataframe
    Checks the Applications sheet for existing job_ids
    """
    logger.info("\n" + "=" * 70)
    logger.info("FILTERING ALREADY APPLIED JOBS")
    logger.info("=" * 70)

    try:
        # Get all job IDs from Applications sheet
        all_applications = applications_sheet.get_all_values()

        # Skip header row, get job_id column (index 2)
        applied_job_ids = set()
        for row in all_applications[1:]:  # Skip header
            if len(row) > 2:  # Make sure row has job_id column
                job_id = row[2]  # Job ID is column 2 (0-indexed)
                if job_id:
                    applied_job_ids.add(job_id)

        logger.info(f"   Found {len(applied_job_ids)} previously applied jobs in Applications sheet")

        # Filter out already applied jobs
        original_count = len(df)
        df_filtered = df[~df['job_id'].isin(applied_job_ids)]
        filtered_count = original_count - len(df_filtered)

        logger.info(f"   Jobs before filter: {original_count}")
        logger.info(f"   Already applied (removed): {filtered_count}")
        logger.info(f"   Remaining jobs: {len(df_filtered)}")

        if filtered_count > 0:
            logger.info(f"   Skipped {filtered_count} jobs already in Applications")

        return df_filtered, filtered_count

    except Exception as e:
        logger.error(f"   Error filtering applied jobs: {e}")
        logger.warning("   Proceeding without filtering")
        return df, 0


# ========================================
# JOB MATCHER
# ========================================

def required_experience_years(text):
    """Years of experience the job description asks for (None if not mentioned)."""
    if not text:
        return None
    t = text.lower()
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
             "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15}
    t = re.sub(r'\b(' + '|'.join(words) + r')\b', lambda m: str(words[m.group(1)]), t)
    found = []
    for m in re.finditer(r'(\d{1,2})\s*(?:\+|plus)?\s*(?:-|–|to)?\s*(\d{1,2})?\s*\+?\s*(?:or\s+more\s+)?(?:years?|yrs?)', t):
        lo = int(m.group(1))
        context = t[max(0, m.start() - 50): m.end() + 60]
        if lo > 15 or not re.search(r'experience|exp\b|work|product|software|industry|relevant|professional|'
                                    r'minimum|at least|required|background|track record', context):
            continue
        found.append(lo)
    return max(found) if found else None


def title_is_target(title):
    """Only Product Manager, Associate Product Manager and AI Product Manager (no senior / other PM flavours)."""
    t = f" {str(title).lower()} "
    if any(k in t for k in EXCLUDE_TITLE_KEYWORDS):
        return False
    t = re.sub(r"\s+", " ", t.replace("–", "-").replace("—", "-"))
    if re.search(r"\bapm\b", t):
        return True
    m = re.search(r"([a-z./ ]*?)\s*product manager", t)
    if not m:
        return False
    # Only look at the words just before "product manager" in this part of the title
    prefix = re.split(r"[-,|:(/]| at ", m.group(1))[-1].strip() if m.group(1).strip() else ""
    prefix = re.sub(r"^(the|an?|founding|junior|jr\.?)(\s+|$)", "", prefix).strip()
    return prefix in ALLOWED_PM_PREFIXES


_COMPANY_NOISE = r"\b(india|pvt|private|ltd|limited|inc|llc|llp|technologies|technology|tech|solutions|group|the|corp|corporation|co|company|labs|software|services|global)\b"


def company_key(name):
    """'Optum India Pvt. Ltd.' and 'Optum' -> 'optum' (so name variants count as the same company)."""
    words = re.sub(_COMPANY_NOISE, " ", re.sub(r"[^a-z0-9 ]", " ", str(name).lower())).split()
    return " ".join(words) or str(name).lower().strip()


FREE_EMAIL_DOMAINS = {"gmail.com", "googlemail.com", "yahoo.com", "yahoo.in", "yahoo.co.in", "outlook.com",
                      "hotmail.com", "live.com", "icloud.com", "rediffmail.com", "proton.me", "protonmail.com"}


def previously_emailed_domains():
    """Email domains of every company we have already emailed (HR or referral), -> company name."""
    out = {}
    for sheet, ci, ei, si in ((contacts_sheet, 7, 3, 10), (referral_contacts_sheet, 8, 4, 11)):
        try:
            for r in sheet.get_all_values()[1:]:
                if len(r) > si and r[si] == "Sent" and "@" in r[ei]:
                    d = r[ei].split("@")[-1].lower().strip()
                    if d not in FREE_EMAIL_DOMAINS:
                        out.setdefault(d, r[ci])
        except Exception:
            pass
    return out


def select_jobs_for_outreach(df):
    """
    Keep only PM / APM / AI PM roles that aren't senior, then order them:
    tier 1 (<= MAX_EXPERIENCE_TIER1 yrs or not stated), then tier 2 (<= MAX_EXPERIENCE_TIER2 yrs),
    best match score first. One job per company, and companies contacted in earlier runs are skipped.
    """
    logger.info("\n" + "=" * 70)
    logger.info("SELECTING JOBS FOR OUTREACH")
    logger.info("=" * 70)
    if len(df) == 0:
        return df
    df = df.copy()
    df = df[df['title'].apply(title_is_target)]
    logger.info(f"   PM / APM / AI PM (non-senior) jobs: {len(df)}")

    df['req_years'] = df['description'].apply(required_experience_years)

    def tier(y):
        if y is None or y != y or y <= MAX_EXPERIENCE_TIER1:
            return 1
        if y <= MAX_EXPERIENCE_TIER2:
            return 2
        return 9
    df['tier'] = df['req_years'].apply(tier)
    skipped = int((df['tier'] == 9).sum())
    df = df[df['tier'] < 9]
    logger.info(f"   Skipped (asks > {MAX_EXPERIENCE_TIER2} yrs): {skipped}")

    contacted = set()
    for sheet in (contacts_sheet, referral_contacts_sheet):
        try:
            for r in sheet.get_all_records():
                if str(r.get('Email Status', '')) == 'Sent' and r.get('Company'):
                    contacted.add(company_key(r['Company']))
        except Exception:
            pass
    before = len(df)
    df = df[~df['company'].apply(company_key).isin(contacted)]
    logger.info(f"   Skipped (company already contacted earlier): {before - len(df)}")

    df = df.sort_values(['tier', 'match_score'], ascending=[True, False])
    df['_ckey'] = df['company'].apply(company_key)
    df = df.drop_duplicates(subset=['_ckey'], keep='first').drop(columns=['_ckey'])
    logger.info(f"   Ready: {int((df['tier'] == 1).sum())} jobs asking <= {MAX_EXPERIENCE_TIER1} yrs, "
                f"{int((df['tier'] == 2).sum())} asking {MAX_EXPERIENCE_TIER2} yrs")
    for i, (_, j) in enumerate(df.head(10).iterrows()):
        yrs = '?' if j['req_years'] is None or j['req_years'] != j['req_years'] else int(j['req_years'])
        logger.info(f"   #{i + 1}: {j['title']} @ {j['company']} | score {j['match_score']} | {yrs} yrs")
    return df


def match_jobs(df):
    """
    Match jobs to resume using multi-signal scoring:
    - Title match (30%): Fuzzy match of job title against target roles
    - Skills match (40%): Count of your skills found in job description
    - Experience fit (15%): Penalize senior roles, boost entry/mid-level
    - TF-IDF similarity (15%): Resume vs full job description text
    """
    logger.info("\n" + "=" * 70)
    logger.info("STEP 2: MATCHING JOBS TO RESUME (Multi-Signal)")
    logger.info("=" * 70)

    # Flatten all title aliases into a single list
    all_target_titles = []
    for category_titles in TITLE_ALIASES.values():
        all_target_titles.extend(category_titles)

    def title_score(job_title):
        """Score 0-100: How well does the job title match our target roles?"""
        if not job_title:
            return 0
        title_lower = job_title.lower().strip()

        # Direct match
        if title_lower in all_target_titles:
            return 100

        # Fuzzy match against all target titles
        best = 0
        for target in all_target_titles:
            ratio = SequenceMatcher(None, title_lower, target).ratio()
            if ratio > best:
                best = ratio

        # Also check if key role words appear in the title
        role_words = ["product manager", "product owner", "apm", "product analyst",
                      "product associate", "products associate", "product specialist", "product"]
        word_bonus = 0
        for word in role_words:
            if word in title_lower:
                word_bonus = 0.2
                break

        return round(min((best + word_bonus), 1.0) * 100, 1)

    def skills_score(description):
        """Score 0-100: What percentage of your skills are mentioned?"""
        if not description or len(description) < 20:
            return 30  # Default score when no description available
        desc_lower = description.lower()

        matched = 0
        for skill in MY_SKILLS:
            if skill in desc_lower:
                matched += 1

        # Normalize: 15+ skills matched = 100%
        return round(min(matched / 15.0, 1.0) * 100, 1)

    def experience_score(job_title, description):
        """Score 0-100: How well does the experience level match?"""
        text = f"{job_title} {description}".lower() if description else (job_title or "").lower()

        # Check for senior-level indicators
        for kw in SENIOR_KEYWORDS:
            if kw in text:
                # Check if it mentions years
                import re
                year_matches = re.findall(r'(\d+)\+?\s*(?:years|yrs|yr)', text)
                if year_matches:
                    max_years = max(int(y) for y in year_matches)
                    if max_years > 5:
                        return 15  # Way too senior
                    elif max_years > 3:
                        return 40  # Bit senior
                    else:
                        return 75  # Reasonable
                return 35  # Senior title but no year info

        # Check for junior/intern/fresher
        for kw in JUNIOR_KEYWORDS:
            if kw in text:
                return 80  # Good fit for ~2 yrs experience

        # Check explicit experience requirements
        import re
        year_matches = re.findall(r'(\d+)\+?\s*(?:years|yrs|yr)', text)
        if year_matches:
            min_years = min(int(y) for y in year_matches)
            if min_years <= MY_EXPERIENCE_YEARS + 1:
                return 95  # Great fit
            elif min_years <= MY_EXPERIENCE_YEARS + 3:
                return 60  # Stretch but possible
            else:
                return 20  # Too senior

        return 70  # No experience mentioned, neutral

    def tfidf_score(resume_text, job_text):
        """Score 0-100: TF-IDF cosine similarity between resume and job"""
        try:
            if not job_text or len(job_text) < 20:
                return 30  # Default when no text
            vec = TfidfVectorizer(stop_words='english', max_features=1000)
            tfidf = vec.fit_transform([resume_text, job_text])
            sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
            return round(sim * 100, 1)
        except:
            return 0

    def compute_match_score(row):
        """Compute weighted multi-signal match score"""
        job_title = row.get('title', '') or ''
        description = row.get('description', '') or ''
        role = row.get('role', '') or ''

        # Build job text for TF-IDF (use description if available, fallback to title+role)
        job_text = description if len(description) > 50 else f"{job_title} {role} {description}"

        # Pick correct resume based on job type
        is_fs = is_fullstack_job(job_title)
        resume = FULLSTACK_RESUME_TEXT if is_fs else RESUME_TEXT

        # Calculate individual scores
        t_score = title_score(job_title)
        s_score = skills_score(description)
        e_score = experience_score(job_title, description)
        tf_score = tfidf_score(resume, job_text)

        # Weighted combination
        final = (t_score * 0.30) + (s_score * 0.40) + (e_score * 0.15) + (tf_score * 0.15)

        return round(final, 1)

    logger.info("   Computing multi-signal match scores...")
    df['match_score'] = df.apply(compute_match_score, axis=1)

    df = df.sort_values('match_score', ascending=False)

    # Log top 5 for debugging
    for i, (idx, job) in enumerate(df.head(5).iterrows()):
        logger.info(f"   #{i+1}: {job['title']} @ {job['company']} -> {job['match_score']}%")

    # Log to Jobs (After Dedup) sheet
    for idx, job in df.iterrows():
        log_to_sheet(jobs_sheet, [
            job['date'],
            job['job_id'],
            job['search_name'],
            job['title'],
            job['company'],
            job['location'],
            job['job_type'],
            job['url'],
            job['match_score'],
            'No',
            ''
        ])

    df_filtered = df[df['match_score'] >= MIN_MATCH_SCORE]

    logger.info(f"[OK] MATCHING COMPLETE")
    logger.info(f"   Total jobs: {len(df)}")
    logger.info(f"   Jobs >= {MIN_MATCH_SCORE}%: {len(df_filtered)}")
    if len(df_filtered) > 0:
        logger.info(f"   Top score: {df_filtered.iloc[0]['match_score']:.1f}%")
        logger.info(f"   Average: {df_filtered['match_score'].mean():.1f}%")

    return df_filtered


# ========================================
# OPTIMIZATION HELPER FUNCTIONS
# ========================================

def load_organization_cache_from_sheet():
    """
    Load organization domains from Google Sheet into memory cache
    Called at bot startup
    """
    try:
        logger.info("[INFO] Loading organization cache from sheet...")
        records = organization_cache_sheet.get_all_records()

        loaded = 0
        for record in records:
            company = record.get('Company Name', '').strip()
            domain = record.get('Domain', '').strip()
            status = record.get('Status', '').strip()

            if company:
                cache_key = company.lower().strip()
                if status == 'Found' and domain:
                    ORGANIZATION_CACHE[cache_key] = domain
                    loaded += 1
                elif status == 'Not Found':
                    ORGANIZATION_CACHE[cache_key] = None
                    loaded += 1

        logger.info(f"âœ“ Loaded {loaded} organizations from cache sheet")
        return True
    except Exception as e:
        logger.warning(f"[!] Failed to load organization cache: {e}")
        return False


def save_organization_cache_to_sheet():
    """
    Save all cached organization domains to Google Sheet
    Called at bot end
    """
    try:
        logger.info("[INFO] Saving organization cache to sheet...")

        # Get existing records to avoid duplicates
        existing_records = organization_cache_sheet.get_all_records()
        existing_companies = {r.get('Company Name', '').lower().strip() for r in existing_records}

        # Prepare new rows
        new_rows = []
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for cache_key, domain in ORGANIZATION_CACHE.items():
            # Convert cache key back to proper company name (capitalize words)
            company_name = ' '.join(word.capitalize() for word in cache_key.split())

            # Skip if already in sheet
            if cache_key in existing_companies:
                continue

            if domain:
                new_rows.append([company_name, domain, timestamp, 'Found'])
            else:
                new_rows.append([company_name, '', timestamp, 'Not Found'])

        if new_rows:
            organization_cache_sheet.append_rows(new_rows)
            logger.info(f"âœ“ Saved {len(new_rows)} new organizations to cache sheet")
        else:
            logger.info(f"âœ“ No new organizations to save")

        return True
    except Exception as e:
        logger.error(f"âœ— Failed to save organization cache: {e}")
        return False


def get_organization_domain(company, headers):
    """
    Get organization domain with caching to avoid duplicate API calls
    Returns: (domain, success)
    """
    # Check cache first
    cache_key = company.lower().strip()

    if cache_key in ORGANIZATION_CACHE:
        domain = ORGANIZATION_CACHE[cache_key]
        if domain:
            logger.info(f"         âœ“ Domain from cache: {domain}")
            return domain, True
        else:
            logger.warning(f"         [!] Company not found (cached)")
            return None, False

    # Not in cache - call API (costs 1 credit)
    if apollo_credits_left() < 1:
        logger.warning("         [CREDITS] Budget used up - skipping company lookup")
        return None, False
    org_url = "https://api.apollo.io/api/v1/organizations/search"
    org_data = {"q_organization_name": company, "page": 1, "per_page": 1}

    try:
        resp = requests.post(org_url, headers=headers, json=org_data, timeout=10)
        logger.info(f"         -> Org search: {resp.status_code}")
        if resp.status_code == 200:
            record_apollo_credit("Company lookup", company)

        if resp.status_code == 200:
            orgs = resp.json().get('organizations', [])

            if orgs:
                domain = orgs[0].get('primary_domain', '') or orgs[0].get('website_url', '')
                domain = domain.replace('https://', '').replace('http://', '').split('/')[0]

                # Cache the result (even if empty) and save right away so it's never paid for twice
                ORGANIZATION_CACHE[cache_key] = domain
                try:
                    organization_cache_sheet.append_row([company, domain or '', datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                                         'Found' if domain else 'Not Found'])
                except Exception:
                    pass

                if domain:
                    logger.info(f"         âœ“ Domain: {domain}")
                    return domain, True
                else:
                    logger.warning(f"         [!] No domain found")
                    return None, False
            else:
                # Cache negative result
                ORGANIZATION_CACHE[cache_key] = None
                try:
                    organization_cache_sheet.append_row([company, '', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Not Found'])
                except Exception:
                    pass
                logger.warning(f"         [!] Company not found")
                return None, False
        else:
            logger.warning(f"         [!] Org search failed")
            return None, False

    except Exception as e:
        logger.error(f"         âœ— Org search error: {e}")
        return None, False


def is_already_contacted(name, company):
    """
    Check if this HR person was already contacted at this company
    Checks the Recruiter Contacts sheet
    Returns True if found, False if new
    """
    try:
        records = contacts_sheet.get_all_records()

        name_lower = name.lower().strip()
        company_lower = company.lower().strip()

        for record in records:
            record_name = record.get('Name', '').lower().strip()
            record_company = record.get('Company', '').lower().strip()

            if record_name == name_lower and record_company == company_lower:
                return True

        return False
    except Exception as e:
        logger.debug(f"Error checking contacts: {e}")
        return False  # If error, proceed with enrichment


def is_already_contacted_referral(name, company):
    """
    Check if this referral person was already contacted at this company
    Checks the Referral Contacts sheet
    Returns True if found, False if new
    """
    try:
        records = referral_contacts_sheet.get_all_records()

        name_lower = name.lower().strip()
        company_lower = company.lower().strip()

        for record in records:
            record_name = record.get('Name', '').lower().strip()
            record_company = record.get('Company', '').lower().strip()

            if record_name == name_lower and record_company == company_lower:
                return True

        return False
    except Exception as e:
        logger.debug(f"Error checking referral contacts: {e}")
        return False  # If error, proceed with enrichment


# ========================================
# APOLLO HR FINDER WITH EMAIL ENRICHMENT
# ========================================

def enrich_person_apollo(person_id, company="", person_name=""):
    """
    Enrich a person's full data using Apollo's /people/match endpoint (costs 1 credit).
    Returns full person dict or None.
    """
    if apollo_credits_left() < 1:
        logger.warning("         [CREDITS] Budget used up - not revealing more emails")
        return None
    try:
        headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'X-Api-Key': APOLLO_API_KEY
        }

        enrich_url = "https://api.apollo.io/v1/people/match"
        enrich_data = {"id": person_id}

        resp = requests.post(enrich_url, headers=headers, json=enrich_data, timeout=10)

        if resp.status_code == 200:
            person = resp.json().get('person', {}) or {}
            record_apollo_credit("Email reveal", company or (person.get('organization') or {}).get('name', ''),
                                 person_name or person.get('name', ''))
            return person
        return None

    except Exception as e:
        logger.debug(f"Person enrichment error: {e}")
        return None


def enrich_email_apollo(person_id):
    """
    Enrich a person's email using Apollo's /people/match endpoint
    This reveals the actual email address
    """
    person_data = enrich_person_apollo(person_id)
    if person_data:
        email = person_data.get('email', '')
        if email and not email.endswith('_not_found@domain.com') and not email.endswith('_not_unlocked@domain.com'):
            return email
    return None


def find_recruiters_improved(company, job_location, job_type):
    """
    OPTIMIZED Apollo integration with:
    - Organization domain caching
    - Pre-enrichment filtering
    - Dynamic email counter
    - Increased search results (30 per page)
    """
    try:
        logger.info(f"      -> Finding HRs at {company}...")

        headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'X-Api-Key': APOLLO_API_KEY
        }

        all_contacts = []

        # OPTIMIZATION 1: Use cached organization domain
        company_domain, success = get_organization_domain(company, headers)

        if not success or not company_domain:
            return []

        # STEP 2: Search for people (using api_search endpoint)
        search_location = extract_location_for_apollo(job_location, job_type)
        logger.info(f"         -> Searching HRs in {search_location}...")

        people_url = "https://api.apollo.io/api/v1/mixed_people/api_search"

        people_data = {
            "q_organization_domains_list": [company_domain],
            "person_titles": HR_TITLES,
            "person_locations": [search_location],
            "page": 1,
            "per_page": 30
        }

        resp = requests.post(people_url, headers=headers, json=people_data, timeout=10)

        logger.info(f"         -> People search: {resp.status_code}")

        if resp.status_code != 200:
            try:
                logger.warning(f"         [!] People search error: {resp.text[:200]}")
            except Exception:
                pass

        # Fallback to country-wide if no results
        if resp.status_code != 200 or not resp.json().get('people'):
            if search_location != APOLLO_DEFAULT_LOCATION:
                logger.info(f"         -> Trying {APOLLO_DEFAULT_LOCATION}-wide...")
                people_data["person_locations"] = [APOLLO_DEFAULT_LOCATION]
                resp = requests.post(people_url, headers=headers, json=people_data, timeout=10)

        # STEP 3: Extract and ENRICH contact information
        if resp.status_code == 200:
            try:
                response_json = resp.json()
                people = response_json.get('people', [])

                logger.info(f"         -> Found {len(people)} potential contacts")

                # Filter to people who have email (api_search returns has_email flag)
                candidates = [p for p in people if p.get('has_email', False)]
                if not candidates:
                    candidates = people  # Fallback: try all

                logger.info(f"         -> {len(candidates)} candidates with email available")

                # Dynamic email counter
                valid_emails_found = 0

                for p in candidates:
                    if valid_emails_found >= EMAILS_PER_COMPANY:
                        logger.info(f"         [OK] Target reached: {valid_emails_found} valid emails")
                        break

                    person_id = p.get('id')
                    if not person_id:
                        continue

                    # Enrich person to get full data (api_search returns limited data)
                    logger.debug(f"         -> Enriching {p.get('first_name', '')}...")
                    enriched = enrich_person_apollo(person_id, company, f"{p.get('first_name', '')} {p.get('last_name', '')}".strip())
                    if not enriched:
                        logger.debug(f"         [!] Enrichment failed")
                        continue

                    # Check already contacted with full name
                    name = f"{enriched.get('first_name', '')} {enriched.get('last_name', '')}".strip()
                    if is_already_contacted(name, company):
                        logger.debug(f"         [SKIP] {name} - Already contacted")
                        continue

                    # Check email validity
                    email = enriched.get('email', '')
                    if not email or email.endswith('_not_found@domain.com') or email.endswith(
                            '_not_unlocked@domain.com'):
                        logger.debug(f"         [!] No valid email for {name}")
                        continue

                    # Extract location
                    person_location = ""
                    if enriched.get('city') and enriched.get('state'):
                        person_location = f"{enriched.get('city')}, {enriched.get('state')}"
                    elif enriched.get('city'):
                        person_location = enriched.get('city')
                    elif enriched.get('country'):
                        person_location = enriched.get('country')

                    # Extract LinkedIn
                    linkedin_url = enriched.get('linkedin_url', '')

                    all_contacts.append({
                        'name': name,
                        'first_name': enriched.get('first_name', 'Hiring Team'),
                        'title': enriched.get('title', 'Recruiter'),
                        'email': email,
                        'linkedin': linkedin_url,
                        'location': person_location,
                        'source': 'Apollo',
                        'seniority': enriched.get('seniority', ''),
                        'departments': enriched.get('departments', [])
                    })

                    valid_emails_found += 1
                    logger.debug(f"         -> Valid emails: {valid_emails_found}/{EMAILS_PER_COMPANY}")
            except Exception as e:
                logger.error(f"         âœ— Parse error: {e}")
        else:
            logger.warning(f"         [!] People search failed")

        if all_contacts:
            logger.info(f"         âœ“ Found {len(all_contacts)} contacts with valid emails")
        else:
            logger.warning(f"         [!] No valid contacts found")

        return all_contacts

    except Exception as e:
        logger.error(f"         âœ— Apollo error: {e}")
        log_error("Apollo Error", "find_recruiters_improved", str(e), company)
        return []


# ========================================
# FIND REFERRAL CONTACTS
# ========================================

def find_referral_contacts(company, job_title, job_location, job_type):
    """
    OPTIMIZED referral contact finder with:
    - Organization domain caching
    - Pre-enrichment filtering
    - Dynamic email counter
    - Increased search results (30 per page)
    """
    try:
        logger.info(f"      â†’ Finding referral contacts at {company}...")

        headers = {
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
            'X-Api-Key': APOLLO_API_KEY
        }

        all_contacts = []

        # OPTIMIZATION 1: Use cached organization domain
        company_domain, success = get_organization_domain(company, headers)

        if not success or not company_domain:
            return []

        # STEP 2: Senior product leaders only (job's own title is not added)
        search_roles = list(dict.fromkeys(REFERRAL_ROLES_BASE))

        logger.info(f"         â†’ Searching for roles: {', '.join(search_roles[:3])}...")

        # STEP 3: Search for people (OPTIMIZATION 4: 30 results per page)
        people_url = "https://api.apollo.io/api/v1/mixed_people/api_search"

        people_data = {
            "q_organization_domains_list": [company_domain],
            "person_titles": search_roles,
            "person_locations": [APOLLO_DEFAULT_LOCATION],
            "page": 1,
            "per_page": 30  # OPTIMIZATION 4: Increased from 15 to 30
        }

        resp = requests.post(people_url, headers=headers, json=people_data, timeout=10)

        logger.info(f"         â†’ People search: {resp.status_code}")

        # STEP 4: Extract and ENRICH contact information
        if resp.status_code == 200:
            try:
                response_json = resp.json()
                people = response_json.get('people', [])

                logger.info(f"         â†’ Found {len(people)} potential contacts")

                # Filter to people who have email
                candidates = [p for p in people if p.get('has_email', False)]
                if not candidates:
                    candidates = people

                # Most senior first (CPO/VP/Head/Director > GPM/Principal > Senior PM)
                def _seniority_rank(person):
                    title = (person.get('title') or '').lower()
                    for rank, kw in enumerate(REFERRAL_SENIORITY_ORDER):
                        if kw in title:
                            return rank
                    return len(REFERRAL_SENIORITY_ORDER)
                candidates = [p for p in candidates
                              if _seniority_rank(p) < len(REFERRAL_SENIORITY_ORDER)]  # senior leaders only
                candidates.sort(key=_seniority_rank)

                logger.info(f"         -> {len(candidates)} referral candidates with email")

                # Dynamic email counter
                valid_emails_found = 0

                for p in candidates:
                    if valid_emails_found >= REFERRALS_PER_COMPANY:
                        logger.info(f"         [OK] Target reached: {valid_emails_found} referral emails")
                        break

                    person_id = p.get('id')
                    if not person_id:
                        continue

                    # Enrich person to get full data
                    logger.debug(f"         -> Enriching {p.get('first_name', '')}...")
                    enriched = enrich_person_apollo(person_id, company, f"{p.get('first_name', '')} {p.get('last_name', '')}".strip())
                    if not enriched:
                        logger.debug(f"         [!] Enrichment failed")
                        continue

                    name = f"{enriched.get('first_name', '')} {enriched.get('last_name', '')}".strip()
                    if is_already_contacted_referral(name, company):
                        logger.debug(f"         [SKIP] {name} - Already contacted for referral")
                        continue

                    email = enriched.get('email', '')
                    if not email or email.endswith('_not_found@domain.com') or email.endswith(
                            '_not_unlocked@domain.com'):
                        logger.debug(f"         [!] No valid email for {name}")
                        continue

                    # Extract location
                    person_location = ""
                    if enriched.get('city') and enriched.get('state'):
                        person_location = f"{enriched.get('city')}, {enriched.get('state')}"
                    elif enriched.get('city'):
                        person_location = enriched.get('city')
                    elif enriched.get('country'):
                        person_location = enriched.get('country')

                    linkedin_url = enriched.get('linkedin_url', '')

                    all_contacts.append({
                        'name': name,
                        'first_name': enriched.get('first_name', 'there'),
                        'title': enriched.get('title', ''),
                        'role': enriched.get('title', ''),
                        'email': email,
                        'linkedin': linkedin_url,
                        'location': person_location,
                        'source': 'Apollo'
                    })

                    valid_emails_found += 1
                    logger.debug(f"         -> Valid referral emails: {valid_emails_found}/{REFERRALS_PER_COMPANY}")
            except Exception as e:
                logger.error(f"         âœ— Parse error: {e}")
        else:
            logger.warning(f"         [!] People search failed")

        if all_contacts:
            logger.info(f"         âœ“ Found {len(all_contacts)} referral contacts with valid emails")
        else:
            logger.warning(f"         [!] No valid referral contacts found")

        return all_contacts

    except Exception as e:
        logger.error(f"         âœ— Apollo error: {e}")
        log_error("Apollo Error", "find_referral_contacts", str(e), company)
        return []


def check_referral_contacted(email, company=""):
    """
    Check if we've already contacted this email for a referral at this company
    Returns: (already_contacted: bool, status: str)
    """
    try:
        # Search for exact email match in referral contacts sheet
        all_values = referral_contacts_sheet.get_all_values()

        # Skip header row
        for row in all_values[1:]:
            if len(row) >= 9:  # Make sure row has enough columns
                row_email = row[4].strip().lower() if len(row) > 4 else ""  # Email is column 4 (0-indexed)
                row_company = row[8].strip().lower() if len(row) > 8 else ""  # Company is column 8

                # Check if email matches
                if row_email == email.strip().lower():
                    # If company provided, check if same company
                    if company:
                        if row_company == company.strip().lower():
                            return True, "Previously contacted for referral at this company"
                    else:
                        return True, "Previously contacted for referral"

        return False, "New referral contact"
    except Exception as e:
        logger.debug(f"Error checking referral contact: {e}")
        return False, "Check failed"


# ========================================
# LINKEDIN CONNECTION REQUEST
# ========================================

def send_linkedin_request(first_name, linkedin_url, job_title, company, driver):
    """Send LinkedIn connection request"""
    try:
        if not linkedin_url:
            return False

        if not linkedin_url.startswith('http'):
            linkedin_url = 'https://www.linkedin.com/in/' + linkedin_url.split('/')[-1]

        driver.get(linkedin_url)
        time.sleep(3)

        connect_selectors = [
            "//button[contains(@aria-label, 'Invite')]",
            "//button[contains(., 'Connect')]",
            "//button[contains(@class, 'artdeco-button--primary') and contains(., 'Connect')]",
        ]

        btns = None
        for selector in connect_selectors:
            btns = driver.find_elements(By.XPATH, selector)
            if btns:
                break

        if not btns:
            logger.warning("         [!] Connect button not found")
            return False

        btns[0].click()
        time.sleep(2)

        try:
            add_note_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Add a note')]")
            add_note_btn.click()
            time.sleep(1)

            message_box = driver.find_element(By.ID, "custom-message")
            message = LINKEDIN_MESSAGE.format(
                hr_first_name=first_name,
                job_role=job_title,
                company_name=company
            )
            message_box.send_keys(message)
            time.sleep(1)

            send_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Send now')]")
            send_btn.click()
            time.sleep(2)
            return True
        except:
            try:
                send_btn = driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Send now')]")
                send_btn.click()
                time.sleep(2)
                return True
            except:
                return False

    except Exception as e:
        logger.error(f"         [X]¢â‚¬â„¢ LinkedIn error: {e}")
        return False


# ========================================
# SEND EMAIL
# ========================================

def send_email_with_pdf(hr_name, hr_first_name, hr_email, job_title, company, job_id, match_score, resume_type="frontend"):
    """
    Send email with resume.
    resume_type: "frontend" or "fullstack" - determines which resume and template to use
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Application for {job_title} - {YOUR_NAME}"
        msg['From'] = YOUR_EMAIL
        msg['To'] = hr_email

        # Select template and resume based on job type
        if resume_type == "fullstack":
            html = FULLSTACK_EMAIL_TEMPLATE_HTML.format(
                hr_first_name=hr_first_name,
                job_role=job_title,
                company_name=company
            )
            text = FULLSTACK_EMAIL_TEMPLATE_PLAIN.format(
                hr_first_name=hr_first_name,
                job_role=job_title,
                company_name=company
            )
            resume_file = FULLSTACK_RESUME_FILENAME
            logger.info(f"         [INFO] Using Full Stack resume and template")
        else:
            html = EMAIL_TEMPLATE_HTML.format(
                hr_first_name=hr_first_name,
                job_role=job_title,
                company_name=company
            )
            text = EMAIL_TEMPLATE_PLAIN.format(
                hr_first_name=hr_first_name,
                job_role=job_title,
                company_name=company
            )
            resume_file = RESUME_FILENAME

        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        with open(os.path.join(BASE_DIR, 'resumes', resume_file), 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={resume_file}')
            msg.attach(part)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(YOUR_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        return True

    except Exception as e:
        logger.error(f"         [X]¢â‚¬â„¢ Email error: {e}")
        return False


# ========================================
# SEND REFERRAL EMAIL
# ========================================

def send_referral_email(name, first_name, email, job_title, company, resume_type="frontend"):
    """
    Send referral request email with resume attached.
    resume_type: "frontend" or "fullstack" - determines which resume and template to use
    """
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Referral Request for {job_title} at {company}"
        msg['From'] = YOUR_EMAIL
        msg['To'] = email

        # Select template and resume based on job type
        if resume_type == "fullstack":
            html = FULLSTACK_REFERRAL_EMAIL_HTML.format(
                first_name=first_name,
                job_role=job_title,
                company_name=company
            )
            text = FULLSTACK_REFERRAL_EMAIL_PLAIN.format(
                first_name=first_name,
                job_role=job_title,
                company_name=company
            )
            resume_file = FULLSTACK_RESUME_FILENAME
            logger.info(f"         [INFO] Using Full Stack resume and template for referral")
        else:
            html = REFERRAL_EMAIL_HTML.format(
                first_name=first_name,
                job_role=job_title,
                company_name=company
            )
            text = REFERRAL_EMAIL_PLAIN.format(
                first_name=first_name,
                job_role=job_title,
                company_name=company
            )
            resume_file = RESUME_FILENAME

        msg.attach(MIMEText(text, 'plain'))
        msg.attach(MIMEText(html, 'html'))

        # Attach resume
        with open(os.path.join(BASE_DIR, 'resumes', resume_file), 'rb') as f:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={resume_file}')
            msg.attach(part)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(YOUR_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        return True

    except Exception as e:
        logger.error(f"         [X] Referral email error: {e}")
        return False


# ========================================
# SEND FOLLOW-UP EMAIL (HR)
# ========================================

_MAIL_GUARD = None


def mail_guard():
    global _MAIL_GUARD
    if _MAIL_GUARD is None:
        _MAIL_GUARD = MailGuard(YOUR_EMAIL, GMAIL_APP_PASSWORD, logger)
    return _MAIL_GUARD


def contact_replied(contact_email, since_date):
    """
    "" if it's OK to follow up; otherwise "Yes" (someone replied) or "Bounced" (email
    bounced / was blocked). Fails safe: if the inbox can't be checked, no follow-up.
    """
    try:
        replied, who = mail_guard().has_replied(contact_email, since_date)
        if not replied:
            return ""
        if who == "BOUNCED":
            logger.info(f"      [SKIP] Our email to {contact_email} bounced / was blocked - no follow-up")
            return "Bounced"
        logger.info(f"      [SKIP] Reply already received from {who} - no follow-up")
        return "Yes"
    except Exception as e:
        logger.error(f"      [SKIP] Could not check inbox for {contact_email} ({e}) - not sending, to be safe")
        return "Unchecked"


def replied_companies():
    """Companies where ANY contact (HR or referral) has replied - nobody there gets a follow-up."""
    out = set()
    try:
        for row in contacts_sheet.get_all_values()[1:]:
            if len(row) > 13 and row[13] == "Yes" and row[7]:
                out.add(row[7].strip().lower())
        for row in referral_contacts_sheet.get_all_values()[1:]:
            if len(row) > 12 and row[12] == "Yes" and row[8]:
                out.add(row[8].strip().lower())
    except Exception as e:
        logger.error(f"   [!] Could not read replied companies: {e}")
    return out


def _thread_for(to_email, subject_hint, since_date):
    try:
        thread = mail_guard().find_thread(to_email, subject_hint, since_date)
    except Exception as e:
        logger.error(f"      [X] Could not look up original email thread: {e}")
        thread = None
    if not thread:
        logger.warning(f"      [SKIP] Original email to {to_email} not found - follow-up NOT sent (never start a new thread)")
    return thread


def send_followup_email(hr_name, hr_first_name, hr_email, job_title, company, application_date, followup_num=1):
    """
    Send follow-up email after no response
    followup_num: 1 = First follow-up, 2 = Final follow-up
    """
    try:
        thread = _thread_for(hr_email, "Application for", application_date)
        if not thread:
            return False
        msg = MIMEMultipart('alternative')

        if followup_num == 1:
            html = FOLLOWUP_EMAIL_HTML.format(
                hr_first_name=hr_first_name,
                job_role=job_title,
                company_name=company,
                application_date=application_date
            )
        else:  # Follow-up 2
            html = HR_FOLLOWUP2_EMAIL_HTML.format(
                hr_first_name=hr_first_name,
                job_role=job_title,
                company_name=company
            )

        apply_thread_headers(msg, thread)
        msg['From'] = YOUR_EMAIL
        msg['To'] = hr_email

        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(YOUR_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        return True

    except Exception as e:
        logger.error(f"         [X] Follow-up {followup_num} email error: {e}")
        return False


# ========================================
# NEW v4.4: SEND REFERRAL FOLLOW-UP EMAIL
# ========================================

def send_referral_followup_email(name, first_name, email, job_title, company, email_date, followup_num=1):
    """
    Send follow-up email for referral request
    followup_num: 1 = First follow-up, 2 = Final follow-up
    """
    try:
        thread = _thread_for(email, "Referral Request", email_date)
        if not thread:
            return False
        msg = MIMEMultipart('alternative')

        if followup_num == 1:
            html = REFERRAL_FOLLOWUP1_EMAIL_HTML.format(
                first_name=first_name,
                job_role=job_title,
                company_name=company,
                email_date=email_date
            )
        else:  # Follow-up 2
            html = REFERRAL_FOLLOWUP2_EMAIL_HTML.format(
                first_name=first_name,
                job_role=job_title,
                company_name=company
            )

        apply_thread_headers(msg, thread)
        msg['From'] = YOUR_EMAIL
        msg['To'] = email

        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(YOUR_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        return True

    except Exception as e:
        logger.error(f"         [X] Referral follow-up {followup_num} email error: {e}")
        return False


# ========================================
# CHECK GMAIL FOR REPLIES FROM CONTACTS
# ========================================

def check_gmail_for_replies():
    """
    Connect to Gmail via IMAP, scan inbox for replies from contacts
    who have Response='No', and update the sheet if a reply is found.
    Updates both Contacts and Referral Contacts sheets.
    """
    global _REPLIES_CHECKED
    if globals().get("_REPLIES_CHECKED"):
        return 0  # already scanned this run (each follow-up is re-checked right before sending anyway)
    _REPLIES_CHECKED = True
    logger.info("\n" + "=" * 70)
    logger.info("CHECKING GMAIL INBOX FOR REPLIES FROM CONTACTS")
    logger.info("=" * 70)

    replies_found = 0

    try:
        # Connect to Gmail IMAP
        guard = mail_guard()  # searches ALL Mail (archived/labelled replies too) + same company domain

        # --- Check HR Contacts sheet ---
        try:
            all_contacts = contacts_sheet.get_all_values()
            if len(all_contacts) > 1:
                logger.info(f"   Checking {len(all_contacts) - 1} HR contacts for replies...")
                for i, row in enumerate(all_contacts[1:], start=2):
                    if len(row) < 14:
                        continue
                    email_status = row[10] if len(row) > 10 else ""
                    response = row[13] if len(row) > 13 else ""
                    contact_email = row[3] if len(row) > 3 else ""

                    if email_status != "Sent" or response != "No" or not contact_email:
                        continue

                    try:
                        replied, who = guard.has_replied(contact_email, row[11] if len(row) > 11 else "")
                        if replied:
                            logger.info(f"   [REPLY] {row[1]} ({contact_email}) - {'email bounced/blocked' if who == 'BOUNCED' else 'reply from ' + who}")
                            try:
                                contacts_sheet.update_cell(i, 14, "Bounced" if who == "BOUNCED" else "Yes")  # Column N: Response
                                contacts_sheet.update_cell(i, 15, datetime.now().strftime('%Y-%m-%d'))  # Column O: Response Date
                                replies_found += 1
                            except Exception as e:
                                logger.error(f"   [!] Could not update sheet for {contact_email}: {e}")
                    except Exception as e:
                        logger.debug(f"   Error searching for {contact_email}: {e}")
        except Exception as e:
            logger.error(f"   [X] Error checking HR contacts for replies: {e}")

        # --- Check Referral Contacts sheet ---
        try:
            all_referrals = referral_contacts_sheet.get_all_values()
            if len(all_referrals) > 1:
                logger.info(f"   Checking {len(all_referrals) - 1} referral contacts for replies...")
                for i, row in enumerate(all_referrals[1:], start=2):
                    if len(row) < 13:
                        continue
                    email_status = row[11] if len(row) > 11 else ""
                    response = row[12] if len(row) > 12 else ""
                    contact_email = row[4] if len(row) > 4 else ""

                    if email_status != "Sent" or response != "No" or not contact_email:
                        continue

                    try:
                        replied, who = guard.has_replied(contact_email, row[13] if len(row) > 13 else "")
                        if replied:
                            logger.info(f"   [REPLY] {row[1]} ({contact_email}) - {'email bounced/blocked' if who == 'BOUNCED' else 'reply from ' + who}")
                            try:
                                referral_contacts_sheet.update_cell(i, 13, "Bounced" if who == "BOUNCED" else "Yes")  # Column M: Response
                                referral_contacts_sheet.update_cell(i, 17, datetime.now().strftime('%Y-%m-%d'))  # Column Q: Response Date
                                replies_found += 1
                            except Exception as e:
                                logger.error(f"   [!] Could not update sheet for {contact_email}: {e}")
                    except Exception as e:
                        logger.debug(f"   Error searching for {contact_email}: {e}")
        except Exception as e:
            logger.error(f"   [X] Error checking referral contacts for replies: {e}")

        logger.info(f"   [OK] Reply check complete: {replies_found} new replies found")

    except Exception as e:
        logger.error(f"   [X] Could not connect to Gmail IMAP: {e}")

    return replies_found


# ========================================
# CHECK AND SEND HR FOLLOW-UPS (2-STAGE)
# ========================================

def check_and_send_followups():
    """
    Check Contacts sheet and send follow-up emails where needed (2-stage)

    Follow-up 1 criteria:
    - Email Status = "Sent"
    - Email Date exists
    - Followup Date is empty
    - Response = "No"
    - HR_FOLLOWUP1_DAYS or more days have passed since email was sent

    Follow-up 2 criteria:
    - Email Status = "Sent"
    - Followup Date exists (FU1 was sent)
    - Followup2 Date is empty
    - Response = "No"
    - HR_FOLLOWUP2_DAYS or more days have passed since Follow-up 1
    """
    # First, check Gmail for any replies to update Response columns
    check_gmail_for_replies()

    logger.info("\n" + "=" * 70)
    logger.info("CHECKING FOR HR FOLLOW-UPS NEEDED (2-STAGE)")
    logger.info("=" * 70)
    logger.info(f"   [INFO] Follow-up 1: {HR_FOLLOWUP1_DAYS} days after initial email")
    logger.info(f"   [INFO] Follow-up 2: {HR_FOLLOWUP2_DAYS} days after Follow-up 1")

    try:
        all_contacts = contacts_sheet.get_all_values()

        if len(all_contacts) <= 1:
            logger.info("   [INFO] No contacts in sheet yet")
            return 0

        logger.info(f"   Checking {len(all_contacts) - 1} contacts...")

        followup1_needed = []
        followup2_needed = []

        # Column indices (0-based):
        # 10 = Email Status, 11 = Email Date, 12 = Followup Date
        # 13 = Response, 14 = Response Date, 15 = Followup2 Date

        # Check each contact (skip header row)
        for i, row in enumerate(all_contacts[1:], start=2):
            if len(row) < 14:  # Need at least Response column
                continue

            try:
                email_status = row[10] if len(row) > 10 else ""
                email_date_str = row[11] if len(row) > 11 else ""
                followup_date_str = row[12] if len(row) > 12 else ""
                response = row[13] if len(row) > 13 else ""
                followup2_date_str = row[15] if len(row) > 15 else ""

                # Skip if not sent or has response
                if email_status != "Sent" or response != "No":
                    continue

                # Check for Follow-up 2 first (if FU1 was already sent)
                if followup_date_str and not followup2_date_str:
                    try:
                        followup1_date = datetime.strptime(followup_date_str, '%Y-%m-%d')
                        days_since_fu1 = (datetime.now() - followup1_date).days

                        if days_since_fu1 >= HR_FOLLOWUP2_DAYS:
                            followup2_needed.append({
                                'row_num': i,
                                'name': row[1],
                                'email': row[3],
                                'company': row[7],
                                'job': row[8],
                                'email_date': email_date_str,
                                'followup1_date': followup_date_str,
                                'days_since_fu1': days_since_fu1,
                                'followup_type': 2
                            })
                    except ValueError:
                        pass

                # Check for Follow-up 1 (if no FU1 sent yet)
                elif email_date_str and not followup_date_str:
                    try:
                        email_date = datetime.strptime(email_date_str, '%Y-%m-%d')
                        days_since_email = (datetime.now() - email_date).days

                        if days_since_email >= HR_FOLLOWUP1_DAYS:
                            followup1_needed.append({
                                'row_num': i,
                                'name': row[1],
                                'email': row[3],
                                'company': row[7],
                                'job': row[8],
                                'email_date': email_date_str,
                                'days_since_email': days_since_email,
                                'followup_type': 1
                            })
                    except ValueError:
                        pass

            except Exception as e:
                logger.debug(f"      Error checking row {i}: {e}")
                continue

        logger.info(f"   Found {len(followup1_needed)} contacts needing Follow-up 1")
        logger.info(f"   Found {len(followup2_needed)} contacts needing Follow-up 2")

        total_needed = followup1_needed + followup2_needed

        if len(total_needed) == 0:
            logger.info("   [OK] No HR follow-ups needed at this time")
            return 0

        # Send follow-ups
        followups_sent = 0

        for contact in total_needed:
            try:
                fu_type = contact['followup_type']
                logger.info(f"\n   [{followups_sent + 1}/{len(total_needed)}] Follow-up {fu_type} to {contact['name']}")
                logger.info(f"      Company: {contact['company']}")
                logger.info(f"      Job: {contact['job']}")

                if fu_type == 1:
                    logger.info(f"      Days since initial email: {contact['days_since_email']}")
                else:
                    logger.info(f"      Days since Follow-up 1: {contact['days_since_fu1']}")

                # Extract first name
                first_name = contact['name'].split()[0] if contact['name'] else "there"

                # Never follow up with someone (or a company) that already replied
                if (contact['company'] or '').strip().lower() in replied_companies():
                    logger.info(f"      [SKIP] Someone at {contact['company']} already replied - no follow-up")
                    continue
                status = contact_replied(contact['email'], contact['email_date'])
                if status:
                    try:
                        if status != "Unchecked":
                            contacts_sheet.update_cell(contact['row_num'], 14, status)
                        contacts_sheet.update_cell(contact['row_num'], 15, datetime.now().strftime('%Y-%m-%d'))
                    except Exception:
                        pass
                    continue

                # Send follow-up email
                logger.info(f"      -> Sending Follow-up {fu_type} email...")
                success = send_followup_email(
                    hr_name=contact['name'],
                    hr_first_name=first_name,
                    hr_email=contact['email'],
                    job_title=contact['job'],
                    company=contact['company'],
                    application_date=contact['email_date'],
                    followup_num=fu_type
                )

                if success:
                    logger.info(f"      [OK] Follow-up {fu_type} sent!")

                    # Update appropriate column
                    try:
                        if fu_type == 1:
                            contacts_sheet.update_cell(
                                contact['row_num'],
                                13,  # Column M: Followup Date
                                datetime.now().strftime('%Y-%m-%d')
                            )
                        else:  # Follow-up 2
                            contacts_sheet.update_cell(
                                contact['row_num'],
                                16,  # Column P: Followup2 Date
                                datetime.now().strftime('%Y-%m-%d')
                            )
                        logger.info(f"      [OK] Updated Followup{fu_type} Date in sheet")
                    except Exception as e:
                        logger.error(f"      [!] Could not update sheet: {e}")

                    followups_sent += 1

                    # Add delay between follow-ups
                    if followups_sent < len(total_needed):
                        delay = random.randint(60, 90)
                        logger.info(f"      [WAIT] Waiting {delay}s before next follow-up...")
                        time.sleep(delay)
                else:
                    logger.error(f"      [X] Failed to send Follow-up {fu_type}")

            except Exception as e:
                logger.error(f"      [X] Error sending follow-up: {e}")
                continue

        logger.info(f"\n[OK] HR follow-up check complete: {followups_sent}/{len(total_needed)} sent")
        return followups_sent

    except Exception as e:
        logger.error(f"   [X] Error checking HR follow-ups: {e}")
        return 0


# ========================================
# NEW v4.4: CHECK AND SEND REFERRAL FOLLOW-UPS (2-STAGE)
# ========================================

def check_and_send_referral_followups():
    """
    Check Referral Contacts sheet and send follow-up emails where needed (2-stage)

    Column structure (0-indexed):
    0=Date, 1=Name, 2=Title, 3=Role, 4=Email, 5=LinkedIn, 6=Location,
    7=Source, 8=Company, 9=Job, 10=LinkedIn Status, 11=Email Status, 12=Response,
    13=Email Date, 14=Followup1 Date, 15=Followup2 Date, 16=Response Date

    Follow-up 1 criteria:
    - Email Status = "Sent"
    - Email Date exists
    - Followup1 Date is empty
    - Response = "No"
    - REFERRAL_FOLLOWUP1_DAYS or more days have passed since email was sent

    Follow-up 2 criteria:
    - Email Status = "Sent"
    - Followup1 Date exists
    - Followup2 Date is empty
    - Response = "No"
    - REFERRAL_FOLLOWUP2_DAYS or more days have passed since Follow-up 1
    """
    # First, check Gmail for any replies to update Response columns
    check_gmail_for_replies()

    logger.info("\n" + "=" * 70)
    logger.info("CHECKING FOR REFERRAL FOLLOW-UPS NEEDED (2-STAGE)")
    logger.info("=" * 70)
    logger.info(f"   [INFO] Follow-up 1: {REFERRAL_FOLLOWUP1_DAYS} days after initial email")
    logger.info(f"   [INFO] Follow-up 2: {REFERRAL_FOLLOWUP2_DAYS} days after Follow-up 1")

    try:
        all_contacts = referral_contacts_sheet.get_all_values()

        if len(all_contacts) <= 1:
            logger.info("   [INFO] No referral contacts in sheet yet")
            return 0

        logger.info(f"   Checking {len(all_contacts) - 1} referral contacts...")

        followup1_needed = []
        followup2_needed = []

        # Check each contact (skip header row)
        for i, row in enumerate(all_contacts[1:], start=2):
            if len(row) < 13:  # Need at least Response column
                continue

            try:
                email_status = row[11] if len(row) > 11 else ""
                response = row[12] if len(row) > 12 else ""
                email_date_str = row[13] if len(row) > 13 else ""
                followup1_date_str = row[14] if len(row) > 14 else ""
                followup2_date_str = row[15] if len(row) > 15 else ""

                # Skip if not sent or has response
                if email_status != "Sent" or response != "No":
                    continue

                # Check for Follow-up 2 first (if FU1 was already sent)
                if followup1_date_str and not followup2_date_str:
                    try:
                        followup1_date = datetime.strptime(followup1_date_str, '%Y-%m-%d')
                        days_since_fu1 = (datetime.now() - followup1_date).days

                        if days_since_fu1 >= REFERRAL_FOLLOWUP2_DAYS:
                            followup2_needed.append({
                                'row_num': i,
                                'name': row[1],
                                'email': row[4],
                                'company': row[8],
                                'job': row[9],
                                'email_date': email_date_str,
                                'followup1_date': followup1_date_str,
                                'days_since_fu1': days_since_fu1,
                                'followup_type': 2
                            })
                    except ValueError:
                        pass

                # Check for Follow-up 1 (if no FU1 sent yet)
                elif email_date_str and not followup1_date_str:
                    try:
                        email_date = datetime.strptime(email_date_str, '%Y-%m-%d')
                        days_since_email = (datetime.now() - email_date).days

                        if days_since_email >= REFERRAL_FOLLOWUP1_DAYS:
                            followup1_needed.append({
                                'row_num': i,
                                'name': row[1],
                                'email': row[4],
                                'company': row[8],
                                'job': row[9],
                                'email_date': email_date_str,
                                'days_since_email': days_since_email,
                                'followup_type': 1
                            })
                    except ValueError:
                        pass

            except Exception as e:
                logger.debug(f"      Error checking row {i}: {e}")
                continue

        logger.info(f"   Found {len(followup1_needed)} referral contacts needing Follow-up 1")
        logger.info(f"   Found {len(followup2_needed)} referral contacts needing Follow-up 2")

        total_needed = followup1_needed + followup2_needed

        if len(total_needed) == 0:
            logger.info("   [OK] No referral follow-ups needed at this time")
            return 0

        # Send follow-ups
        followups_sent = 0

        for contact in total_needed:
            try:
                fu_type = contact['followup_type']
                logger.info(
                    f"\n   [{followups_sent + 1}/{len(total_needed)}] Referral Follow-up {fu_type} to {contact['name']}")
                logger.info(f"      Company: {contact['company']}")
                logger.info(f"      Job: {contact['job']}")

                if fu_type == 1:
                    logger.info(f"      Days since initial email: {contact['days_since_email']}")
                else:
                    logger.info(f"      Days since Follow-up 1: {contact['days_since_fu1']}")

                # Extract first name
                first_name = contact['name'].split()[0] if contact['name'] else "there"

                # Never follow up with someone (or a company) that already replied
                if (contact['company'] or '').strip().lower() in replied_companies():
                    logger.info(f"      [SKIP] Someone at {contact['company']} already replied - no follow-up")
                    continue
                status = contact_replied(contact['email'], contact['email_date'])
                if status:
                    try:
                        if status != "Unchecked":
                            referral_contacts_sheet.update_cell(contact['row_num'], 13, status)
                        referral_contacts_sheet.update_cell(contact['row_num'], 17, datetime.now().strftime('%Y-%m-%d'))
                    except Exception:
                        pass
                    continue

                # Send follow-up email
                logger.info(f"      -> Sending Referral Follow-up {fu_type} email...")
                success = send_referral_followup_email(
                    name=contact['name'],
                    first_name=first_name,
                    email=contact['email'],
                    job_title=contact['job'],
                    company=contact['company'],
                    email_date=contact['email_date'],
                    followup_num=fu_type
                )

                if success:
                    logger.info(f"      [OK] Referral Follow-up {fu_type} sent!")

                    # Update appropriate column
                    try:
                        if fu_type == 1:
                            referral_contacts_sheet.update_cell(
                                contact['row_num'],
                                15,  # Column O: Followup1 Date
                                datetime.now().strftime('%Y-%m-%d')
                            )
                        else:  # Follow-up 2
                            referral_contacts_sheet.update_cell(
                                contact['row_num'],
                                16,  # Column P: Followup2 Date
                                datetime.now().strftime('%Y-%m-%d')
                            )
                        logger.info(f"      [OK] Updated Followup{fu_type} Date in sheet")
                    except Exception as e:
                        logger.error(f"      [!] Could not update sheet: {e}")

                    followups_sent += 1

                    # Add delay between follow-ups
                    if followups_sent < len(total_needed):
                        delay = random.randint(60, 90)
                        logger.info(f"      [WAIT] Waiting {delay}s before next follow-up...")
                        time.sleep(delay)
                else:
                    logger.error(f"      [X] Failed to send Referral Follow-up {fu_type}")

            except Exception as e:
                logger.error(f"      [X] Error sending referral follow-up: {e}")
                continue

        logger.info(f"\n[OK] Referral follow-up check complete: {followups_sent}/{len(total_needed)} sent")
        return followups_sent

    except Exception as e:
        logger.error(f"   [X] Error checking referral follow-ups: {e}")
        return 0


# ========================================
# MAIN BOT WORKFLOW
# ========================================

def run_bot():
    """Main bot execution"""
    start_time = datetime.now()

    # OPTIMIZATION: Load organization cache from sheet
    logger.info("\n" + "=" * 70)
    logger.info("INITIALIZING BOT")
    logger.info("=" * 70)
    load_organization_cache_from_sheet()

    stats = {
        'jobs_scraped': 0,
        'duplicates_filtered': 0,
        'already_applied': 0,
        'blacklisted': 0,
        'jobs_matched': 0,
        'top_score': 0,
        'avg_score': 0,
        'linkedin_sent': 0,
        'emails_sent': 0,
        'hr_followups_sent': 0,  # UPDATED v4.4
        'referral_emails_sent': 0,
        'referral_linkedin_logged': 0,
        'referral_followups_sent': 0,  # NEW v4.4
        'errors': 0
    }

    try:
        # STEP 1: Scrape
        df_jobs, blacklisted = pd.DataFrame(), 0
        if USE_SELENIUM_SCRAPER:
            try:
                df_jobs, blacklisted = scrape_all_jobs_selenium()
            except Exception as e:
                logger.error(f"[X] Chrome scraper crashed: {e}")
            if len(df_jobs) == 0:
                logger.warning("[!] Chrome scraper got no jobs - falling back to LinkedIn's public jobs feed")
        if len(df_jobs) == 0:
            df_jobs, blacklisted = scrape_all_jobs()
        extra = []
        for extra_source in (scrape_wellfound_jobs, scrape_job_alert_emails):
            try:
                extra += extra_source()
            except Exception as e:
                logger.error(f"[X] {extra_source.__name__} failed (run continues): {e}")
        if extra:
            df_jobs = pd.concat([df_jobs, pd.DataFrame(extra)], ignore_index=True)
            logger.info(f"[OK] Total jobs from all sources: {len(df_jobs)} ({len(extra)} from Wellfound / alert emails)")
        stats['jobs_scraped'] = len(df_jobs)
        stats['blacklisted'] = blacklisted

        if len(df_jobs) == 0:
            logger.error("[X]¢â‚¬â„¢ No jobs scraped!")
            return

        # STEP 2: Deduplicate
        df_dedup, duplicates = deduplicate_jobs_improved(df_jobs)
        stats['duplicates_filtered'] = duplicates

        if len(df_dedup) == 0:
            logger.error("[X]¢â‚¬â„¢ No unique jobs!")
            return

        # STEP 2.5: Filter Already Applied Jobs
        df_filtered, already_applied = filter_already_applied_jobs(df_dedup)
        stats['already_applied'] = already_applied

        if len(df_filtered) == 0:
            logger.warning("All remaining jobs have already been applied to!")
            return

        # STEP 3: Match
        df_matched = match_jobs(df_filtered)
        stats['jobs_matched'] = len(df_matched)

        if len(df_matched) == 0:
            logger.warning(f"[!] No jobs >= {MIN_MATCH_SCORE}%")
            return

        stats['top_score'] = df_matched.iloc[0]['match_score']
        stats['avg_score'] = df_matched['match_score'].mean()

        df_matched = select_jobs_for_outreach(df_matched)
        if len(df_matched) == 0:
            logger.warning("[!] No jobs pass the PM / experience filters")

        # STEP 4: Apply
        logger.info("\n" + "=" * 70)
        logger.info(f"STEP 3: OUTREACH (max {TOP_JOBS_TO_APPLY} jobs, max {MAX_APOLLO_CREDITS_PER_RUN} Apollo credits)")
        logger.info("=" * 70)

        # No LinkedIn driver needed - handled separately
        li_driver = None

        # Never email a company twice: email domains already used in earlier runs / earlier jobs this run
        emailed_domains = previously_emailed_domains()

        for idx, (_, job) in enumerate(df_matched.head(TOP_JOBS_TO_APPLY).iterrows()):
            if apollo_credits_left() < 1:
                logger.info(f"\n[CREDITS] Reached {MAX_APOLLO_CREDITS_PER_RUN} Apollo credits - stopping outreach for this run")
                break
            try:
                # Determine resume type based on job title
                _, resume_type = get_resume_for_job(job['title'])
                
                logger.info(f"\n[{idx + 1}/{TOP_JOBS_TO_APPLY}] {job['title']} @ {job['company']}")
                logger.info(f"   Match: {job['match_score']:.1f}% | Location: {job['location']}")
                if resume_type == "fullstack":
                    logger.info(f"   [FULLSTACK] Using Full Stack resume and templates")

                # Company's email domain first (cached = free, else 1 credit) - skip before paying for any email reveal
                dom, _ok = get_organization_domain(job['company'], {'Content-Type': 'application/json',
                                                                     'Cache-Control': 'no-cache',
                                                                     'X-Api-Key': APOLLO_API_KEY})
                if dom and dom.lower() in emailed_domains:
                    logger.info(f"      [SKIP] Already emailed this company before ({dom} / {emailed_domains[dom.lower()]}) - not contacting again")
                    continue

                logger.info(f"   -> Finding recruiters...")
                contacts = find_recruiters_improved(
                    job['company'],
                    job['location'],
                    job['job_type']
                )

                if not contacts:
                    logger.info("      [!] No contacts found")
                    stats['errors'] += 1
                    continue

                job_domains = {c['email'].split('@')[-1].lower() for c in contacts if '@' in (c.get('email') or '')}
                job_domains -= FREE_EMAIL_DOMAINS
                clash = [d for d in job_domains if d in emailed_domains]
                if clash:
                    logger.info(f"      [SKIP] Already emailed this company before ({clash[0]} / {emailed_domains[clash[0]]}) - not contacting again")
                    continue
                for d in job_domains:
                    emailed_domains[d] = job['company']

                for contact_idx, contact in enumerate(contacts[:EMAILS_PER_COMPANY]):
                    # Check if contacted
                    already_contacted, contact_status = check_contacted(contact['email'], job['company'])

                    if already_contacted:
                        logger.info(f"      [!] {contact_status}: {contact['name']}")

                    email_success = False
                    li_status = "Not Sent"
                    email_status = "Not Sent"

                    # Only send email if not already contacted
                    if not already_contacted:
                        # Log to LinkedIn Contacts sheet for separate LinkedIn bot
                        if contact.get('linkedin'):
                            logger.info(f"      -> Logging LinkedIn contact: {contact['first_name']}")
                            log_to_sheet(linkedin_contacts_sheet, [
                                datetime.now().strftime('%Y-%m-%d'),
                                contact['name'],
                                contact['title'],
                                contact.get('linkedin', ''),
                                job['company'],
                                job['title'],
                                contact.get('location', ''),
                                '0',  # Status: 0 = Not contacted
                                f"Job Match: {job['match_score']:.1f}%"
                            ])
                            li_status = "Logged for LinkedIn Bot"
                            stats['linkedin_sent'] += 1  # Count as logged

                        # Send email
                        logger.info(f"      -> Email to {contact['first_name']}...")
                        email_success = send_email_with_pdf(
                            contact['name'],
                            contact['first_name'],
                            contact['email'],
                            job['title'],
                            job['company'],
                            job['url_id'],
                            job['match_score'],
                            resume_type
                        )

                        if email_success:
                            logger.info(f"        [OK]Ã…[OK] Sent!")
                            stats['emails_sent'] += 1
                            email_status = "Sent"
                        else:
                            stats['errors'] += 1
                            email_status = "Failed"
                    else:
                        li_status = "Already Contacted"
                        email_status = "Already Contacted"

                    # Always log to sheets
                    rec1 = contacts[0] if len(contacts) > 0 else {}
                    rec2 = contacts[1] if len(contacts) > 1 else {}
                    rec3 = contacts[2] if len(contacts) > 2 else {}

                    # Log to Applications
                    log_to_sheet(applications_sheet, [
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        datetime.now().strftime('%Y-%m-%d'),
                        job['job_id'],
                        job['title'],
                        job['company'],
                        job['location'],
                        job['job_type'],
                        job['url'],
                        job['match_score'],
                        job['search_name'],
                        rec1.get('name', ''),
                        rec1.get('email', ''),
                        rec1.get('linkedin', ''),
                        rec2.get('name', ''),
                        rec2.get('email', ''),
                        rec3.get('name', ''),
                        rec3.get('email', ''),
                        '',  # hiring team
                        '',  # hiring email
                        li_status,  # LinkedIn Status
                        email_status,  # Email Status
                        datetime.now().strftime('%Y-%m-%d') if email_success else '',
                        '',  # LinkedIn date (handled separately now)
                        '',  # followup
                        'No',
                        '',
                        ''
                    ])

                    # Log to Contacts
                    log_to_sheet(contacts_sheet, [
                        datetime.now().strftime('%Y-%m-%d'),
                        contact['name'],
                        contact['title'],
                        contact['email'],
                        contact.get('linkedin', ''),
                        contact.get('location', ''),
                        contact.get('source', 'Apollo'),
                        job['company'],
                        job['title'],
                        li_status,  # LinkedIn Status
                        email_status,  # Email Status
                        datetime.now().strftime('%Y-%m-%d') if email_success else '',  # Email Date
                        '',  # Followup Date (empty initially)
                        'No',  # Response
                        '',  # Response Date (empty initially)
                        ''  # Followup2 Date (NEW v4.4 - empty initially)
                    ])

                    # Update jobs sheet
                    if email_success:
                        try:
                            cell = jobs_sheet.find(job['job_id'])
                            if cell:
                                jobs_sheet.update_cell(cell.row, 10, 'Yes')
                                jobs_sheet.update_cell(cell.row, 11, datetime.now().strftime('%Y-%m-%d'))
                        except:
                            pass

                    if not already_contacted:
                        random_delay(10, 20)

                # ========================================
                # REFERRAL OUTREACH
                # ========================================

                logger.info(f"   -> Finding referral contacts...")
                referral_contacts = find_referral_contacts(
                    job['company'],
                    job['title'],  # Pass actual job title for dynamic role
                    job['location'],
                    job['job_type']
                )

                referral_emails_sent = 0
                referral_linkedin_logged = 0

                if referral_contacts:
                    logger.info(f"      [OK] Found {len(referral_contacts)} referral contacts")

                    for ref_idx, ref_contact in enumerate(referral_contacts):
                        # Check if already contacted for referral
                        already_ref_contacted, ref_status = check_referral_contacted(
                            ref_contact['email'],
                            job['company']
                        )

                        if already_ref_contacted:
                            logger.info(f"      [!] {ref_status}: {ref_contact['name']}")
                            continue

                        ref_email_success = False
                        ref_li_status = "Not Sent"
                        ref_email_status = "Not Sent"

                        # Log to LinkedIn Referral Contacts sheet
                        if ref_contact.get('linkedin'):
                            logger.info(
                                f"      -> Logging LinkedIn referral contact: {ref_contact['first_name']}")
                            log_to_sheet(linkedin_referral_contacts_sheet, [
                                datetime.now().strftime('%Y-%m-%d'),
                                ref_contact['name'],
                                ref_contact['title'],
                                ref_contact.get('role', ''),
                                ref_contact.get('linkedin', ''),
                                job['company'],
                                job['title'],
                                ref_contact.get('location', ''),
                                '0',  # Status: 0 = Not contacted
                                f"Referral for {job['title']}"
                            ])
                            ref_li_status = "Logged for LinkedIn Bot"
                            referral_linkedin_logged += 1

                        # Send referral email
                        logger.info(f"      -> Referral email to {ref_contact['first_name']}...")
                        ref_email_success = send_referral_email(
                            ref_contact['name'],
                            ref_contact['first_name'],
                            ref_contact['email'],
                            job['title'],
                            job['company'],
                            resume_type
                        )

                        if ref_email_success:
                            logger.info(f"        [OK] Referral email sent!")
                            referral_emails_sent += 1
                            ref_email_status = "Sent"
                        else:
                            stats['errors'] += 1
                            ref_email_status = "Failed"

                        # Log to Referral Contacts sheet (UPDATED v4.4: Added Email Date and follow-up columns)
                        log_to_sheet(referral_contacts_sheet, [
                            datetime.now().strftime('%Y-%m-%d'),
                            ref_contact['name'],
                            ref_contact['title'],
                            ref_contact.get('role', ''),
                            ref_contact['email'],
                            ref_contact.get('linkedin', ''),
                            ref_contact.get('location', ''),
                            ref_contact.get('source', 'Apollo'),
                            job['company'],
                            job['title'],
                            ref_li_status,
                            ref_email_status,
                            'No',  # Response
                            datetime.now().strftime('%Y-%m-%d') if ref_email_success else '',  # Email Date
                            '',  # Followup1 Date (empty initially)
                            '',  # Followup2 Date (empty initially)
                            ''  # Response Date (empty initially)
                        ])

                        # Small delay between referral emails
                        if ref_email_success:
                            random_delay(5, 10)

                    # Log to Referral Applications sheet
                    ref1 = referral_contacts[0] if len(referral_contacts) > 0 else {}
                    ref2 = referral_contacts[1] if len(referral_contacts) > 1 else {}
                    ref3 = referral_contacts[2] if len(referral_contacts) > 2 else {}
                    ref4 = referral_contacts[3] if len(referral_contacts) > 3 else {}
                    ref5 = referral_contacts[4] if len(referral_contacts) > 4 else {}

                    log_to_sheet(referral_applications_sheet, [
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        datetime.now().strftime('%Y-%m-%d'),
                        job['job_id'],
                        job['title'],
                        job['company'],
                        job['location'],
                        job['job_type'],
                        job['url'],
                        job['match_score'],
                        job['search_name'],
                        ref1.get('name', ''),
                        ref1.get('email', ''),
                        ref1.get('linkedin', ''),
                        ref2.get('name', ''),
                        ref2.get('email', ''),
                        ref3.get('name', ''),
                        ref3.get('email', ''),
                        ref4.get('name', ''),
                        ref4.get('email', ''),
                        ref5.get('name', ''),
                        ref5.get('email', ''),
                        str(referral_emails_sent),
                        str(referral_linkedin_logged),
                        f"Match: {job['match_score']:.1f}%"
                    ])

                    # Update stats
                    stats['referral_emails_sent'] += referral_emails_sent
                    stats['referral_linkedin_logged'] += referral_linkedin_logged

                    logger.info(
                        f"      [OK] Referral outreach complete: {referral_emails_sent} emails sent")
                else:
                    logger.info(f"      [!] No referral contacts found")

            except Exception as e:
                logger.error(f"   [X]¢â‚¬â„¢ Error: {e}")
                log_error("Application Error", "run_bot", str(e), f"{job['title']} @ {job['company']}")
                stats['errors'] += 1
                continue

    except Exception as e:
        logger.error(f"[X]¢â‚¬â„¢ CRITICAL ERROR: {e}")
        log_error("Critical", "run_bot", str(e), "Main Pipeline")
        stats['errors'] += 1

    # STEP 5: Check and Send HR Follow-ups
    try:
        followups_sent = check_and_send_followups()
        stats['hr_followups_sent'] = followups_sent
    except Exception as e:
        logger.error(f"[X] Error in HR follow-up module: {e}")
        stats['hr_followups_sent'] = 0

    # STEP 6: Check and Send Referral Follow-ups (NEW v4.4)
    try:
        referral_followups_sent = check_and_send_referral_followups()
        stats['referral_followups_sent'] = referral_followups_sent
    except Exception as e:
        logger.error(f"[X] Error in referral follow-up module: {e}")
        stats['referral_followups_sent'] = 0

    # Log daily stats (UPDATED v4.4: Separate HR and Referral follow-ups)
    try:
        log_to_sheet(daily_sheet, [
            datetime.now().strftime('%Y-%m-%d'),
            stats['jobs_scraped'],
            stats.get('duplicates_filtered', 0),
            stats.get('blacklisted', 0),
            stats['jobs_scraped'] - stats.get('duplicates_filtered', 0) - stats.get('blacklisted', 0),
            stats['jobs_matched'],
            round(stats['top_score'], 1),
            round(stats['avg_score'], 1),
            stats['linkedin_sent'],
            stats['emails_sent'],
            stats.get('referral_emails_sent', 0),
            stats.get('referral_linkedin_logged', 0),
            stats.get('hr_followups_sent', 0),
            stats.get('referral_followups_sent', 0),
            stats['errors']
        ])
    except:
        pass

    # OPTIMIZATION: Save organization cache to sheet
    save_organization_cache_to_sheet()

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds() / 60

    logger.info("\n" + "=" * 70)
    logger.info("[OK] BOT COMPLETED!")
    logger.info("=" * 70)
    logger.info(f"[INFO] STATISTICS:")
    logger.info(f"   * Jobs scraped: {stats['jobs_scraped']}")
    logger.info(f"   * Blacklisted: {stats.get('blacklisted', 0)}")
    logger.info(f"   * Duplicates: {stats.get('duplicates_filtered', 0)}")
    logger.info(f"   * Already applied: {stats.get('already_applied', 0)}")
    logger.info(
        f"   * New jobs: {stats['jobs_scraped'] - stats.get('duplicates_filtered', 0) - stats.get('blacklisted', 0) - stats.get('already_applied', 0)}")
    logger.info(f"   * Jobs matched: {stats['jobs_matched']}")
    logger.info(f"   * Top score: {stats['top_score']:.1f}%")
    logger.info(f"   * Average: {stats['avg_score']:.1f}%")
    logger.info(f"   * LinkedIn contacts logged: {stats['linkedin_sent']}")
    logger.info(f"   * Emails sent: {stats['emails_sent']}")
    logger.info(f"   * HR follow-ups sent: {stats.get('hr_followups_sent', 0)}")
    logger.info(f"   * Referral emails sent: {stats.get('referral_emails_sent', 0)}")
    logger.info(f"   * Referral LinkedIn logged: {stats.get('referral_linkedin_logged', 0)}")
    logger.info(f"   * Referral follow-ups sent: {stats.get('referral_followups_sent', 0)}")
    logger.info(f"   * Errors: {stats['errors']}")
    logger.info(f"   * Duration: {duration:.1f} min")
    logger.info("\n[INFO] Dashboard: run  venv/bin/python dashboard.py  ->  http://127.0.0.1:8050")
    logger.info(f"\nCompleted: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)


# ========================================
# RUN THE BOT
# ========================================

if __name__ == "__main__":
    try:
        run_bot()
    except KeyboardInterrupt:
        logger.info("\n\n[!] Bot stopped by user")
    except Exception as e:
        logger.error(f"\n\n[X]¢â‚¬â„¢ Error: {e}")
        import traceback

        traceback.print_exc()