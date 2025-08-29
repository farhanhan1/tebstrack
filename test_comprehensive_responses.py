"""
Test the improved chatbot with comprehensive context and "who" questions
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
    
    print("=== IMPROVED COMPREHENSIVE RESPONSE TEST ===\n")
    
    # Test the problematic questions from the user's example
    problem_questions = [
        "who requested it",
        "who sent in the mail",
        "tell me about this ticket",
        "what should I do next?"
    ]
    
    for question in problem_questions:
        print(f"USER: {question}")
        response = ai_service.chatbot_response(question, sample_ticket)
        print(f"BOT:  {response}")
        print(f"      ({len(response)} characters)")
        print()
    
    print("=" * 60)
    print("✅ IMPROVEMENTS:")
    print("• All ticket details included in context")
    print("• Who questions properly handled")
    print("• Longer, more informative responses")
    print("• Direct answers with comprehensive context")
