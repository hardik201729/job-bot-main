import os
from dotenv import load_dotenv

load_dotenv()

# ========================================
# CREDENTIALS (loaded from .env)
# ========================================

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

YOUR_EMAIL = os.getenv("YOUR_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")

YOUR_NAME = os.getenv("YOUR_NAME")
YOUR_PHONE = os.getenv("YOUR_PHONE")
YOUR_LINKEDIN = os.getenv("YOUR_LINKEDIN")

RESUME_DRIVE_FILE_ID = os.getenv("RESUME_DRIVE_FILE_ID")
RESUME_FILENAME = os.getenv("RESUME_FILENAME", "Hardik_PMb.pdf")

# Full Stack Resume (for full stack developer jobs)
FULLSTACK_RESUME_DRIVE_FILE_ID = os.getenv("FULLSTACK_RESUME_DRIVE_FILE_ID")
FULLSTACK_RESUME_FILENAME = os.getenv("FULLSTACK_RESUME_FILENAME") or RESUME_FILENAME

# Keywords to detect full stack jobs
# Single PM resume -> no alternate resume selection
FULLSTACK_KEYWORDS = [
]

# ========================================
# SKILLS & MATCHING CONFIGURATION
# ========================================

# Your core skills (used for keyword-based job matching)
MY_SKILLS = [
    "product management", "product manager", "product owner",
    "prd", "prds", "product requirement", "roadmap", "product roadmap",
    "product discovery", "user research", "user interviews", "customer interviews",
    "a/b test", "experimentation", "product analytics", "metrics", "kpi", "okr",
    "funnel", "conversion", "retention", "engagement", "churn", "growth",
    "stakeholder", "cross-functional", "go-to-market", "gtm", "launch",
    "agile", "scrum", "jira", "sprint", "backlog",
    "sql", "python", "data-driven", "analytics", "google analytics", "mixpanel", "amplitude", "clevertap",
    "figma", "wireframe", "prototype", "prototyping", "ux",
    "llm", "llms", "generative ai", "genai", "gen ai", "ai product", "agentic", "ai agents",
    "prompt engineering", "conversational ai", "chatbot", "machine learning",
    "b2b", "b2c", "saas", "edtech", "fintech", "risk", "fraud", "compliance",
    "0 to 1", "zero to one",
]

# Title aliases - titles that are equivalent to your target roles
TITLE_ALIASES = {
    "product": ["product manager", "associate product manager", "apm",
                "product owner", "technical product manager", "ai product manager",
                "growth product manager", "product analyst", "product specialist",
                "product associate", "products associate", "senior associate product manager",
                "product manager i", "product manager 1", "product manager - ai",
                "senior product manager"],
}

# Experience level keywords (for scoring)
SENIOR_KEYWORDS = ["senior", "sr.", "sr ", "lead", "principal", "staff", "group product", "director", "head of", "vp ", "vice president", "chief"]
JUNIOR_KEYWORDS = ["intern", "fresher", "trainee", "apprentice", "graduate", "entry level", "entry-level", "associate"]
MY_EXPERIENCE_YEARS = 3  # Your experience in years

# ========================================
# JOB SEARCH CONFIGURATION
# ========================================

JOB_ROLES = [
    {"role": "Associate Product Manager", "local_jobs": 80, "remote_jobs": 20},
    {"role": "Product Manager", "local_jobs": 80, "remote_jobs": 20},
    {"role": "AI Product Manager", "local_jobs": 40, "remote_jobs": 20},
    # {"role": "Technical Product Manager", "local_jobs": 40, "remote_jobs": 20},
    # {"role": "Growth Product Manager", "local_jobs": 40, "remote_jobs": 20},
    # {"role": "Product Owner", "local_jobs": 40, "remote_jobs": 20},
]

LOCAL_LOCATIONS = ["Delhi, India", "Gurugram, India", "Noida, India", "Bengaluru, India", "Pune, India", "Hyderabad, India"]
REMOTE_LOCATION = "India"
# Remote searches run once per entry: remote jobs in India + remote jobs worldwide
REMOTE_LOCATIONS = ["India", "Worldwide"]

# Apollo location mapping (city keyword -> Apollo search location)
APOLLO_LOCATION_MAP = {
    'Mumbai': "Mumbai, India",
    'Pune': "Pune, India",
    'Bengaluru': "Bengaluru, India",
    'Bangalore': "Bengaluru, India",
    'Delhi': "Delhi, India",
    'NCR': "Delhi, India",
    'Hyderabad': "Hyderabad, India",
    'Chennai': "Chennai, India",
    'Kolkata': "Kolkata, India",
    'Noida': "Delhi, India",
    'Gurugram': "Delhi, India",
    'Gurgaon': "Delhi, India",
}
APOLLO_DEFAULT_LOCATION = "India"

# Time filter for job postings
# Change this based on how frequently you run the bot:
#   - "24_hours" = Jobs posted in last 24 hours (for daily runs)
#   - "7_days" = Jobs posted in last 7 days (for weekly runs)
JOB_TIME_FILTER = "7_days"  # <<< CHANGE THIS WHEN NEEDED

# ========================================
# COMPANY BLACKLIST
# ========================================

BLACKLIST_COMPANIES = [
    # Current employer (don't apply here)
    "ZIGRAM",
    "Zigram Data Technologies",

    # Spam / staffing / irrelevant (kept from original list)
    "GoodSpace AI",
    "GoodSpace",
    "Turing",
    "Somewhere",
    "Hancod",
    "Miamin Systems",
    "Skillzenloop",
    "Scoutit",
    "DataLendly",
    "Interview Kickstart",
    "intern",
    "fresher",
]

BLACKLIST_PATTERNS = [
    # substring match on company name - avoid short words (e.g. "turing" matches "Manufacturing")
    "zigram",
    "goodspace",
    "hancod",
    "miamin systems",
    "skillzenloop",
    "scoutit",
    "datalendly",
    "interview kickstart",
]

# ========================================
# APPLICATION SETTINGS
# ========================================

TOP_JOBS_TO_APPLY = 60  # Max jobs to outreach per run (start small, raise later)
MIN_MATCH_SCORE = 50

EMAILS_PER_COMPANY = 2  # HR / recruiter emails per job
LINKEDIN_REQUESTS_PER_COMPANY = 1
MAX_LINKEDIN_REQUESTS_PER_DAY = 30

# Follow-up email settings
# ========================================
# HR FOLLOW-UP TIMING
# ========================================
# Follow-up 1: Days after initial email
# Follow-up 2: Days after Follow-up 1
HR_FOLLOWUP1_DAYS = 1  # 1 day after initial email
HR_FOLLOWUP2_DAYS = 3  # 3 days after Follow-up 1

# ========================================
# REFERRAL FOLLOW-UP TIMING
# ========================================
# Follow-up 1: Days after initial referral email
# Follow-up 2: Days after Follow-up 1
REFERRAL_FOLLOWUP1_DAYS = 1  # 1 days after initial email
REFERRAL_FOLLOWUP2_DAYS = 3  # 3 days after Follow-up 1

# Legacy variable (kept for backward compatibility)
FOLLOWUP_DAYS = HR_FOLLOWUP1_DAYS

# Random delays (seconds)
MIN_DELAY = 60
MAX_DELAY = 90

# Auto re-login timeout (seconds)
AUTO_RELOGIN_TIMEOUT = 1800  # 30 minutes

# ========================================
# HR TITLES TO SEARCH
# ========================================

HR_TITLES = [
    "Recruiter", "Technical Recruiter", "Senior Recruiter", "Lead Recruiter",
    "Talent Acquisition", "Talent Acquisition Specialist",
    "Senior Talent Acquisition", "Lead Talent Acquisition",
    "HR Manager", "Senior HR Manager", "HR Business Partner", "HRBP",
    "Hiring Manager",
    "People Operations", "People Partner", "Talent Partner",
    "Director of Talent", "Head of Talent", "Director of Hiring"
]

# ========================================
# REFERRAL OUTREACH SETTINGS
# ========================================

REFERRALS_PER_COMPANY = 2  # Senior product leaders per job

# Referral contacts: only senior product leaders (the job's own title is NOT added).
# Candidates are ranked by seniority, so the most senior people get emailed first.
REFERRAL_ROLES_BASE = [
    "Senior Product Manager",
    "Group Product Manager",
    "Principal Product Manager",
    "Lead Product Manager",
    "Product Lead",
    "Head of Product",
    "Director of Product",
    "Product Director",
    "Senior Director of Product",
    "VP Product",
    "Vice President Product",
    "Chief Product Officer",
]

# Seniority ranking used to order referral candidates (first match wins, lower = more senior)
REFERRAL_SENIORITY_ORDER = [
    "chief product", "cpo", "vp", "vice president", "head of product", "head - product",
    "head, product", "director", "group product", "principal product", "lead product",
    "product lead", "senior product", "sr. product", "sr product",
]

# Google Sheets name
SHEETS_NAME = os.getenv("SHEETS_NAME", "Hardik Job Applications Tracker 2026")

# ========================================
# APOLLO CREDIT BUDGET
# ========================================
# Hard cap per run: the bot stops contacting people once this many credits are spent.
# Counted: 1 credit per company lookup (organizations/search) + 1 per email reveal (people/match).
# People search itself is free.
MAX_APOLLO_CREDITS_PER_RUN = 60

# Your Apollo credit balance when tracking started (update it if you buy/renew credits).
# Dashboard shows: remaining = this number - credits logged in the "Apollo Credits" table.
APOLLO_TOTAL_CREDITS = 1600

# ========================================
# WHICH JOBS GET OUTREACH (priority order)
# ========================================
# Title must contain one of these...
TARGET_TITLE_KEYWORDS = ["associate product manager", "ai product manager", "product manager", "apm"]
# ...and none of these (no senior roles, interns or adjacent roles)
EXCLUDE_TITLE_KEYWORDS = ["senior", "sr.", "sr ", "lead", "principal", "staff", "head", "director",
                          "vp", "vice president", "chief", "group product", "intern", "trainee"]
# Experience asked in the job description:
#   tier 1 = up to 3 years (or not mentioned) -> contacted first, best match score first
#   tier 2 = exactly 4 years                  -> only if tier 1 runs out before the credit cap
#   more than 4 years                          -> skipped
MAX_EXPERIENCE_TIER1 = 3
MAX_EXPERIENCE_TIER2 = 3   # 16 Nov: hard cap - anything asking more than 3 years is skipped

# Only these three roles (16 Nov). The words before "product manager" must be one of these,
# e.g. "Product Manager - Payments" / "AI Product Manager" pass, "Technical/Growth Product Manager" don't.
ALLOWED_PM_PREFIXES = ["", "associate", "ai", "a.i.", "ai/ml", "genai", "gen ai", "generative ai"]

# LinkedIn via logged-in Chrome (data/chrome-profile keeps the session). Real Remote label,
# more results. Falls back to the public jobs feed automatically if login / Chrome fails.
USE_SELENIUM_SCRAPER = True
LINKEDIN_GEO_IDS = {"delhi, india": "106187582", "gurugram, india": "106442238", "noida, india": "104869687",
                    "bengaluru, india": "105214831", "pune, india": "112419263", "hyderabad, india": "105556991",
                    "india": "102713980", "worldwide": "92000000"}

# ========================================
# EXTRA JOB SOURCES (16 Nov)
# ========================================
# Wellfound public role pages (allowed by wellfound.com/robots.txt, no login)
WELLFOUND_ENABLED = True
WELLFOUND_ROLES = ["product-manager", "associate-product-manager", "ai-product-manager"]
WELLFOUND_LOCATIONS = ["india", "bangalore", "delhi", "gurgaon", "noida", "pune", "hyderabad", "mumbai"]
WELLFOUND_INCLUDE_REMOTE = True   # remote roles that accept India / worldwide
# Job-alert emails in Gmail (read-only): Naukri, Indeed and LinkedIn block automated search,
# so set up daily alerts on those sites and the bot reads them from your inbox.
JOB_ALERT_EMAILS_ENABLED = True
JOB_ALERT_LOOKBACK_DAYS = 3
