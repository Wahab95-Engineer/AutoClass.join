import imaplib, email
from email.header import decode_header
from datetime import datetime, timedelta
from link_extractor import extract_meeting_links
from database import add_log

HOSTS = {
    "gmail":   "imap.gmail.com",
    "outlook": "imap-mail.outlook.com",
}

def decode_str(s):
    if not s: return ""
    d, enc = decode_header(s)[0]
    return d.decode(enc or "utf-8", errors="ignore") if isinstance(d, bytes) else d

def get_body(msg):
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try: body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                except: pass
    else:
        try: body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
        except: pass
    return body

def fetch_meetings(account):
    meetings = []
    try:
        imap = imaplib.IMAP4_SSL(account["imap_host"])
        imap.login(account["email"], account["password"])
        imap.select("INBOX")
        since = (datetime.now() - timedelta(days=2)).strftime("%d-%b-%Y")
        _, ids = imap.search(None, f'(SINCE "{since}")')
        if not ids[0]:
            imap.logout(); return meetings
        for mid in ids[0].split()[-30:]:
            try:
                _, data = imap.fetch(mid, "(RFC822)")
                msg = email.message_from_bytes(data[0][1])
                subject = decode_str(msg.get("Subject", ""))
                body = get_body(msg)
                links = extract_meeting_links(subject + " " + body)
                for l in links:
                    meetings.append({
                        "title": subject[:80] or "Class Meeting",
                        "link": l["link"],
                        "platform": l["platform"],
                        "scheduled_time": datetime.now().isoformat(),
                        "source": f"email:{account['email']}"
                    })
            except: pass
        imap.logout()
        add_log(f"📧 {len(meetings)} meetings found in {account['email']}")
    except Exception as e:
        add_log(f"❌ Email error: {e}", "error")
    return meetings