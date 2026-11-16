from config import YOUR_NAME, YOUR_PHONE, YOUR_EMAIL, YOUR_LINKEDIN

# ========================================
# EMAIL TEMPLATES (FRONTEND)
# ========================================

EMAIL_TEMPLATE_HTML = """<html><body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
<p>Hi {hr_first_name},</p>
<p>I am writing to submit my application for the <strong>{job_role}</strong> position at <strong>{company_name}</strong>.</p>
<p>With around <strong>2 years of experience in frontend development</strong>, and a <strong>87% match score</strong> for this role, I am confident I can deliver immediate value to your team.</p>
<p>I hold strong expertise in <strong>ReactJS/NextJS, TypeScript/JavaScript</strong>, optimizing core web performance and user experience.</p>
<p>If you are involved in hiring for this position, I would welcome the opportunity to discuss my qualifications. If this role falls under a different team, I would greatly appreciate if you could direct my resume to the relevant hiring manager.</p>
<p>My resume is attached for your review.</p>
<p>Thank you for your time and consideration.</p>

<p>Best regards,<br>
<strong>""" + YOUR_NAME + """</strong><br>
""" + YOUR_PHONE + """<br>
""" + YOUR_EMAIL + """<br>
<a href="https://""" + YOUR_LINKEDIN + """">""" + YOUR_LINKEDIN + """</a></p>
</body></html>"""

EMAIL_TEMPLATE_PLAIN = """Hi {hr_first_name},

I am writing to submit my application for the {job_role} position at {company_name}.

With around 2 years of experience in frontend development, and a 87% match score for this role, I am confident I can deliver immediate value to your team.

I hold strong expertise in ReactJS/NextJS, TypeScript/JavaScript, optimizing core web performance and user experience.

If you are involved in hiring for this position, I would welcome the opportunity to discuss my qualifications. If this role falls under a different team, I would greatly appreciate if you could direct my resume to the relevant hiring manager.

My resume is attached for your review.

Thank you for your time and consideration.

Best regards,
""" + YOUR_NAME + """
""" + YOUR_PHONE + """
""" + YOUR_EMAIL + """
""" + YOUR_LINKEDIN

FOLLOWUP_EMAIL_HTML = """<html><body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
<p>Hi {hr_first_name},</p>
<p>I wanted to follow up on my application for the <strong>{job_role}</strong> position at <strong>{company_name}</strong> that I submitted on <strong>{application_date}</strong>.</p>
<p>I remain very interested in this opportunity and would welcome the chance to discuss how my experience at <strong>Frontend Development</strong> with <strong>ReactJS/NextJS, TypeScript/JavaScript</strong> would benefit your team.</p>
<p>Please let me know if you need any additional information.</p>
<p>Best regards,<br>
<strong>""" + YOUR_NAME + """</strong><br>
""" + YOUR_PHONE + """<br>
""" + YOUR_EMAIL + """<br>
<a href="https://""" + YOUR_LINKEDIN + """">""" + YOUR_LINKEDIN + """</a></p>
</body></html>"""

LINKEDIN_MESSAGE = """Hi {hr_first_name},

I came across the {job_role} opening at {company_name} and was impressed by the opportunity. I'm a Frontend Developer at Parallel Minds with experience building frontend applications with ReactJS/NextJS, TypeScript/JavaScript.

Would love to connect and explore potential fit!"""

# ========================================
# REFERRAL EMAIL TEMPLATES (FRONTEND)
# ========================================

REFERRAL_EMAIL_HTML = """<html><body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
<p>Hi {first_name},</p>
<p>I hope this message finds you well. I'm reaching out because I noticed you work at <strong>{company_name}</strong>, and I'm very interested in the <strong>{job_role}</strong> position currently open at {company_name}.</p>
<p>I would be grateful if you could refer me for this role or connect me with the hiring team.</p>
<p>A bit about my background: I have around <strong>2 years of experience at Parallel Minds</strong>, where I've built frontend applications with ReactJS/NextJS, TypeScript/JavaScript.</p>
<p>I believe my experience aligns well with this opportunity, and I'm confident I can contribute meaningfully to your team.</p>
<p>My resume is attached for your reference. I'd be happy to provide any additional information or discuss my qualifications further.</p>
<p>Thank you for considering my request!</p>
<p>Best regards,<br>
<strong>""" + YOUR_NAME + """</strong><br>
""" + YOUR_PHONE + """<br>
""" + YOUR_EMAIL + """<br>
<a href="https://""" + YOUR_LINKEDIN + """">""" + YOUR_LINKEDIN + """</a></p>
</body></html>"""

REFERRAL_EMAIL_PLAIN = """Hi {first_name},

I hope this message finds you well. I'm reaching out because I noticed you work at {company_name}, and I'm very interested in the {job_role} position currently open at{company_name}.

I would be grateful if you could refer me for this role or connect me with the hiring team.

A bit about my background: I have around 2 years of experience at Parallel Minds, where I've built frontend applications with ReactJS/NextJS, TypeScript/JavaScript.

I believe my experience aligns well with this opportunity, and I'm confident I can contribute meaningfully to your team.

My resume is attached for your reference. I'd be happy to provide any additional information or discuss my qualifications further.

Thank you for considering my request!

Best regards,
""" + YOUR_NAME + """
""" + YOUR_PHONE + """
""" + YOUR_EMAIL + """
""" + YOUR_LINKEDIN

# ========================================
# FOLLOW-UP 2 TEMPLATES (HR)
# ========================================

HR_FOLLOWUP2_EMAIL_HTML = """<html><body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
<p>Hi {hr_first_name},</p>
<p>I wanted to reach out one last time regarding my application for the <strong>{job_role}</strong> position at <strong>{company_name}</strong>.</p>
<p>I understand hiring timelines can shift and you may have many candidates to review. If this role has been filled or isn't the right fit, I completely understand.</p>
<p>However, if the position is still open, I would be grateful for the opportunity to connect. I'm confident my frontend development expertise with ReactJS/NextJS, TypeScript/JavaScript would allow me to contribute meaningfully to your team.</p>
<p>Thank you for your time and consideration throughout this process.</p>
<p>Best regards,<br>
<strong>""" + YOUR_NAME + """</strong><br>
""" + YOUR_PHONE + """<br>
""" + YOUR_EMAIL + """<br>
<a href="https://""" + YOUR_LINKEDIN + """">""" + YOUR_LINKEDIN + """</a></p>
</body></html>"""

# ========================================
# REFERRAL FOLLOW-UP TEMPLATES
# ========================================

REFERRAL_FOLLOWUP1_EMAIL_HTML = """<html><body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
<p>Hi {first_name},</p>
<p>I wanted to follow up on my earlier message regarding the <strong>{job_role}</strong> position at <strong>{company_name}</strong> that I sent on <strong>{email_date}</strong>.</p>
<p>I completely understand you may have a busy schedule, but I wanted to gently check if you had a chance to consider my referral request or could point me to the right person on the hiring team.</p>
<p>I remain very excited about the opportunity to join <strong>{company_name}</strong> and believe my experience in <strong>frontend development</strong> with <strong>ReactJS/NextJS, TypeScript/JavaScript</strong> expertise would be a great fit.</p>
<p>Thank you again for your time — I truly appreciate any help you can provide!</p>
<p>Best regards,<br>
<strong>""" + YOUR_NAME + """</strong><br>
""" + YOUR_PHONE + """<br>
""" + YOUR_EMAIL + """<br>
<a href="https://""" + YOUR_LINKEDIN + """">""" + YOUR_LINKEDIN + """</a></p>
</body></html>"""

REFERRAL_FOLLOWUP2_EMAIL_HTML = """<html><body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
<p>Hi {first_name},</p>
<p>I wanted to reach out one last time regarding my referral request for the <strong>{job_role}</strong> position at <strong>{company_name}</strong>.</p>
<p>I completely understand if you're not able to help or if this isn't the right time — no worries at all! I truly appreciate you taking the time to read my messages.</p>
<p>If you do know anyone on the hiring team or could submit a referral, I would be very grateful. Either way, thank you for your time, and I wish you all the best!</p>
<p>Warm regards,<br>
<strong>""" + YOUR_NAME + """</strong><br>
""" + YOUR_PHONE + """<br>
""" + YOUR_EMAIL + """<br>
<a href="https://""" + YOUR_LINKEDIN + """">""" + YOUR_LINKEDIN + """</a></p>
</body></html>"""

# ========================================
# FULL STACK EMAIL TEMPLATES
# ========================================

FULLSTACK_EMAIL_TEMPLATE_HTML = """<html><body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
<p>Hi {hr_first_name},</p>
<p>I am writing to submit my application for the <strong>{job_role}</strong> position at <strong>{company_name}</strong>.</p>
<p>With around <strong>2 years of experience in full stack development</strong>, and a <strong>87% match score</strong> for this role, I am confident I can deliver immediate value to your team.</p>
<p>I hold strong expertise in <strong>ReactJS/NextJS, NodeJS/ExpressJS, MongoDB</strong>, building end-to-end web applications with optimized performance.</p>
<p>If you are involved in hiring for this position, I would welcome the opportunity to discuss my qualifications. If this role falls under a different team, I would greatly appreciate if you could direct my resume to the relevant hiring manager.</p>
<p>My resume is attached for your review.</p>
<p>Thank you for your time and consideration.</p>

<p>Best regards,<br>
<strong>""" + YOUR_NAME + """</strong><br>
""" + YOUR_PHONE + """<br>
""" + YOUR_EMAIL + """<br>
<a href="https://""" + YOUR_LINKEDIN + """">""" + YOUR_LINKEDIN + """</a></p>
</body></html>"""

FULLSTACK_EMAIL_TEMPLATE_PLAIN = """Hi {hr_first_name},

I am writing to submit my application for the {job_role} position at {company_name}.

With around 2 years of experience in full stack development, and a 87% match score for this role, I am confident I can deliver immediate value to your team.

I hold strong expertise in ReactJS/NextJS, NodeJS/ExpressJS, MongoDB, building end-to-end web applications with optimized performance.

If you are involved in hiring for this position, I would welcome the opportunity to discuss my qualifications. If this role falls under a different team, I would greatly appreciate if you could direct my resume to the relevant hiring manager.

My resume is attached for your review.

Thank you for your time and consideration.

Best regards,
""" + YOUR_NAME + """
""" + YOUR_PHONE + """
""" + YOUR_EMAIL + """
""" + YOUR_LINKEDIN

FULLSTACK_FOLLOWUP_EMAIL_HTML = """<html><body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
<p>Hi {hr_first_name},</p>
<p>I wanted to follow up on my application for the <strong>{job_role}</strong> position at <strong>{company_name}</strong> that I submitted on <strong>{application_date}</strong>.</p>
<p>I remain very interested in this opportunity and would welcome the chance to discuss how my experience in <strong>Full Stack Development</strong> with <strong>ReactJS/NextJS, NodeJS/ExpressJS, MongoDB</strong> would benefit your team.</p>
<p>Please let me know if you need any additional information.</p>
<p>Best regards,<br>
<strong>""" + YOUR_NAME + """</strong><br>
""" + YOUR_PHONE + """<br>
""" + YOUR_EMAIL + """<br>
<a href="https://""" + YOUR_LINKEDIN + """">""" + YOUR_LINKEDIN + """</a></p>
</body></html>"""

FULLSTACK_FOLLOWUP2_EMAIL_HTML = """<html><body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
<p>Hi {hr_first_name},</p>
<p>I wanted to reach out one last time regarding my application for the <strong>{job_role}</strong> position at <strong>{company_name}</strong>.</p>
<p>I understand hiring timelines can shift and you may have many candidates to review. If this role has been filled or isn't the right fit, I completely understand.</p>
<p>However, if the position is still open, I would be grateful for the opportunity to connect. I'm confident my full stack development expertise with ReactJS/NextJS, NodeJS/ExpressJS, MongoDB would allow me to contribute meaningfully to your team.</p>
<p>Thank you for your time and consideration throughout this process.</p>
<p>Best regards,<br>
<strong>""" + YOUR_NAME + """</strong><br>
""" + YOUR_PHONE + """<br>
""" + YOUR_EMAIL + """<br>
<a href="https://""" + YOUR_LINKEDIN + """">""" + YOUR_LINKEDIN + """</a></p>
</body></html>"""

FULLSTACK_REFERRAL_EMAIL_HTML = """<html><body style="font-family: Arial, sans-serif; font-size: 14px; line-height: 1.6; color: #333;">
<p>Hi {first_name},</p>
<p>I hope this message finds you well. I'm reaching out because I noticed you work at <strong>{company_name}</strong>, and I'm very interested in the <strong>{job_role}</strong> position currently open at {company_name}.</p>
<p>I would be grateful if you could refer me for this role or connect me with the hiring team.</p>
<p>A bit about my background: I have around <strong>2 years of experience at Parallel Minds</strong>, where I've built full stack applications with ReactJS/NextJS, NodeJS/ExpressJS, and MongoDB.</p>
<p>I believe my experience aligns well with this opportunity, and I'm confident I can contribute meaningfully to your team.</p>
<p>My resume is attached for your reference. I'd be happy to provide any additional information or discuss my qualifications further.</p>
<p>Thank you for considering my request!</p>
<p>Best regards,<br>
<strong>""" + YOUR_NAME + """</strong><br>
""" + YOUR_PHONE + """<br>
""" + YOUR_EMAIL + """<br>
<a href="https://""" + YOUR_LINKEDIN + """">""" + YOUR_LINKEDIN + """</a></p>
</body></html>"""

FULLSTACK_REFERRAL_EMAIL_PLAIN = """Hi {first_name},

I hope this message finds you well. I'm reaching out because I noticed you work at {company_name}, and I'm very interested in the {job_role} position currently open at {company_name}.

I would be grateful if you could refer me for this role or connect me with the hiring team.

A bit about my background: I have around 2 years of experience at Parallel Minds, where I've built full stack applications with ReactJS/NextJS, NodeJS/ExpressJS, and MongoDB.

I believe my experience aligns well with this opportunity, and I'm confident I can contribute meaningfully to your team.

My resume is attached for your reference. I'd be happy to provide any additional information or discuss my qualifications further.

Thank you for considering my request!

Best regards,
""" + YOUR_NAME + """
""" + YOUR_PHONE + """
""" + YOUR_EMAIL + """
""" + YOUR_LINKEDIN

FULLSTACK_LINKEDIN_MESSAGE = """Hi {hr_first_name},

I came across the {job_role} opening at {company_name} and was impressed by the opportunity. I'm a Full Stack Developer at Parallel Minds with experience building web applications with ReactJS/NextJS, NodeJS/ExpressJS, and MongoDB.

Would love to connect and explore potential fit!"""
