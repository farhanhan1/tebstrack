#!/usr/bin/env python3
"""
Debug script to check attachment data in EmailMessage records
"""

import sys
import os
import json

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def check_attachments():
    """Check how attachments are stored in the database"""
    
    print("🔍 DEBUGGING ATTACHMENT STORAGE")
    print("=" * 40)
    
    try:
        from app import create_app
        from app.models import db, EmailMessage, Ticket
        
        app = create_app()
        
        with app.app_context():
            # Find some recent tickets with email threads
            tickets_with_threads = Ticket.query.filter(Ticket.thread_id.isnot(None)).order_by(Ticket.created_at.desc()).limit(3).all()
            
            if not tickets_with_threads:
                print("❌ No tickets with email threads found")
                return
            
            for ticket in tickets_with_threads:
                print(f"\n📋 Ticket {ticket.id}: {ticket.subject}")
                print(f"   Thread ID: {ticket.thread_id}")
                
                # Get all email messages for this thread
                messages = EmailMessage.query.filter_by(thread_id=ticket.thread_id).order_by(EmailMessage.sent_at.asc()).all()
                
                print(f"   Messages in thread: {len(messages)}")
                
                for i, msg in enumerate(messages):
                    print(f"\n   📧 Message {i+1}:")
                    print(f"      From: {msg.sender}")
                    print(f"      Subject: {msg.subject}")
                    print(f"      Sent: {msg.sent_at}")
                    print(f"      Message-ID: {msg.message_id}")
                    
                    # Check attachments
                    if msg.attachments:
                        try:
                            attachments = json.loads(msg.attachments)
                            print(f"      Attachments ({len(attachments)}):")
                            for att in attachments:
                                print(f"        - {att.get('filename', 'Unknown')} ({'image' if att.get('is_image') else 'file'})")
                        except Exception as e:
                            print(f"      ❌ Error parsing attachments: {e}")
                            print(f"      Raw attachments data: {msg.attachments}")
                    else:
                        print(f"      Attachments: None")
                
                print(f"   " + "-" * 50)
                
    except Exception as e:
        print(f"❌ Debug failed: {e}")

if __name__ == "__main__":
    check_attachments()
