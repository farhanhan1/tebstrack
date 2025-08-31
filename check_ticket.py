from app import create_app
from app.models import Ticket, Log as TicketLog

app = create_app()

with app.app_context():
    # Check if ticket #4 exists
    ticket = Ticket.query.get(4)
    if ticket:
        print(f"Ticket #4 found:")
        print(f"  Subject: {ticket.subject}")
        print(f"  Category: {ticket.category.name if ticket.category else 'None'}")
        print(f"  Status: {ticket.status}")
        print(f"  Urgency: {ticket.urgency}")
        print(f"  Body: {ticket.body[:100]}...")
        print(f"  Sender: {ticket.sender}")
        
        # Check logs
        logs = TicketLog.query.filter_by(ticket_id=4).all()
        print(f"  Logs count: {len(logs)}")
    else:
        print("Ticket #4 not found")
        
        # Show all tickets
        all_tickets = Ticket.query.all()
        print(f"Available tickets: {[t.id for t in all_tickets]}")
