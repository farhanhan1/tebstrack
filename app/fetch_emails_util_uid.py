"""
Optimized UID-based email fetching utility for TebsTrack

This module provides robust, scalable email fetching using IMAP UIDs
to avoid re-processing emails and handle large mailboxes efficiently.
"""

import imaplib
import email
import email.utils
import os
import logging
from datetime import datetime, timezone
from email.header import decode_header
from dotenv import load_dotenv
from .models import db, Ticket, EmailMessage, EmailFetchState
import json
import uuid
import time

# Configure logging
logger = logging.getLogger(__name__)

def parse_email(msg):
    """
    Parse email message and extract relevant fields
    Returns: (subject, sender, date, body, message_id, thread_id, attachments, in_reply_to)
    """
    # Extract basic headers
    subject = msg.get('subject', '')
    sender_name, sender_email = email.utils.parseaddr(msg.get('from', ''))
    sender = msg.get('from', '')
    date = msg.get('date', '')
    message_id = msg.get('Message-ID', '')
    in_reply_to = msg.get('In-Reply-To', '')
    
    # Use References header to find the root of the thread if available
    references = msg.get('References', '')
    if references:
        # Use the first reference as thread_id
        thread_id = references.split()[0] if references.split() else message_id
    elif in_reply_to:
        # Use In-Reply-To as thread_id
        thread_id = in_reply_to
    else:
        # This is likely the start of a thread
        thread_id = message_id
    
    # Decode subject if needed
    if subject:
        try:
            decoded_parts = decode_header(subject)
            subject = ''.join([
                part.decode(encoding or 'utf-8') if isinstance(part, bytes) else str(part)
                for part, encoding in decoded_parts
            ])
        except Exception as e:
            logger.warning(f"Failed to decode subject: {e}")
            # Keep original subject if decoding fails
    
    # Extract body and attachments
    body = ''
    attachments = []
    inline_images = {}  # Store inline images by Content-ID
    
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = part.get('Content-Disposition', '')
            content_id = part.get('Content-ID', '').strip('<>')
            
            if content_type == 'text/plain' and 'attachment' not in content_disposition:
                try:
                    charset = part.get_content_charset() or 'utf-8'
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode(charset, errors='replace')
                except Exception as e:
                    logger.warning(f"Failed to decode email body: {e}")
                    body = "Error decoding email body"
            elif 'attachment' in content_disposition:
                # Regular file attachments
                filename = part.get_filename()
                if filename:
                    # Save attachment file
                    attachment_data = part.get_payload(decode=True)
                    if attachment_data:
                        safe_filename = f"{uuid.uuid4().hex}_{filename}"
                        attachment_path = os.path.join('attachments', safe_filename)
                        os.makedirs('attachments', exist_ok=True)
                        
                        with open(attachment_path, 'wb') as f:
                            f.write(attachment_data)
                        
                        attachments.append({
                            'filename': filename,
                            'url': f'/attachments/{safe_filename}',
                            'is_image': content_type.startswith('image/'),
                            'size': len(attachment_data)
                        })
            elif content_id and content_type.startswith('image/'):
                # Inline images with Content-ID
                filename = part.get_filename() or f"inline_image_{content_id}.{content_type.split('/')[-1]}"
                attachment_data = part.get_payload(decode=True)
                if attachment_data:
                    safe_filename = f"{uuid.uuid4().hex}_{filename}"
                    attachment_path = os.path.join('attachments', safe_filename)
                    os.makedirs('attachments', exist_ok=True)
                    
                    with open(attachment_path, 'wb') as f:
                        f.write(attachment_data)
                    
                    # Store in inline_images for CID replacement
                    inline_images[content_id] = safe_filename
                    
                    # Also add to attachments list
                    attachments.append({
                        'filename': filename,
                        'url': f'/attachments/{safe_filename}',
                        'is_image': True,
                        'size': len(attachment_data)
                    })
    else:
        try:
            charset = msg.get_content_charset() or 'utf-8'
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode(charset, errors='replace')
        except Exception as e:
            logger.warning(f"Failed to decode simple email body: {e}")
            body = "Error decoding email body"
    
    # Replace CID references with actual image links
    if body and inline_images:
        import re
        for content_id, filename in inline_images.items():
            # Replace [cid:content_id] with a note about the inline image
            cid_pattern = f"\\[cid:{re.escape(content_id)}\\]"
            body = re.sub(cid_pattern, f"[Inline image: {filename}]", body)
    
    # Clean up Outlook inline image URLs that don't work outside of Outlook
    if body:
        import re
        # Remove Outlook/Office365 inline image URLs
        outlook_patterns = [
            r'\[https://attachment\.outlook\.live\.net/[^\]]+\]',
            r'\[https://[^/]*\.outlook\.com/[^\]]+\]',
            r'\[https://.*?\.office\.com/[^\]]+\]',
            r'\[https://.*outlook.*?/service\.svc/[^\]]+\]'
        ]
        
        for pattern in outlook_patterns:
            body = re.sub(pattern, '[Inline image not available - please attach images as files instead]', body)
    
    return subject, sender, date, body, message_id, thread_id, attachments, in_reply_to


def ticket_exists_by_message_id(message_id):
    """Check if a ticket/email already exists by Message-ID"""
    if not message_id:
        return False
    return EmailMessage.query.filter_by(message_id=message_id).first() is not None


def process_email(msg, mailbox, uid):
    """
    Process a single email message and create/update tickets
    Returns: (success: bool, ticket_id: int or None, is_new_ticket: bool)
    """
    try:
        subject, sender, date, body, message_id, thread_id, attachments, in_reply_to = parse_email(msg)
        
        # Skip if we already processed this email
        if ticket_exists_by_message_id(message_id):
            logger.debug(f"Email {message_id} already processed, skipping")
            return True, None, False
        
        # Skip emails from tebstrack to avoid processing our own sent emails
        GMAIL_USER = os.getenv('IMAP_USER', os.getenv('GMAIL_USER', ''))
        if sender and GMAIL_USER and GMAIL_USER.lower() in sender.lower():
            logger.debug(f"Skipping email from tebstrack: {sender}")
            return True, None, False
        
        # Parse date
        created_at = datetime.utcnow()
        if date:
            try:
                parsed_tuple = email.utils.parsedate_tz(date)
                if parsed_tuple:
                    timestamp = email.utils.mktime_tz(parsed_tuple)
                    created_at = datetime.fromtimestamp(timestamp, tz=timezone.utc).replace(tzinfo=None)
            except Exception as e:
                logger.warning(f"Failed to parse date '{date}': {e}")
        
        # Find existing ticket for this thread
        ticket = None
        is_new_ticket = False
        
        if thread_id:
            ticket = Ticket.query.filter_by(thread_id=thread_id).first()
        
        # Only create a new ticket if:
        # 1. No existing ticket found
        # 2. Email is from INBOX (not sent mail)
        # 3. Sender is not our support email
        if not ticket and mailbox == 'INBOX':
            if not (sender and GMAIL_USER and GMAIL_USER.lower() in sender.lower()):
                ticket = Ticket(
                    subject=subject or 'No Subject',
                    sender=sender,
                    created_at=created_at,
                    status='Open',
                    category='General',
                    urgency='Medium',
                    description=body or 'No description',
                    thread_id=thread_id
                )
                db.session.add(ticket)
                db.session.flush()  # Get the ticket ID
                is_new_ticket = True
                logger.info(f"Created new ticket {ticket.id} for email: {subject}")
        
        # Save email message if we have a ticket
        if ticket:
            email_msg = EmailMessage(
                ticket_id=ticket.id,
                thread_id=thread_id,
                sender=sender,
                subject=subject,
                body=body,
                sent_at=created_at,
                attachments=json.dumps(attachments) if attachments else None,
                message_id=message_id,
                in_reply_to=in_reply_to
            )
            db.session.add(email_msg)
            logger.debug(f"Added email message for ticket {ticket.id}")
        
        db.session.commit()
        return True, ticket.id if ticket else None, is_new_ticket
        
    except Exception as e:
        logger.error(f"Failed to process email UID {uid}: {e}")
        db.session.rollback()
        return False, None, False


def fetch_and_store_emails():
    """
    Fetch and store emails using UID-based incremental approach
    Returns: Number of new emails processed
    """
    load_dotenv()
    
    # Configuration
    IMAP_HOST = os.getenv('IMAP_HOST', 'imap.gmail.com')
    IMAP_PORT = int(os.getenv('IMAP_PORT', 993))
    IMAP_USER = os.getenv('IMAP_USER', os.getenv('GMAIL_USER', ''))
    IMAP_PASS = os.getenv('IMAP_PASS', os.getenv('GMAIL_APP_PASSWORD', ''))
    
    # Safety limits
    MAX_EMAILS_PER_FETCH = int(os.getenv('MAX_EMAILS_PER_FETCH', 100))
    MAILBOXES_TO_PROCESS = os.getenv('MAILBOXES_TO_PROCESS', 'INBOX').split(',')
    
    if not IMAP_USER or not IMAP_PASS:
        logger.error("Missing IMAP credentials in environment variables")
        raise Exception("Missing IMAP credentials (IMAP_USER/IMAP_PASS)")
    
    total_processed = 0
    new_tickets = 0
    
    try:
        logger.info(f"Starting UID-based email fetch for {len(MAILBOXES_TO_PROCESS)} mailboxes")
        
        # Connect to IMAP server
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(IMAP_USER, IMAP_PASS)
        
        for mailbox in MAILBOXES_TO_PROCESS:
            mailbox = mailbox.strip()
            logger.info(f"Processing mailbox: {mailbox}")
            
            try:
                # Select mailbox
                status, data = mail.select(mailbox)
                if status != 'OK':
                    logger.warning(f"Failed to select mailbox {mailbox}: {data}")
                    continue
                
                # Get last processed UID
                last_uid = EmailFetchState.get_last_uid(mailbox)
                logger.info(f"Last processed UID for {mailbox}: {last_uid}")
                
                # Search for emails with UID > last_uid
                if last_uid > 0:
                    search_criteria = f'UID {last_uid + 1}:*'
                else:
                    # First time - get last 50 emails to avoid overwhelming
                    search_criteria = 'ALL'
                
                result, messages = mail.uid('search', None, search_criteria)
                
                if result != 'OK' or not messages[0]:
                    logger.info(f"No new emails found in {mailbox}")
                    continue
                
                uids = messages[0].split()
                
                # Limit emails processed per fetch for safety
                if len(uids) > MAX_EMAILS_PER_FETCH:
                    if last_uid == 0:
                        # First time - take the most recent emails
                        uids = uids[-MAX_EMAILS_PER_FETCH:]
                    else:
                        # Subsequent fetches - take the oldest new emails first
                        uids = uids[:MAX_EMAILS_PER_FETCH]
                    logger.warning(f"Limited to {MAX_EMAILS_PER_FETCH} emails for safety")
                
                logger.info(f"Processing {len(uids)} emails from {mailbox}")
                
                emails_processed = 0
                highest_uid = last_uid
                
                for uid_bytes in uids:
                    uid = int(uid_bytes.decode())
                    
                    try:
                        # Fetch email
                        result, data = mail.uid('fetch', uid_bytes, '(RFC822)')
                        if result != 'OK':
                            logger.warning(f"Failed to fetch UID {uid}")
                            continue
                        
                        raw_email = data[0][1]
                        msg = email.message_from_bytes(raw_email)
                        
                        # Process email
                        success, ticket_id, is_new_ticket = process_email(msg, mailbox, uid)
                        
                        if success:
                            emails_processed += 1
                            highest_uid = max(highest_uid, uid)
                            
                            if is_new_ticket:
                                new_tickets += 1
                            
                            if emails_processed % 10 == 0:
                                logger.info(f"Processed {emails_processed} emails from {mailbox}")
                        
                    except Exception as e:
                        logger.error(f"Failed to process UID {uid} in {mailbox}: {e}")
                        continue
                
                # Update the last processed UID
                if emails_processed > 0:
                    EmailFetchState.update_last_uid(mailbox, highest_uid, emails_processed)
                    total_processed += emails_processed
                    logger.info(f"Completed {mailbox}: processed {emails_processed} emails, highest UID: {highest_uid}")
                else:
                    logger.info(f"No new emails processed in {mailbox}")
                    
            except Exception as e:
                logger.error(f"Error processing mailbox {mailbox}: {e}")
                continue
        
        mail.logout()
        
        logger.info(f"Email fetch completed: {total_processed} emails processed, {new_tickets} new tickets created")
        return new_tickets
        
    except Exception as e:
        logger.error(f"Email fetch failed: {e}")
        try:
            mail.logout()
        except:
            pass
        raise


def get_fetch_statistics():
    """Get statistics about email fetching"""
    stats = {}
    
    for state in EmailFetchState.query.all():
        stats[state.mailbox] = {
            'last_uid': state.last_uid,
            'last_fetch_time': state.last_fetch_time.isoformat() if state.last_fetch_time else None,
            'total_emails_processed': state.total_emails_processed,
            'created_at': state.created_at.isoformat() if state.created_at else None,
            'updated_at': state.updated_at.isoformat() if state.updated_at else None
        }
    
    return stats


def reset_fetch_state(mailbox=None):
    """Reset fetch state for debugging/maintenance (admin only)"""
    if mailbox:
        state = EmailFetchState.query.filter_by(mailbox=mailbox).first()
        if state:
            db.session.delete(state)
    else:
        EmailFetchState.query.delete()
    
    db.session.commit()
    logger.warning(f"Reset fetch state for mailbox: {mailbox or 'ALL'}")
