"""
Test script for ticket-aware chatbot functionality
"""
from app import create_app
from app.ai_service import get_ai_service

app = create_app()

# Mock ticket context for testing
mock_ticket_context = {
    'id': 4,
    'subject': 'Server Access Request', 
    'body': 'I need access to the production server to deploy the latest updates. My user account is john.doe@company.com and I need read/write access to /var/www/html/',
    'sender': 'john.doe@company.com',
    'category': 'Server Access',
    'status': 'Open',
    'urgency': 'Medium',
    'created_at': '2025-08-28 10:30',
    'assigned_to': 'Unassigned',
    'recent_activity': [
        {
            'action': 'Ticket Created',
            'details': 'New ticket submitted',
            'timestamp': '2025-08-28 10:30',
            'user': 'john.doe'
        }
    ]
}

with app.app_context():
    ai_service = get_ai_service()
    
    # Test different types of questions
    test_questions = [
        "Tell me about this ticket",
        "What should I do next?", 
        "What category is this?",
        "Is this urgent?",
        "Who submitted this?"
    ]
    
    print("🤖 Testing Ticket-Aware Chatbot")
    print("=" * 50)
    print(f"Context: Ticket #{mock_ticket_context['id']} - {mock_ticket_context['subject']}")
    print("=" * 50)
    
    for question in test_questions:
        print(f"\n❓ Question: {question}")
        print("🤖 Response:")
        
        try:
            response = ai_service.chatbot_response(question, mock_ticket_context)
            print(response)
        except Exception as e:
            print(f"Error: {e}")
        
        print("-" * 40)
