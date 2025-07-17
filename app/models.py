from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

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
    # ...add more fields as needed...
