
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from flask_login import UserMixin
import json
import os

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
    message_id = db.Column(db.String(255), nullable=True, unique=True)
    in_reply_to = db.Column(db.String(255), nullable=True)
    cc_emails = db.Column(db.Text)  # JSON list of CC email addresses
    tagged_users = db.Column(db.Text)  # JSON list of tagged user IDs

    def get_attachments(self):
        if self.attachments:
            return json.loads(self.attachments)
        return []

    def get_cc_emails(self):
        if self.cc_emails:
            return json.loads(self.cc_emails)
        return []

    def get_tagged_users(self):
        if self.tagged_users:
            return json.loads(self.tagged_users)
        return []

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='infra')  # 'admin' or 'infra'

class UserSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    pagination_enabled = db.Column(db.Boolean, default=False)
    tickets_per_page = db.Column(db.Integer, default=10)
    
    user = db.relationship('User', backref=db.backref('settings', uselist=False))

    @classmethod
    def get_user_settings(cls, user_id):
        """Get or create user settings with defaults"""
        settings = cls.query.filter_by(user_id=user_id).first()
        if not settings:
            settings = cls(user_id=user_id, pagination_enabled=False, tickets_per_page=10)
            db.session.add(settings)
            db.session.commit()
        return settings


class SystemSettings(db.Model):
    """System-wide settings for TeBSTrack"""
    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column(db.String(100), unique=True, nullable=False)
    setting_value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_setting(cls, key, default=None):
        """Get a system setting value"""
        setting = cls.query.filter_by(setting_key=key).first()
        return setting.setting_value if setting else default
    
    @classmethod
    def set_setting(cls, key, value, description=None):
        """Set a system setting value"""
        setting = cls.query.filter_by(setting_key=key).first()
        if setting:
            setting.setting_value = value
            setting.updated_at = datetime.utcnow()
            if description:
                setting.description = description
        else:
            setting = cls(
                setting_key=key,
                setting_value=value,
                description=description
            )
            db.session.add(setting)
        db.session.commit()
        return setting
    
    @classmethod
    def get_openai_api_key(cls):
        """Get the OpenAI API key from settings or environment"""
        # First check if custom API key is set in system settings
        custom_key = cls.get_setting('openai_api_key')
        if custom_key:
            return custom_key
        # Fall back to environment variable
        return os.getenv('OPENAI_API_KEY')


class EmailTemplate(db.Model):
    """Email templates for automated responses"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    use_case_description = db.Column(db.Text, nullable=True)  # When to use this template
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship to action steps
    action_steps = db.relationship('TemplateActionStep', backref='template', lazy=True, cascade='all, delete-orphan')
    
    creator = db.relationship('User', backref='created_templates')


class TemplateActionStep(db.Model):
    """Action steps associated with email templates"""
    id = db.Column(db.Integer, primary_key=True)
    template_id = db.Column(db.Integer, db.ForeignKey('email_template.id'), nullable=False)
    step_order = db.Column(db.Integer, nullable=False)  # Order of execution
    step_type = db.Column(db.String(50), nullable=False)  # 'manual', 'web_action', 'api_call', etc.
    step_title = db.Column(db.String(200), nullable=False)
    step_description = db.Column(db.Text, nullable=False)
    step_config = db.Column(db.Text, nullable=True)  # JSON config for automated steps
    is_automated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class TicketTemplateRecommendation(db.Model):
    """AI recommendations for email templates on tickets"""
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    template_id = db.Column(db.Integer, db.ForeignKey('email_template.id'), nullable=True)
    confidence_score = db.Column(db.Float, nullable=True)  # AI confidence (0-1)
    ai_reasoning = db.Column(db.Text, nullable=True)  # Why AI recommended this template
    is_user_selected = db.Column(db.Boolean, default=False)  # Did user manually select this?
    selected_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    ticket = db.relationship('Ticket', backref='template_recommendations')
    template = db.relationship('EmailTemplate', backref='recommendations')
    selector = db.relationship('User', backref='template_selections')


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


class EmailFetchState(db.Model):
    """Track the state of email fetching to enable incremental UID-based fetching"""
    __tablename__ = 'email_fetch_state'
    
    id = db.Column(db.Integer, primary_key=True)
    mailbox = db.Column(db.String(100), nullable=False, unique=True)  # 'INBOX', 'SENT', etc.
    last_uid = db.Column(db.Integer, nullable=False, default=0)  # Last processed UID
    last_fetch_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_emails_processed = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @classmethod
    def get_last_uid(cls, mailbox):
        """Get the last processed UID for a mailbox"""
        state = cls.query.filter_by(mailbox=mailbox).first()
        return state.last_uid if state else 0
    
    @classmethod
    def update_last_uid(cls, mailbox, uid, emails_processed=0):
        """Update the last processed UID for a mailbox"""
        state = cls.query.filter_by(mailbox=mailbox).first()
        if state:
            state.last_uid = max(state.last_uid, uid)  # Ensure we only move forward
            state.last_fetch_time = datetime.utcnow()
            state.total_emails_processed += emails_processed
            state.updated_at = datetime.utcnow()
        else:
            state = cls(
                mailbox=mailbox,
                last_uid=uid,
                total_emails_processed=emails_processed
            )
            db.session.add(state)
        db.session.commit()
        return state
