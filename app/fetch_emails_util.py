import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
from datetime import datetime
from .models import db, Ticket

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

def ticket_exists(subject, sender, date):
    # Use subject, sender, and date as a unique key
    return db.session.query(Ticket).filter_by(subject=subject, sender=sender, created_at=date).first() is not None

def add_ticket(subject, sender, date, body):
    # You may want to parse category/urgency from subject/body
    try:
        created_at = datetime.strptime(date[:25], '%a, %d %b %Y %H:%M:%S') if date else datetime.utcnow()
    except Exception:
        created_at = datetime.utcnow()
    if ticket_exists(subject, sender, created_at):
        return False
    ticket = Ticket(
        subject=subject,
        sender=sender,
        created_at=created_at,
        status='Open',
        category='General',
        urgency='Medium',
        description=body
    )
    db.session.add(ticket)
    db.session.commit()
    return True

def fetch_and_store_emails():
    load_dotenv()
    GMAIL_USER = os.getenv('GMAIL_USER')
    GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
    import ssl
    mail = imaplib.IMAP4_SSL('imap.gmail.com')
    mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
    mail.select('inbox')
    status, messages = mail.search(None, '(UNSEEN)')
    if status != 'OK':
        return 0
    count = 0
    for num in messages[0].split():
        status, data = mail.fetch(num, '(RFC822)')
        if status != 'OK':
            continue
        msg = email.message_from_bytes(data[0][1])
        subject, sender, date, body = parse_email(msg)
        if add_ticket(subject, sender, date, body):
            count += 1
        mail.store(num, '+FLAGS', '\Seen')
    mail.logout()
    return count
