#!/usr/bin/env python3
"""Initialize database tables"""

from run import app
from app.models import db

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print('Database tables created successfully')
