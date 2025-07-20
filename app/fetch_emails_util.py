import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
from datetime import datetime
from .models import db, Ticket, EmailMessage

def parse_email(msg):
    subject = msg['subject']
    sender = msg['from']
    date = msg['date']
    message_id = msg.get('Message-ID')
    thread_id = msg.get('In-Reply-To') or message_id
    # Try to decode subject
    if subject:
        dh = decode_header(subject)
        subject = ''.join([
            (t.decode(enc) if isinstance(t, bytes) else t)
            if enc else (t if isinstance(t, str) else t.decode())
            for t, enc in dh
        ])
    import mimetypes, uuid, os, json
    body = ''
    attachments = []
    if msg.is_multipart():
        for part in msg.walk():
            ctype = part.get_content_type()
            cdispo = str(part.get('Content-Disposition'))
            if ctype == 'text/plain' and 'attachment' not in cdispo:
                charset = part.get_content_charset() or 'utf-8'
                body = part.get_payload(decode=True).decode(charset, errors='replace')
            elif part.get_filename():
                # Save attachment
                filename = part.get_filename()
                if not filename:
                    ext = mimetypes.guess_extension(ctype) or '.bin'
                    filename = f'attachment_{uuid.uuid4().hex}{ext}'
                else:
                    filename = f'{uuid.uuid4().hex}_{filename}'
                att_folder = os.path.join(os.getcwd(), 'attachments')
                os.makedirs(att_folder, exist_ok=True)
                filepath = os.path.join(att_folder, filename)
                with open(filepath, 'wb') as f:
                    f.write(part.get_payload(decode=True))
                is_image = ctype.startswith('image/')
                attachments.append({
                    'filename': filename,
                    'is_image': is_image,
                    'url': f'/attachments/{filename}'
                })
    else:
        charset = msg.get_content_charset() or 'utf-8'
        body = msg.get_payload(decode=True).decode(charset, errors='replace')
    return subject, sender, date, body, message_id, thread_id, attachments

def ticket_exists(subject, sender, date):
    # Use subject, sender, and date as a unique key (legacy, not used for threads)
    return db.session.query(Ticket).filter_by(subject=subject, sender=sender, created_at=date).first() is not None

def add_ticket(subject, sender, date, body):
    # Deprecated: not used for threads
    return False

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
        subject, sender, date, body, message_id, thread_id, attachments = parse_email(msg)
        # Parse date
        try:
            created_at = datetime.strptime(date[:25], '%a, %d %b %Y %H:%M:%S') if date else datetime.utcnow()
        except Exception:
            created_at = datetime.utcnow()
        # Find or create ticket for this thread
        ticket = None
        if thread_id:
            ticket = Ticket.query.filter_by(thread_id=thread_id).first()
        if not ticket:
            ticket = Ticket(
                subject=subject,
                sender=sender,
                created_at=created_at,
                status='Open',
                category='General',
                urgency='Medium',
                description=body,
                thread_id=thread_id
            )
            db.session.add(ticket)
            db.session.commit()
        # Save email message
        import json
        emsg = EmailMessage(
            ticket_id=ticket.id,
            thread_id=thread_id,
            sender=sender,
            subject=subject,
            body=body,
            sent_at=created_at,
            attachments=json.dumps(attachments) if attachments else None
        )
        db.session.add(emsg)
        db.session.commit()
        count += 1
        mail.store(num, '+FLAGS', '\\Seen')
    mail.logout()
    return count
