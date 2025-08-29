"""
Final test of ultra-concise chatbot responses
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
    
    # Test cases showing before/after improvement
    print("=== FINAL CONCISE CHATBOT TEST ===\n")
    
    test_messages = [
        "hi",
        "what's the status?", 
        "help me understand the category",
        "what should I do next?",
        "tell me about this ticket"
    ]
    
    for message in test_messages:
        print(f"USER: {message}")
        response = ai_service.chatbot_response(message, sample_ticket)
        print(f"BOT:  {response}")
        print(f"      ({len(response)} characters)\n")
