import os
import imaplib
import email
from email.header import decode_header
from dotenv import load_dotenv
from datetime import datetime
from .models import db, Ticket, EmailMessage

def parse_email(msg):
    subject = msg['subject']
    import email.utils
    sender_name, sender_email = email.utils.parseaddr(msg['from'])
    if sender_email:
        # Always store as 'Name <email>' if email is present
        if sender_name:
            sender = f"{sender_name} <{sender_email}>"
        else:
            sender = f"<{sender_email}>"
    else:
        sender = msg['from']
    date = msg['date']
    message_id = msg.get('Message-ID')
    # Use References header to find the root of the thread if available
    references = msg.get('References')
    if references:
        # References is a space-separated list of Message-IDs, the first is the root
        root_id = references.split()[0]
        thread_id = root_id
    else:
        # If no References, use In-Reply-To, else Message-ID
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
    # Fetch both inbox and sent mail for GMAIL_USER
    count = 0
    import ssl
    import email as email_mod
    GMAIL_USER = os.getenv('GMAIL_USER')
    GMAIL_APP_PASSWORD = os.getenv('GMAIL_APP_PASSWORD')
    for mailbox in ['INBOX', '"[Gmail]/Sent Mail"']:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        # Use double quotes for Sent Mail to avoid IMAP parse errors
        mail.select(mailbox)
        if mailbox == 'INBOX':
            status, messages = mail.search(None, '(UNSEEN)')
        else:
            status, messages = mail.search(None, 'ALL')
        if status != 'OK':
            mail.logout()
            continue
        for num in messages[0].split():
            status, data = mail.fetch(num, '(RFC822)')
            if status != 'OK':
                continue
            msg = email_mod.message_from_bytes(data[0][1])
            subject, sender, date, body, message_id, thread_id, attachments = parse_email(msg)
            # Debug: print the raw and parsed sender
            print(f"[DEBUG] Raw msg['from']: {msg['from']}", flush=True)
            print(f"[DEBUG] Parsed sender: {sender}", flush=True)
            # Parse date
            try:
                import email.utils
                # Parse date to UTC
                if date:
                    parsed_tuple = email.utils.parsedate_tz(date)
                    if parsed_tuple:
                        timestamp = email.utils.mktime_tz(parsed_tuple)
                        from datetime import datetime, timezone
                        created_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    else:
                        created_at = datetime.utcnow().replace(tzinfo=None)
                else:
                    created_at = datetime.utcnow().replace(tzinfo=None)
            except Exception:
                created_at = datetime.utcnow().replace(tzinfo=None)
            # Find ticket for this thread (do not create for sent mail)
            ticket = None
            if thread_id:
                ticket = Ticket.query.filter_by(thread_id=thread_id).first()
            # Check if ticket was deleted (soft delete: status='Deleted')
            if ticket and getattr(ticket, 'status', None) == 'Deleted':
                # Don't recreate deleted tickets, and don't log the email message
                ticket = None
            # Only create a ticket if the sender is NOT the support email (GMAIL_USER) and mailbox is INBOX
            if not ticket and mailbox == 'INBOX':
                if sender and GMAIL_USER and GMAIL_USER.lower() in sender.lower():
                    ticket = None
                else:
                    # Auto-categorize new tickets using AI
                    try:
                        from app.ai_service import get_ai_service
                        ai_service = get_ai_service()
                        categorization_result = ai_service.categorize_ticket(subject, body, sender)
                        
                        # Use AI-suggested category and urgency if available
                        ai_category = categorization_result.get('category', 'General')
                        ai_urgency = categorization_result.get('urgency', 'Medium')
                        
                        # Validate that the AI-suggested category exists in the database
                        from app.models import Category
                        category_obj = Category.query.filter_by(name=ai_category).first()
                        if not category_obj:
                            ai_category = 'General'  # Fallback to General if AI category doesn't exist
                            
                        print(f"[DEBUG] AI categorized new ticket '{subject}' as '{ai_category}' with urgency '{ai_urgency}' (confidence: {categorization_result.get('confidence', 0):.2f})", flush=True)
                        
                    except Exception as e:
                        # Fallback to defaults if AI categorization fails
                        ai_category = 'General'
                        ai_urgency = 'Medium'
                        print(f"[DEBUG] AI categorization failed for new ticket '{subject}': {e}. Using defaults.", flush=True)
                    
                    ticket = Ticket(
                        subject=subject,
                        sender=sender,
                        created_at=created_at,
                        status='Open',
                        category=ai_category,
                        urgency=ai_urgency,
                        description=body,
                        thread_id=thread_id
                    )
                    db.session.add(ticket)
                    db.session.commit()
                    
                    # Log AI categorization if it was used successfully
                    if ai_category != 'General' or ai_urgency != 'Medium':
                        try:
                            from app.models import Log
                            confidence = categorization_result.get('confidence', 0)
                            log = Log(
                                user='System (AI)',
                                action='auto_categorize_email',
                                details=f"AI auto-categorized new email ticket '{subject}' (ID: {ticket.id}) as '{ai_category}' with urgency '{ai_urgency}' (confidence: {confidence:.1%})"
                            )
                            db.session.add(log)
                            db.session.commit()
                        except Exception as log_error:
                            print(f"[DEBUG] Failed to log AI categorization: {log_error}", flush=True)
            # Save email message only if ticket exists and is not deleted, and not already saved
            if ticket:
                from sqlalchemy import and_
                exists = db.session.query(EmailMessage).filter(
                    and_(
                        EmailMessage.thread_id==thread_id,
                        EmailMessage.sender==sender,
                        EmailMessage.subject==subject,
                        EmailMessage.sent_at==created_at,
                        EmailMessage.message_id==msg.get('Message-ID'),
                        EmailMessage.in_reply_to==msg.get('In-Reply-To')
                    )
                ).first()
                if not exists:
                    import json
                    emsg = EmailMessage(
                        ticket_id=ticket.id,
                        thread_id=thread_id,
                        sender=sender,
                        subject=subject,
                        body=body,
                        sent_at=created_at,
                        attachments=json.dumps(attachments) if attachments else None,
                        message_id=msg.get('Message-ID'),
                        in_reply_to=msg.get('In-Reply-To')
                    )
                    db.session.add(emsg)
                    db.session.commit()
                    count += 1
            mail.store(num, '+FLAGS', r'\Seen')
        mail.logout()
    return count
