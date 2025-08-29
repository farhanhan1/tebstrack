"""
Test script to verify improved chatbot responses
"""
from app import create_app
from app.ai_service import get_ai_service

app = create_app()

with app.app_context():
    ai_service = get_ai_service()
    
    # Sample ticket context
    sample_ticket = {
        'id': 5,
        'subject': 'Help create vpn account',
        'sender': 'Farhan han <minecraftfarhan@gmail.com>',
        'category': 'SVN & VPN',
        'status': 'Open',
        'urgency': 'Medium',
        'created_at': 'August 30, 2025',
        'assigned_to': 'Unassigned',
        'body': 'I need VPN access to perform my work tasks.'
    }
    
    # Test different types of messages
    test_messages = [
        ("hi", "Simple greeting"),
        ("hello", "Basic greeting"), 
        ("thanks", "Casual thanks"),
        ("tell me about this ticket", "Explicit ticket request"),
        ("what should I do next?", "Next steps question"),
        ("how are you?", "General conversation"),
        ("what's the status?", "Status inquiry"),
        ("help me understand the category", "Category question")
    ]
    
    print("=== CHATBOT RESPONSE TESTING ===\n")
    
    for message, description in test_messages:
        print(f"🧪 TEST: {description}")
        print(f"📝 USER MESSAGE: '{message}'")
        
        try:
            # Test with ticket context
            response = ai_service.chatbot_response(message, sample_ticket)
            print(f"🤖 RESPONSE: {response}")
            print(f"📏 LENGTH: {len(response)} characters")
            
            # Show intent analysis
            intent = ai_service._analyze_user_intent(message)
            print(f"🧠 INTENT: {intent}")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("-" * 80)
    
    print("\n=== INTENT ANALYSIS TESTING ===\n")
    
    # Test intent analysis specifically
    intent_tests = [
        "hi",
        "hello there",
        "thanks a lot", 
        "tell me about this ticket",
        "what is the status",
        "explain the category",
        "how do I fix this",
        "good morning",
        "what should I do next",
        "can you help me"
    ]
    
    for test_msg in intent_tests:
        intent = ai_service._analyze_user_intent(test_msg)
        print(f"'{test_msg}' -> {intent}")
