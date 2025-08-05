
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from flask_login import UserMixin
import json

db = SQLAlchemy()

class LoginAttempt(db.Model):
    __tablename__ = 'login_attempts'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(64), unique=True, nullable=False)
    fail_count = db.Column(db.Integer, default=0)
    lockout_until = db.Column(db.Float, default=0)  # store as timestamp
    last_attempt = db.Column(db.DateTime, default=datetime.utcnow)

class EmailMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'))
    thread_id = db.Column(db.String(255))
    sender = db.Column(db.String(150))
    subject = db.Column(db.String(255))
    body = db.Column(db.Text)
    sent_at = db.Column(db.DateTime)
    attachments = db.Column(db.Text)  # JSON list of dicts: [{filename, is_image, url}]
    message_id = db.Column(db.String(255), nullable=True)
    in_reply_to = db.Column(db.String(255), nullable=True)

    def get_attachments(self):
        if self.attachments:
            return json.loads(self.attachments)
        return []

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='infra')  # 'admin' or 'infra'


class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    user = db.Column(db.String(150), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    sender = db.Column(db.String(150), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    urgency = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Open')
    resolution = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())
    thread_id = db.Column(db.String(255), nullable=True)  # For email threading
    audit_log = db.Column(db.Text, nullable=True)  # JSON or text log
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
