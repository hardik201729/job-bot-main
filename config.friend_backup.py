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
RESUME_FILENAME = os.getenv("RESUME_FILENAME", "Aditya_Patil_Resume.pdf")

# Full Stack Resume (for full stack developer jobs)
FULLSTACK_RESUME_DRIVE_FILE_ID = os.getenv("FULLSTACK_RESUME_DRIVE_FILE_ID")
FULLSTACK_RESUME_FILENAME = os.getenv("FULLSTACK_RESUME_FILENAME", "AdityaPatil_FullStack_Resume.pdf")

# Keywords to detect full stack jobs
FULLSTACK_KEYWORDS = [
    "full stack", "fullstack", "full-stack",
    "mern", "mean", "backend", "back end", "back-end",
    "node.js", "nodejs", "express", "mongodb",
    "python developer", "django", "flask",
    "java developer", "spring boot",
    "full stack engineer", "fullstack engineer", "sde", "sde-1"
]

# ========================================
# SKILLS & MATCHING CONFIGURATION
# ========================================

# Your core skills (used for keyword-based job matching)
MY_SKILLS = [
    "react", "reactjs", "react.js",
    "next", "nextjs", "next.js",
    "javascript", "typescript",
    "html", "css", "sass", "scss", "tailwind", "tailwindcss",
    "redux", "zustand", "context api",
    "node", "nodejs", "node.js",
    "express", "expressjs", "express.js",
    "mongodb", "mongoose",
    "rest api", "restful", "graphql",
    "git", "github",
    "webpack", "vite",
    "jest", "testing",
    "responsive design", "responsive",
    "material ui", "mui",
    "figma",
    "agile", "scrum",
    "docker",
    "vercel", "netlify",
    "python",
    "sql", "postgresql", "mysql",
    "firebase",
    "socket.io", "websocket",
]

# Title aliases - titles that are equivalent to your target roles
TITLE_ALIASES = {
    "frontend": ["frontend developer", "front end developer", "front-end developer",
                  "frontend engineer", "front end engineer", "front-end engineer",
                  "react developer", "react engineer", "reactjs developer",
                  "ui developer", "ui engineer", "web developer",
                  "javascript developer", "js developer", "typescript developer"],
    "fullstack": ["full stack developer", "fullstack developer", "full-stack developer",
                   "full stack engineer", "fullstack engineer", "full-stack engineer",
                   "mern developer", "mern stack developer", "mean developer",
                   "software development engineer", "sde", "sde-1", "sde 1",
                   "software engineer", "software developer", "web developer"],
}

# Experience level keywords (for scoring)
SENIOR_KEYWORDS = ["senior", "sr.", "sr ", "lead", "principal", "staff", "architect", "director", "manager", "head of", "vp ", "vice president"]
JUNIOR_KEYWORDS = ["intern", "fresher", "trainee", "apprentice", "graduate", "entry level", "entry-level"]
MY_EXPERIENCE_YEARS = 2  # Your experience in years

# ========================================
# JOB SEARCH CONFIGURATION
# ========================================

JOB_ROLES = [
    {"role": "Frontend Developer", "local_jobs": 160, "remote_jobs": 80},
    {"role": "Frontend Engineer", "local_jobs": 80, "remote_jobs": 20},
    {"role": "React Developer", "local_jobs": 80, "remote_jobs": 20},
    # {"role": "UI Developer", "local_jobs": 20, "remote_jobs": 20},
    # {"role": "UI Engineer", "local_jobs": 20, "remote_jobs": 20},
    # {"role": "Web Developer", "local_jobs": 20, "remote_jobs": 20},
    # {"role": "JavaScript Developer", "local_jobs": 20, "remote_jobs": 20},
    # {"role": "Software Development Engineer", "local_jobs": 20, "remote_jobs": 20},
    # {"role": "Software Engineer", "local_jobs": 20, "remote_jobs": 20},
]

LOCAL_LOCATIONS = ["Bengaluru, India", "Pune, India", "Delhi, India", "Hyderabad, India"]
REMOTE_LOCATION = "India"

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
    "Parallel Minds",
    "Parallel Minds Technologies",
    "Parallel Minds Technologies Private Limited",
    "Parallel Minds Technologies Private Limited India",
    "Pi Labs",
    "Pi Labs Technologies",
    "Pi Labs Technologies Private Limited",
    "Pi Labs Technologies Private Limited India",
    "Oniber",
    "Oniber Technologies",
    "Oniber Technologies Private Limited",
    "Oniber Technologies Private Limited India",
    "pi-labs.ai",
    "GoodSpace AI",
    "GoodSpace",

    "Turing",
    "Somewhere",
    "Hancod",
    "Miamin Systems",
    "Skillzenloop",

    "Scoutit",
    "DataLendly",
    "intern",
    "fresher",

    "Interview Kickstart",
    "FlytBase",
    "INDMoney",
    "EssentiallySports" 
]

BLACKLIST_PATTERNS = [
    "parallel minds",
    "parallel minds technologies",
    "parallel minds technologies private limited",
    "parallel minds technologies private limited india",
    "pi labs",
    "pi labs technologies",
    "pi labs technologies private limited",
    "pi labs technologies private limited india",
    "oniber",
    "oniber technologies",
    "oniber technologies private limited",
    "oniber technologies private limited india",
    "pi-labs.ai",
    "goodspace ai",
    "goodspace",

    "Turing",
    "Somewhere",
    "Hancod",
    "Miamin Systems",
    "Skillzenloop",
    "intern",
    "fresher",

    "Scoutit",
    "DataLendly",

    "EssentiallySports" 
]

# ========================================
# APPLICATION SETTINGS
# ========================================

TOP_JOBS_TO_APPLY = 20
MIN_MATCH_SCORE = 50

EMAILS_PER_COMPANY = 6
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
    "Hiring Manager", "Engineering Manager", "Software Engineering Manager",
    "Analytics Manager", "Senior Engineering Manager",
    "People Operations", "People Partner", "Talent Partner",
    "Director of Talent", "Head of Talent", "Director of Hiring"
]

# ========================================
# REFERRAL OUTREACH SETTINGS
# ========================================

REFERRALS_PER_COMPANY = 6

# Referral roles: 4 based on your profile + 1 dynamic (job title from posting)
# The dynamic role will be added at runtime
REFERRAL_ROLES_BASE = [
    "Software Engineer",
    "Frontend Engineer",
    "Software Development Engineer",
    "Senior Frontend Engineer",
    "Senior Software Development Engineer",
]

# Google Sheets name
SHEETS_NAME = os.getenv("SHEETS_NAME", "Aditya's Job Applications Tracker v5.0 - 2026")
