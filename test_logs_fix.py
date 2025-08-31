from app import create_app
from app.models import Ticket, User
from app.ai_service import get_ai_service

app = create_app()

with app.app_context():
    # Test the chatbot route logic without the problematic logs query
    ticket = Ticket.query.get(4)
    if ticket:
        # Get assigned user if any
        assigned_user = None
        if ticket.assigned_to:
            assigned_user = User.query.get(ticket.assigned_to)
        
        ticket_context = {
            'id': ticket.id,
            'subject': ticket.subject,
            'body': ticket.description,
            'sender': ticket.sender,
            'category': ticket.category,
            'status': ticket.status,
            'urgency': ticket.urgency,
            'created_at': ticket.created_at.strftime('%Y-%m-%d %H:%M') if ticket.created_at else 'Unknown',
            'assigned_to': assigned_user.username if assigned_user else 'Unassigned',
            'recent_activity': []  # Empty as expected
        }
        
        print("✅ Ticket context created successfully")
        print(f"Ticket: {ticket_context['subject']}")
        print(f"Category: {ticket_context['category']}")
        print(f"Status: {ticket_context['status']}")
        
        # Test AI service
        ai_service = get_ai_service()
        try:
            response = ai_service.chatbot_response("tell me about this ticket", ticket_context)
            print("\n✅ AI Response generated successfully")
            print(f"Response length: {len(response)} characters")
            print(f"First 200 chars: {response[:200]}...")
        except Exception as e:
            print(f"❌ AI Service error: {e}")
    else:
        print("❌ Ticket not found")
