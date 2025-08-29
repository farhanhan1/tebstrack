"""
Comprehensive test of user context integration
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.ai_service import get_ai_service

def test_user_context_integration():
    print("=== Testing User Context Integration ===\n")
    
    app = create_app()
    
    with app.app_context():
        ai_service = get_ai_service()
        
        # Test user contexts
        user_contexts = [
            {'username': 'farhan', 'role': 'infra', 'id': 1},
            {'username': 'admin', 'role': 'admin', 'id': 2},
            {'username': 'john', 'role': 'infra', 'id': 3}
        ]
        
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
        
        print("🧪 TESTING USER-AWARE RESPONSES:\n")
        
        test_cases = [
            ("hi", "Casual greeting"),
            ("hello there", "Formal greeting"),
            ("tell me about this ticket", "Ticket inquiry"),
            ("what should I do next?", "Action guidance"),
            ("who requested it", "Simple question"),
            ("status?", "Status check")
        ]
        
        for user_context in user_contexts[:2]:  # Test with first 2 users
            print(f"=== USER: {user_context['username']} ({user_context['role']}) ===")
            
            for question, test_type in test_cases:
                print(f"\nTEST: {test_type}")
                print(f"USER: {question}")
                
                # Test without ticket context
                response_no_ticket = ai_service.chatbot_response(question, None, user_context)
                print(f"NO TICKET:  {response_no_ticket}")
                
                # Test with ticket context
                response_with_ticket = ai_service.chatbot_response(question, sample_ticket, user_context)
                print(f"WITH TICKET: {response_with_ticket}")
                
                print("-" * 60)
            
            print("\n" + "=" * 80 + "\n")
        
        print("✅ USER CONTEXT VERIFICATION:")
        print("• Responses should include user names in greetings")
        print("• Different users should get personalized responses")
        print("• Role information should be considered")
        print("• Ticket context should work with user context")
        print("• Fallback responses should be user-aware")

if __name__ == "__main__":
    test_user_context_integration()
