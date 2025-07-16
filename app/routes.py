from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Ticket, db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import func
import datetime
from .fetch_emails_util import fetch_and_store_emails

main = Blueprint('main', __name__)

# Create Ticket endpoint (must be after Blueprint definition)
@main.route('/create_ticket', methods=['POST'])
@login_required
def create_ticket():
    subject = request.form.get('subject')
    category = request.form.get('category')
    urgency = request.form.get('urgency')
    description = request.form.get('description')
    if not subject or not category or not urgency or not description:
        return jsonify({'success': False, 'error': 'All fields are required.'})
    try:
        ticket = Ticket(
            subject=subject,
            category=category,
            urgency=urgency,
            description=description,
            sender=current_user.username if hasattr(current_user, 'username') else 'Unknown',
            status='Open',
            created_at=datetime.datetime.now()
        )
        db.session.add(ticket)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})



# Fetch emails endpoint (must be after main is defined)
@main.route('/fetch_emails', methods=['POST'])
@login_required
def fetch_emails():
    try:
        count = fetch_and_store_emails()
        return jsonify({'success': True, 'new_tickets': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})



# Delete tickets route (must be after Blueprint definition, and only defined once)
@main.route('/delete_tickets', methods=['POST'])
@login_required
def delete_tickets():
    ids = request.form.getlist('ticket_ids')
    if not ids and request.is_json:
        ids = request.get_json().get('ticket_ids', [])
    if ids:
        Ticket.query.filter(Ticket.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
        if request.is_json:
            return jsonify({'success': True})
    if request.is_json:
        return jsonify({'success': False, 'error': 'No ticket IDs provided.'})
    return redirect(url_for('main.tickets'))

# (Removed duplicate import and Blueprint block)

@main.before_app_request
def require_login():
    allowed_routes = ['main.login', 'static']
    if not current_user.is_authenticated and request.endpoint not in allowed_routes:
        return redirect(url_for('main.login'))

@main.route('/')
def index():
    # Quick stats
    open_count = Ticket.query.filter_by(status='Open').count()
    urgent_count = Ticket.query.filter_by(urgency='Urgent').count()
    closed_count = Ticket.query.filter_by(status='Closed').count()
    user_count = User.query.count()

    # Top requestor (by sender)
    top = db.session.query(Ticket.sender, func.count(Ticket.id).label('count')) \
        .group_by(Ticket.sender) \
        .order_by(func.count(Ticket.id).desc()) \
        .first()
    top_requestor = {'name': top[0], 'count': top[1]} if top else None

    # Ticket stats by month (last 6 months)
    months_to_show = 6
    now = datetime.datetime.now()
    months = []
    open_counts = []
    closed_counts = []
    for i in range(months_to_show-1, -1, -1):
        month = (now - datetime.timedelta(days=now.day-1)).replace(day=1) - datetime.timedelta(days=30*i)
        month_start = month.replace(day=1)
        next_month = (month_start + datetime.timedelta(days=32)).replace(day=1)
        label = month_start.strftime('%Y-%m')
        months.append(label)
        open_count_month = Ticket.query.filter(Ticket.status=='Open', Ticket.created_at >= month_start, Ticket.created_at < next_month).count()
        closed_count_month = Ticket.query.filter(Ticket.status=='Closed', Ticket.created_at >= month_start, Ticket.created_at < next_month).count()
        open_counts.append(open_count_month)
        closed_counts.append(closed_count_month)
    ticket_stats_by_month = {
        'months': months,
        'open': open_counts,
        'closed': closed_counts
    }

    # Tickets list (for table)
    tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()

    return render_template('home.html',
        open_count=open_count,
        urgent_count=urgent_count,
        closed_count=closed_count,
        user_count=user_count,
        tickets=tickets,
        current_user=current_user,
        ticket_stats_by_month=ticket_stats_by_month,
        months_to_show=months_to_show,
        top_requestor=top_requestor
    )

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.index'))
        else:
            flash('Login failed.')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have successfully logged out!', 'info')
    return redirect(url_for('main.login'))

@main.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@main.route('/test-session')
def test_session():
    session['test'] = 'hello'
    return f"Session set to: {session['test']}"

@main.route('/tickets')
@login_required
def tickets():
    # Filters
    month = request.args.get('month')
    status = request.args.get('status', 'Open')
    category = request.args.get('category')
    # Default to current month
    import datetime
    now = datetime.datetime.now()
    if not month:
        month = now.strftime('%Y-%m')
    month_start = datetime.datetime.strptime(month, '%Y-%m')
    next_month = (month_start + datetime.timedelta(days=32)).replace(day=1)

    # Query tickets
    query = Ticket.query.filter(Ticket.created_at >= month_start, Ticket.created_at < next_month)
    if status and status != 'All':
        query = query.filter(Ticket.status == status)
    if category and category != 'All':
        query = query.filter(Ticket.category == category)
    tickets = query.order_by(Ticket.created_at.desc()).all()

    # Key stats
    tickets_raised = len(tickets)
    from collections import Counter
    most_common_category = Counter([t.category for t in tickets if t.category]).most_common(1)
    most_common_category = most_common_category[0][0] if most_common_category else '-'
    most_common_requestor = Counter([t.sender for t in tickets if t.sender]).most_common(1)
    most_common_requestor = most_common_requestor[0][0] if most_common_requestor else '-'

    # For dropdowns
    # Get all months for dropdown (YYYY-MM format) from tickets in DB
    from sqlalchemy import func
    all_months = [m[0] for m in db.session.query(func.strftime('%Y-%m', Ticket.created_at)).distinct().order_by(func.strftime('%Y-%m', Ticket.created_at).desc()).all()]
    all_categories = sorted(set([t.category for t in Ticket.query if t.category]))
    all_statuses = ['Open', 'Closed', 'All']

    return render_template('tickets.html',
        tickets=tickets,
        month=month,
        status=status,
        category=category,
        all_months=all_months,
        all_categories=all_categories,
        all_statuses=all_statuses,
        tickets_raised=tickets_raised,
        most_common_category=most_common_category,
        most_common_requestor=most_common_requestor
    )

@main.route('/viewticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    # For now, just show all fields and a placeholder for email thread
    return render_template('viewticket.html', ticket=ticket)
