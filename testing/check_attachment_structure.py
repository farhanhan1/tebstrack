#!/usr/bin/env python3
"""
Check attachment data structure in the database
"""
from app.models import EmailMessage, db
from app import create_app
import json

app = create_app()
with app.app_context():
    # Get a few recent messages with attachments
    messages = EmailMessage.query.filter(EmailMessage.attachments.isnot(None)).limit(5).all()
    
    print("=== Current Attachment Data Structure ===")
    for i, msg in enumerate(messages):
        print(f"\nMessage {i+1} (ID: {msg.id}):")
        print(f"Subject: {msg.subject}")
        print(f"Raw attachments field: {msg.attachments}")
        
        if msg.attachments:
            try:
                attachments = json.loads(msg.attachments)
                print(f"Parsed attachments: {attachments}")
                for j, att in enumerate(attachments):
                    print(f"  Attachment {j+1}:")
                    for key, value in att.items():
                        print(f"    {key}: {value}")
            except Exception as e:
                print(f"Error parsing attachments: {e}")
        
        print("-" * 50)
