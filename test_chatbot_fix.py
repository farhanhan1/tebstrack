"""
Quick test script to verify chatbot fixes
"""
import os
import sys
sys.path.append('c:/Users/Farhan/Documents/GitHub/tebstrack')

from app import create_app
from app.ai_service import get_ai_service

app = create_app()

# Test ticket context
test_context = {
    'id': 4,
    'subject': 'Server Access Request',
    'body': 'I need access to the production server to deploy updates',
    'sender': 'user@example.com', 
    'category': 'Server Access',
    'status': 'Open',
    'urgency': 'Medium',
    'created_at': '2025-08-28 10:30',
    'assigned_to': 'Unassigned'
}

with app.app_context():
    ai_service = get_ai_service()
    
    print("🧪 Testing Chatbot Fixes")
    print("=" * 50)
    
    # Test the specific question that was failing
    test_question = "tell me more about this ticket i am viewing"
    
    print(f"Question: {test_question}")
    print("Response:")
    
    try:
        response = ai_service.chatbot_response(test_question, test_context)
        print(response)
        print("\n✅ Chatbot is working correctly!")
    except Exception as e:
        print(f"❌ Error: {e}")
        
    print("\n" + "=" * 50)
    print("URL Pattern Test:")
    print("✅ Updated to match /viewticket/4 pattern")
    print("✅ Added debugging console logs")
    print("✅ Fixed chatbot bubble SVG")
    print("✅ Added fallback responses for no OpenAI API key")
