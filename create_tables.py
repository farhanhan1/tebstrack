#!/usr/bin/env python3

"""
Script to create database tables for TeBSTrack
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the Flask app and database
from app import create_app, db

def create_tables():
    """Create all database tables"""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Print created tables
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"📊 Created {len(tables)} tables:")
        for table in sorted(tables):
            print(f"   - {table}")

if __name__ == "__main__":
    create_tables()
