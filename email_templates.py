from config import YOUR_NAME, YOUR_PHONE, YOUR_EMAIL, YOUR_LINKEDIN

# ========================================
# Templates tailored to Hardik's Product Manager profile.
# Placeholders: {hr_first_name}, {first_name}, {job_role}, {company_name},
#               {application_date}, {email_date}
# (The original frontend templates are saved in email_templates.friend_backup.py)
# ========================================

_STYLE = 'font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;'

SIGNATURE_HTML = ("<p>Best regards,<br>\n<strong>" + str(YOUR_NAME) + "</strong><br>\n"
                  + str(YOUR_PHONE) + "<br>\n" + str(YOUR_EMAIL) + "<br>\n"
                  + '<a href="https://' + str(YOUR_LINKEDIN) + '">' + str(YOUR_LINKEDIN) + "</a></p>")

SIGNATURE_PLAIN = ("Best regards,\n" + str(YOUR_NAME) + "\n" + str(YOUR_PHONE) + "\n"
                   + str(YOUR_EMAIL) + "\n" + str(YOUR_LINKEDIN))

# ========================================
# APPLICATION EMAIL (to HR / hiring manager)
# ========================================

EMAIL_TEMPLATE_HTML = """<html><body style=\"""" + _STYLE + """\">
<p>Hi {hr_first_name},</p>
<p>I am writing to apply for the <strong>{job_role}</strong> position at <strong>{company_name}</strong>.</p>
<p>I am a Product Manager with <strong>3 years of experience</strong> across B2C edtech and B2B risk/fraud data products (ZIGRAM, PrepLadder by Unacademy, University Living). A few highlights:</p>
<ul>
<li>Scaled an <strong>LLM-based AI chatbot from 0 to 10k+ users</strong>, owning PRDs, prompt iteration and guardrails</li>
<li>Revamped the signup flow, increasing <strong>new user signups by 18%</strong></li>
<li>Cut risk profile creation time from <strong>1 day to 2-3 hours</strong> for an enterprise client (Moody's)</li>
</ul>
<p>If you are involved in hiring for this role, I would welcome the chance to discuss it. If it sits with a different team, I would really appreciate it if you could forward my resume to the right hiring manager.</p>
<p>My resume is attached for your review. Thank you for your time.</p>
""" + SIGNATURE_HTML + """
</body></html>"""

EMAIL_TEMPLATE_PLAIN = """Hi {hr_first_name},

I am writing to apply for the {job_role} position at {company_name}.

I am a Product Manager with 3 years of experience across B2C edtech and B2B risk/fraud data products (ZIGRAM, PrepLadder by Unacademy, University Living). A few highlights:

- Scaled an LLM-based AI chatbot from 0 to 10k+ users, owning PRDs, prompt iteration and guardrails
- Revamped the signup flow, increasing new user signups by 18%
- Cut risk profile creation time from 1 day to 2-3 hours for an enterprise client (Moody's)

If you are involved in hiring for this role, I would welcome the chance to discuss it. If it sits with a different team, I would really appreciate it if you could forward my resume to the right hiring manager.

My resume is attached for your review. Thank you for your time.

""" + SIGNATURE_PLAIN

# ========================================
# HR FOLLOW-UPS
# ========================================

FOLLOWUP_EMAIL_HTML = """<html><body style=\"""" + _STYLE + """\">
<p>Hi {hr_first_name},</p>
<p>I wanted to follow up on my application for the <strong>{job_role}</strong> position at <strong>{company_name}</strong>, which I sent on <strong>{application_date}</strong>.</p>
<p>I remain very interested and would love to discuss how my experience shipping AI and growth products (0 to 10k+ users on an LLM chatbot, +18% signups) could help your team.</p>
<p>Happy to share anything else you need.</p>
""" + SIGNATURE_HTML + """
</body></html>"""

HR_FOLLOWUP2_EMAIL_HTML = """<html><body style=\"""" + _STYLE + """\">
<p>Hi {hr_first_name},</p>
<p>Reaching out one last time about the <strong>{job_role}</strong> position at <strong>{company_name}</strong>.</p>
<p>I understand hiring timelines shift, and if the role has been filled or isn't the right fit, no problem at all.</p>
<p>If it is still open, I would be grateful for a quick conversation. I'm confident my product experience across discovery, PRDs, AI products and growth would let me contribute quickly.</p>
<p>Thank you for your time and consideration.</p>
""" + SIGNATURE_HTML + """
</body></html>"""

# ========================================
# LINKEDIN CONNECTION MESSAGE (keep under ~300 chars)
# ========================================

LINKEDIN_MESSAGE = """Hi {hr_first_name},

I came across the {job_role} opening at {company_name}. I'm a Product Manager (ex-PrepLadder, University Living) who scaled an LLM chatbot from 0 to 10k+ users. Would love to connect!"""

# ========================================
# REFERRAL EMAILS (to employees at the company)
# ========================================

REFERRAL_EMAIL_HTML = """<html><body style=\"""" + _STYLE + """\">
<p>Hi {first_name},</p>
<p>I hope you're doing well. I noticed you work at <strong>{company_name}</strong>, and I'm very interested in the <strong>{job_role}</strong> role currently open there.</p>
<p>Would you be open to referring me, or pointing me to the right person on the hiring team?</p>
<p>A bit about me: I'm a Product Manager with 3 years of experience at ZIGRAM, PrepLadder by Unacademy and University Living. I scaled an LLM-based AI chatbot from 0 to 10k+ users, grew new signups by 18%, and automated risk workflows for Moody's.</p>
<p>My resume is attached. Happy to share anything else that helps.</p>
<p>Thank you so much for considering it!</p>
""" + SIGNATURE_HTML + """
</body></html>"""

REFERRAL_EMAIL_PLAIN = """Hi {first_name},

I hope you're doing well. I noticed you work at {company_name}, and I'm very interested in the {job_role} role currently open there.

Would you be open to referring me, or pointing me to the right person on the hiring team?

A bit about me: I'm a Product Manager with 3 years of experience at ZIGRAM, PrepLadder by Unacademy and University Living. I scaled an LLM-based AI chatbot from 0 to 10k+ users, grew new signups by 18%, and automated risk workflows for Moody's.

My resume is attached. Happy to share anything else that helps.

Thank you so much for considering it!

""" + SIGNATURE_PLAIN

REFERRAL_FOLLOWUP1_EMAIL_HTML = """<html><body style=\"""" + _STYLE + """\">
<p>Hi {first_name},</p>
<p>Just following up on my message from <strong>{email_date}</strong> about the <strong>{job_role}</strong> role at <strong>{company_name}</strong>.</p>
<p>I know you're busy. If you get a moment, I'd really appreciate a referral or a pointer to the right person on the hiring team.</p>
<p>Thanks again for your time, I truly appreciate any help!</p>
""" + SIGNATURE_HTML + """
</body></html>"""

REFERRAL_FOLLOWUP2_EMAIL_HTML = """<html><body style=\"""" + _STYLE + """\">
<p>Hi {first_name},</p>
<p>Reaching out one last time about a referral for the <strong>{job_role}</strong> role at <strong>{company_name}</strong>.</p>
<p>Completely understand if it's not possible right now, no worries at all. Thank you for reading my messages, and I wish you all the best!</p>
""" + SIGNATURE_HTML + """
</body></html>"""

# ========================================
# "FULLSTACK" VARIANTS
# The bot was built for two resumes (frontend / fullstack). With a single PM
# resume these simply reuse the templates above.
# ========================================

FULLSTACK_EMAIL_TEMPLATE_HTML = EMAIL_TEMPLATE_HTML
FULLSTACK_EMAIL_TEMPLATE_PLAIN = EMAIL_TEMPLATE_PLAIN
FULLSTACK_FOLLOWUP_EMAIL_HTML = FOLLOWUP_EMAIL_HTML
FULLSTACK_FOLLOWUP2_EMAIL_HTML = HR_FOLLOWUP2_EMAIL_HTML
FULLSTACK_REFERRAL_EMAIL_HTML = REFERRAL_EMAIL_HTML
FULLSTACK_REFERRAL_EMAIL_PLAIN = REFERRAL_EMAIL_PLAIN
FULLSTACK_LINKEDIN_MESSAGE = LINKEDIN_MESSAGE
