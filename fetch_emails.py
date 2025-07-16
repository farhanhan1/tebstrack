import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
from datetime import datetime
import sqlite3

# Load environment variables
load_dotenv()
GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'tickets.db')

# Connect to the database
def get_db():
    return sqlite3.connect(DB_PATH)

def parse_email(msg):
    subject = msg['subject']
    sender = msg['from']
    date = msg['date']
    # Try to decode subject
    if subject:
        dh = decode_header(subject)
        subject = ''.join([
            (t.decode(enc) if isinstance(t, bytes) else t)
            if enc else (t if isinstance(t, str) else t.decode())
            for t, enc in dh
        ])
    # Get body (plain text only)
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                charset = part.get_content_charset() or 'utf-8'
                body = part.get_payload(decode=True).decode(charset, errors='replace')
                break
    else:
        charset = msg.get_content_charset() or 'utf-8'
        body = msg.get_payload(decode=True).decode(charset, errors='replace')
    return subject, sender, date, body

def add_ticket(subject, sender, date, body):
    # You may want to parse category/urgency from subject/body
    created_at = datetime.strptime(date[:25], '%a, %d %b %Y %H:%M:%S') if date else datetime.utcnow()
    with get_db() as conn:
        c = conn.cursor()
        c.execute('''INSERT INTO tickets (subject, sender, created_at, status, category, urgency, description)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (subject, sender, created_at, 'Open', 'General', 'Medium', body))
        conn.commit()

def fetch_and_store_emails():
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    mail.select('inbox')
    status, messages = mail.search(None, '(UNSEEN)')
    if status != 'OK':
        print('No new emails found.')
        return
    for num in messages[0].split():
        status, data = mail.fetch(num, '(RFC822)')
        if status != 'OK':
            continue
        msg = email.message_from_bytes(data[0][1])
        subject, sender, date, body = parse_email(msg)
        add_ticket(subject, sender, date, body)
        # Mark as seen
        mail.store(num, '+FLAGS', '\Seen')
    mail.logout()

if __name__ == '__main__':
    fetch_and_store_emails()
