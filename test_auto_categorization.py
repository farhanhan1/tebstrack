"""
Test script to verify auto-categorization functionality for new email tickets
"""
from app import create_app
from app.models import Category, Ticket, Log, db
from app.ai_service import get_ai_service

app = create_app()

with app.app_context():
    # Check available categories
    categories = [c.name for c in Category.query.all()]
    print('Available categories:', categories)
    print('Total categories:', len(categories))
    
    # Test AI categorization
    try:
        ai_service = get_ai_service()
        
        # Test with a sample email
        test_subject = "My laptop won't start"
        test_body = "Hi, I tried to turn on my laptop this morning but it won't boot up. The power light comes on but the screen stays black. I have an important presentation today. Please help!"
        test_sender = "john.doe@company.com"
        
        print(f"\nTesting AI categorization for:")
        print(f"Subject: {test_subject}")
        print(f"Body: {test_body[:100]}...")
        print(f"Sender: {test_sender}")
        
        result = ai_service.categorize_ticket(test_subject, test_body, test_sender)
        
        print(f"\nAI Categorization Result:")
        print(f"Category: {result.get('category', 'N/A')}")
        print(f"Urgency: {result.get('urgency', 'N/A')}")
        print(f"Confidence: {result.get('confidence', 0):.2%}")
        print(f"Reasoning: {result.get('reasoning', 'N/A')}")
        
        # Check if suggested category exists
        suggested_category = result.get('category', 'General')
        category_obj = Category.query.filter_by(name=suggested_category).first()
        if category_obj:
            print(f"✅ Category '{suggested_category}' exists in database")
        else:
            print(f"❌ Category '{suggested_category}' NOT found in database, will fallback to 'General'")
            
    except Exception as e:
        print(f"❌ AI categorization failed: {e}")
        print("This is expected if OpenAI API key is not configured")
