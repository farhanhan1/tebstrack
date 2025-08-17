#!/usr/bin/env python3
"""
Test script for UID-based email fetching system

This script tests the new UID-based email fetching to ensure it works correctly
and provides performance metrics.
"""

import sys
import os
import time
from datetime import datetime

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

def test_uid_system():
    """Test the UID-based email fetching system"""
    
    print("🧪 TESTING UID-BASED EMAIL FETCHING SYSTEM")
    print("=" * 50)
    
    # Test database connection and models
    try:
        from app import create_app
        from app.models import db, EmailFetchState, Ticket, EmailMessage
        from app.fetch_emails_util_uid import fetch_and_store_emails, get_fetch_statistics, reset_fetch_state
        
        app = create_app()
        
        with app.app_context():
            # Initialize database
            db.create_all()
            print("✅ Database connection successful")
            
            # Check current fetch state
            print("\n📊 Current Fetch State:")
            stats = get_fetch_statistics()
            
            if stats:
                for mailbox, data in stats.items():
                    print(f"   {mailbox}:")
                    print(f"     Last UID: {data['last_uid']}")
                    print(f"     Total Processed: {data['total_emails_processed']}")
                    print(f"     Last Fetch: {data['last_fetch_time']}")
            else:
                print("   No previous fetch state found (first run)")
            
            # Test configuration
            print("\n🔧 Configuration Check:")
            IMAP_USER = os.getenv('IMAP_USER', os.getenv('GMAIL_USER', ''))
            IMAP_PASS = os.getenv('IMAP_PASS', os.getenv('GMAIL_APP_PASSWORD', ''))
            MAX_EMAILS = os.getenv('MAX_EMAILS_PER_FETCH', '100')
            MAILBOXES = os.getenv('MAILBOXES_TO_PROCESS', 'INBOX')
            
            print(f"   IMAP User: {IMAP_USER}")
            print(f"   IMAP Pass: {'*' * len(IMAP_PASS) if IMAP_PASS else 'NOT SET'}")
            print(f"   Max Emails per Fetch: {MAX_EMAILS}")
            print(f"   Mailboxes: {MAILBOXES}")
            
            if not IMAP_USER or not IMAP_PASS:
                print("❌ Missing IMAP credentials - cannot test actual fetching")
                return False
            
            # Test email fetching
            print("\n📧 Testing Email Fetch...")
            start_time = time.time()
            
            try:
                new_tickets = fetch_and_store_emails()
                fetch_time = time.time() - start_time
                
                print(f"✅ Email fetch completed successfully!")
                print(f"   New tickets created: {new_tickets}")
                print(f"   Fetch time: {fetch_time:.2f} seconds")
                
                # Show updated statistics
                print("\n📈 Updated Fetch State:")
                updated_stats = get_fetch_statistics()
                
                for mailbox, data in updated_stats.items():
                    print(f"   {mailbox}:")
                    print(f"     Last UID: {data['last_uid']}")
                    print(f"     Total Processed: {data['total_emails_processed']}")
                    print(f"     Last Fetch: {data['last_fetch_time']}")
                
                # Database statistics
                total_tickets = Ticket.query.count()
                total_emails = EmailMessage.query.count()
                
                print(f"\n📊 Database Statistics:")
                print(f"   Total Tickets: {total_tickets}")
                print(f"   Total Email Messages: {total_emails}")
                
                return True
                
            except Exception as e:
                print(f"❌ Email fetch failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False


def test_performance():
    """Test performance characteristics"""
    
    print("\n⚡ PERFORMANCE TEST")
    print("=" * 30)
    
    try:
        from app import create_app
        from app.models import db, EmailFetchState
        
        app = create_app()
        
        with app.app_context():
            # Simulate multiple fetch operations
            test_runs = 3
            fetch_times = []
            
            for i in range(test_runs):
                print(f"\n🔄 Test Run {i+1}/{test_runs}")
                start_time = time.time()
                
                from app.fetch_emails_util_uid import fetch_and_store_emails
                new_tickets = fetch_and_store_emails()
                
                fetch_time = time.time() - start_time
                fetch_times.append(fetch_time)
                
                print(f"   Time: {fetch_time:.2f}s, New tickets: {new_tickets}")
                
                # Small delay between runs
                time.sleep(1)
            
            # Performance summary
            avg_time = sum(fetch_times) / len(fetch_times)
            max_time = max(fetch_times)
            min_time = min(fetch_times)
            
            print(f"\n📊 Performance Summary:")
            print(f"   Average fetch time: {avg_time:.2f} seconds")
            print(f"   Fastest fetch: {min_time:.2f} seconds")
            print(f"   Slowest fetch: {max_time:.2f} seconds")
            
            if avg_time < 10:
                print("✅ Performance: EXCELLENT (< 10s)")
            elif avg_time < 30:
                print("✅ Performance: GOOD (< 30s)")
            elif avg_time < 60:
                print("⚠️  Performance: ACCEPTABLE (< 60s)")
            else:
                print("❌ Performance: SLOW (> 60s) - consider optimization")
                
    except Exception as e:
        print(f"❌ Performance test failed: {e}")


def main():
    """Main test function"""
    
    print("TebsTrack UID-Based Email Fetching Test")
    print("Date:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print()
    
    # Test basic functionality
    success = test_uid_system()
    
    if success:
        # Test performance if basic test passed
        test_performance()
        
        print("\n🎉 ALL TESTS COMPLETED!")
        print("\n💡 Next Steps:")
        print("   1. Monitor the fetch statistics via /fetch_statistics endpoint")
        print("   2. Test the refresh button in the web interface")
        print("   3. Send a test email and verify it's processed correctly")
        print("   4. Check performance with larger email volumes")
        
    else:
        print("\n💥 TESTS FAILED!")
        print("   Check your .env configuration and network connectivity")


if __name__ == "__main__":
    main()
