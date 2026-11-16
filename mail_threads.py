"""
Gmail helpers that keep follow-ups safe:

* has_replied(...)   - did this person (or anyone at their company) ever write back?
                        Searches ALL Mail (not just the Inbox), so archived/labelled
                        replies count too.
* find_thread(...)   - the original email we sent this person (Message-ID + subject),
                        so a follow-up can be sent as a reply in the SAME thread.

Read-only: it never changes, moves or marks anything in the mailbox.
"""

import email as email_lib
import imaplib
import re
from datetime import datetime, timedelta
from email.header import decode_header, make_header
from email.utils import parseaddr

# Replies from these domains can't be tied to a company, so only exact-address matches count
FREE_DOMAINS = {
    "gmail.com", "googlemail.com", "yahoo.com", "yahoo.in", "yahoo.co.in", "outlook.com",
    "hotmail.com", "live.com", "icloud.com", "me.com", "aol.com", "proton.me",
    "protonmail.com", "rediffmail.com", "zoho.com",
}


def _imap_date(date_str):
    try:
        d = datetime.strptime(str(date_str)[:10], "%Y-%m-%d") - timedelta(days=1)
    except ValueError:
        d = datetime.now() - timedelta(days=60)
    return d.strftime("%d-%b-%Y")


def _decode(value):
    try:
        return str(make_header(decode_header(value or "")))
    except Exception:
        return value or ""


class MailGuard:
    def __init__(self, user, app_password, logger=None):
        self.user = user
        self.password = app_password
        self.logger = logger
        self.me = (user or "").lower()
        self.my_domain = self.me.split("@")[-1]
        self._conn = None
        self._all_mail = None

    # ---------- connection ----------
    def _log(self, msg):
        if self.logger:
            self.logger.info(msg)

    def _imap(self):
        if self._conn is not None:
            try:
                self._conn.noop()
                return self._conn
            except Exception:
                self._conn = None
        conn = imaplib.IMAP4_SSL("imap.gmail.com", timeout=60)
        conn.login(self.user, self.password)
        if self._all_mail is None:
            self._all_mail = '"[Gmail]/All Mail"'
            status, boxes = conn.list()
            for line in boxes or []:
                text = line.decode(errors="ignore")
                if "\\All" in text:
                    m = re.search(r'"([^"]+)"\s*$', text)
                    if m:
                        self._all_mail = f'"{m.group(1)}"'
                    break
        conn.select(self._all_mail, readonly=True)
        self._conn = conn
        return conn

    def close(self):
        if self._conn is not None:
            try:
                self._conn.logout()
            except Exception:
                pass
            self._conn = None

    def _search(self, criteria):
        status, data = self._imap().search(None, criteria)
        return data[0].split() if status == "OK" and data and data[0] else []

    def _from_addresses(self, ids):
        out = []
        for i in ids:
            status, data = self._imap().fetch(i, "(BODY.PEEK[HEADER.FIELDS (FROM)])")
            if status == "OK" and data and data[0]:
                out.append(parseaddr(email_lib.message_from_bytes(data[0][1])["From"] or "")[1].lower())
        return out

    # ---------- reply detection ----------
    def has_replied(self, contact_email, since_date=None, company_level=True):
        """
        Returns (True, who) if the contact - or, with company_level, anyone from the
        same company email domain - has sent any email since our first email.
        """
        contact_email = (contact_email or "").strip().lower()
        if not contact_email or "@" not in contact_email:
            return False, ""
        since = _imap_date(since_date) if since_date else _imap_date("")

        if self._search(f'(FROM "{contact_email}" SINCE {since})'):
            return True, contact_email

        # Our email bounced / was blocked / rejected for this address
        if self.is_bounced(contact_email, since):
            return True, "BOUNCED"

        # Anyone writing back inside a thread we started with this person counts,
        # even from a different address (e.g. Apollo had an old company domain).
        who = self._reply_in_threads(contact_email, since)
        if who:
            return True, who

        domain = contact_email.split("@")[-1]
        if company_level and domain not in FREE_DOMAINS and domain != self.my_domain:
            ids = self._search(f'(FROM "@{domain}" SINCE {since})')
            for addr in self._from_addresses(ids):
                if addr.endswith("@" + domain) and addr != self.me:
                    return True, addr
        return False, ""

    # Gmail search for bounce / "message blocked" / rejection notices
    BOUNCE_QUERY = ('(from:mailer-daemon OR from:postmaster OR from:microsoftexchange OR '
                    'subject:undeliverable OR subject:undelivered OR subject:"delivery status notification" OR '
                    'subject:"delivery has failed" OR subject:"delivery failure" OR subject:"failure notice" OR '
                    'subject:"not delivered" OR subject:"returned mail" OR subject:blocked OR subject:rejected OR '
                    'blocked OR "has been rejected" OR "was not delivered" OR '
                    '"account is disabled" OR "account has been disabled" OR "account is blocked" OR '
                    '"account has been blocked" OR "account is suspended" OR "account is inactive" OR '
                    '"mailbox unavailable" OR "mailbox is full" OR "address not found" OR "does not exist" OR '
                    '"no longer with" OR "no longer works" OR "no longer employed" OR "has left the company")')

    def is_bounced(self, contact_email, since=None):
        """True if a bounce / 'message blocked' / rejection notice mentions this address."""
        try:
            after = datetime.strptime(since, "%d-%b-%Y").strftime("%Y/%m/%d") if since else ""
        except ValueError:
            after = ""
        raw = f'"{contact_email}" -from:me {self.BOUNCE_QUERY}' + (f" after:{after}" if after else "")
        status, data = self._imap().search(None, "X-GM-RAW", '"' + raw.replace('"', '\\"') + '"')
        return bool(status == "OK" and data and data[0])

    def _reply_in_threads(self, contact_email, since):
        conn = self._imap()
        thread_ids = set()
        for i in self._search(f'(FROM "{self.me}" TO "{contact_email}" SINCE {since})'):
            status, data = conn.fetch(i, "(X-GM-THRID)")
            if status == "OK" and data and data[0]:
                m = re.search(rb"X-GM-THRID (\d+)", data[0] if isinstance(data[0], bytes) else data[0][0])
                if m:
                    thread_ids.add(m.group(1).decode())
        for tid in thread_ids:
            for addr in self._from_addresses(self._search(f"(X-GM-THRID {tid})")):
                if addr and addr != self.me:
                    return addr
        return ""

    # ---------- thread lookup ----------
    def find_thread(self, to_email, subject_hint=None, since_date=None):
        """
        Find the first email we sent to `to_email` (optionally whose subject contains
        `subject_hint`). Returns {"message_id", "subject", "references"} or None.
        """
        to_email = (to_email or "").strip().lower()
        if not to_email:
            return None
        since = _imap_date(since_date) if since_date else _imap_date("")
        ids = self._search(f'(FROM "{self.me}" TO "{to_email}" SINCE {since})')
        for i in ids:  # oldest first
            status, data = self._imap().fetch(
                i, "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID SUBJECT REFERENCES)])")
            if status != "OK" or not data or not data[0]:
                continue
            h = email_lib.message_from_bytes(data[0][1])
            subject = _decode(h["Subject"])
            if subject.lower().startswith("re:"):
                continue
            if subject_hint and subject_hint.lower() not in subject.lower():
                continue
            if h["Message-ID"]:
                return {"message_id": h["Message-ID"].strip(), "subject": subject,
                        "references": (h["References"] or "").strip()}
        return None


def apply_thread_headers(msg, thread):
    """Turn `msg` into a reply within `thread` (same subject, In-Reply-To, References)."""
    subject = thread["subject"]
    msg["Subject"] = subject if subject.lower().startswith("re:") else f"Re: {subject}"
    msg["In-Reply-To"] = thread["message_id"]
    refs = (thread.get("references") or "").split()
    if thread["message_id"] not in refs:
        refs.append(thread["message_id"])
    msg["References"] = " ".join(refs)
    return msg
