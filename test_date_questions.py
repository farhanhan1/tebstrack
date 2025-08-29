"""
Test date-related questions for tickets
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
    
    # Test date-related questions
    date_questions = [
        "when was this ticket received",
        "when did this issue occur?",
        "what is the creation date?",
        "when was it created?",
        "when did this happen?",
        "what date was this reported?"
    ]
    
    print("=== DATE QUESTION TEST ===\n")
    
    for question in date_questions:
        print(f"USER: {question}")
        
        # Check intent first
        intent = ai_service._analyze_user_intent(question)
        print(f"INTENT: {intent}")
        
        # Get response
        response = ai_service.chatbot_response(question, sample_ticket)
        print(f"BOT: {response}")
        print(f"LENGTH: {len(response)} chars")
        print("-" * 40)
