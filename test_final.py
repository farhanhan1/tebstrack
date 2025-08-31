from app import create_app
from app.models import Ticket, User
from app.ai_service import get_ai_service

app = create_app()

with app.app_context():
    # Test ticket retrieval and context building
    ticket = Ticket.query.get(4)
    if ticket:
        print("✅ Ticket found")
        print(f"Subject: {ticket.subject}")
        print(f"Description: {ticket.description}")
        print(f"Category: {ticket.category}")
        print(f"Status: {ticket.status}")
        print(f"Sender: {ticket.sender}")
        
        # Test assigned user
        assigned_user = None
        if ticket.assigned_to:
            assigned_user = User.query.get(ticket.assigned_to)
            print(f"Assigned to: {assigned_user.username if assigned_user else 'User not found'}")
        else:
            print("Assigned to: Unassigned")
        
        # Create context as the route would
        ticket_context = {
            'id': ticket.id,
            'subject': ticket.subject,
            'body': ticket.description,
            'sender': ticket.sender,
            'category': ticket.category,
            'status': ticket.status,
            'urgency': ticket.urgency,
        }
        
        print("\n🤖 Testing AI Service")
        ai_service = get_ai_service()
        try:
            response = ai_service.chatbot_response("tell me about this ticket", ticket_context)
            print("✅ AI Response generated successfully")
            print(f"Response length: {len(response)} characters")
            print(f"First 200 chars: {response[:200]}...")
        except Exception as e:
            print(f"❌ AI Service error: {e}")
    else:
        print("❌ Ticket #4 not found")
