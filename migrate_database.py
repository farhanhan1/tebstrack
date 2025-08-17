#!/usr/bin/env python3
"""
Database migration script to add missing columns to EmailMessage table
"""

import sqlite3
import os

def migrate_database():
    """Add missing columns to EmailMessage table"""
    
    db_path = "instance/tickets.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Starting database migration...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(email_message)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print(f"📋 Current columns: {columns}")
        
        # Add missing columns
        columns_to_add = [
            ('cc_emails', 'TEXT'),
            ('tagged_users', 'TEXT')
        ]
        
        for column_name, column_type in columns_to_add:
            if column_name not in columns:
                try:
                    sql = f"ALTER TABLE email_message ADD COLUMN {column_name} {column_type}"
                    cursor.execute(sql)
                    print(f"✅ Added column: {column_name}")
                except Exception as e:
                    print(f"❌ Failed to add column {column_name}: {e}")
            else:
                print(f"✅ Column {column_name} already exists")
        
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(email_message)")
        updated_columns = [row[1] for row in cursor.fetchall()]
        
        print(f"\n📋 Updated columns: {updated_columns}")
        print("✅ Database migration completed successfully!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_database()
