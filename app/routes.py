from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from app.models import User, Ticket, db, Category
from app.models import Log as TicketLog
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import func
import datetime
from .fetch_emails_util import fetch_and_store_emails

main = Blueprint('main', __name__)

# ...existing code...



# ...existing code...

@main.route('/settings', methods=['GET'])
@login_required
def settings():
    # Only admin can manage categories
    if current_user.role != 'admin':
        return render_template('settings.html', all_categories=[], current_user=current_user)
    all_categories = Category.query.order_by(Category.name).all()
    return render_template('settings.html', all_categories=all_categories, current_user=current_user)

@main.route('/add_category', methods=['POST'])
@login_required
def add_category():
    if current_user.role != 'admin':
        return redirect(url_for('main.settings'))
    new_category = request.form.get('category')
    if new_category:
        if not Category.query.filter_by(name=new_category).first():
            db.session.add(Category(name=new_category))
            db.session.commit()
            log = TicketLog(user=current_user.username, action='add_category', details=f"Added category '{new_category}'")
            db.session.add(log)
            db.session.commit()
    return redirect(url_for('main.settings'))

@main.route('/edit_category/<category>', methods=['POST'])
@login_required
def edit_category(category):
    if current_user.role != 'admin':
        return redirect(url_for('main.settings'))
    new_category = request.form.get('new_category')
    if new_category:
        cat = Category.query.filter_by(name=category).first()
        if cat:
            old_name = cat.name
            cat.name = new_category
            db.session.commit()
            # Update all tickets with the old category to the new one
            Ticket.query.filter_by(category=category).update({'category': new_category})
            db.session.commit()
            log = TicketLog(user=current_user.username, action='edit_category', details=f"Renamed category '{old_name}' to '{new_category}'")
            db.session.add(log)
            db.session.commit()
    return redirect(url_for('main.settings'))

@main.route('/delete_category/<category>', methods=['POST'])
@login_required
def delete_category(category):
    if current_user.role != 'admin':
        return redirect(url_for('main.settings'))
    cat = Category.query.filter_by(name=category).first()
    if cat:
        db.session.delete(cat)
        db.session.commit()
        # Remove category from all tickets
        Ticket.query.filter_by(category=category).update({'category': None})
        db.session.commit()
        log = TicketLog(user=current_user.username, action='delete_category', details=f"Deleted category '{category}'")
        db.session.add(log)
        db.session.commit()
    return redirect(url_for('main.settings'))



# Admin: Manage Users page
@main.route('/manage_users', methods=['GET'])
@login_required
def manage_users():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
    users = User.query.order_by(User.username).all()
    return render_template('manage_users.html', users=users)

# Admin: Create User endpoint
@main.route('/create_user', methods=['POST'])
@login_required
def create_user():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')
    if not username or not password or not role:
        flash('All fields are required.', 'error')
        return redirect(url_for('main.manage_users'))
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('main.manage_users'))
    new_user = User(
        username=username,
        password=generate_password_hash(password),
        role=role
    )
    db.session.add(new_user)
    db.session.commit()
    from .models import Log
    log = Log(user=current_user.username, action='create_user', details=f"Created user '{username}' with role '{role}'")
    db.session.add(log)
    db.session.commit()
    flash(f"User '{username}' created.", 'success')
    return redirect(url_for('main.manage_users'))

# Admin: Delete User endpoint
@main.route('/delete_user/<username>', methods=['POST'])
@login_required
def delete_user(username):
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
    user = User.query.filter_by(username=username).first()
    if not user or user.username == 'admin':
        flash('Cannot delete this user.', 'error')
        return redirect(url_for('main.manage_users'))
    db.session.delete(user)
    db.session.commit()
    from .models import Log
    log = Log(user=current_user.username, action='delete_user', details=f"Deleted user '{username}'")
    db.session.add(log)
    db.session.commit()
    flash(f"User '{username}' deleted.", 'success')
    return redirect(url_for('main.manage_users'))

# Admin: Edit User endpoint
@main.route('/edit_user/<username>', methods=['POST'])
@login_required
def edit_user(username):
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
    user = User.query.filter_by(username=username).first()
    if not user or user.username == 'admin':
        flash('Cannot edit this user.', 'error')
        return redirect(url_for('main.manage_users'))
    password = request.form.get('password')
    role = request.form.get('role')
    if role:
        user.role = role
    if password:
        from werkzeug.security import generate_password_hash
        user.password = generate_password_hash(password)
    db.session.commit()
    from .models import Log
    log = Log(user=current_user.username, action='edit_user', details=f"Edited user '{username}' (role: {role})")
    db.session.add(log)
    db.session.commit()
    flash(f"User '{username}' updated.", 'success')
    return redirect(url_for('main.manage_users'))

# Admin: Audit Logs page
@main.route('/audit_logs', methods=['GET'])
@login_required
def audit_logs():
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
    from .models import Log
    logs = Log.query.order_by(Log.timestamp.desc()).all()
    return render_template('audit_logs.html', logs=logs)

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
    
@main.route('/bulk_ticket_action', methods=['POST'])
def bulk_ticket_action():
    data = request.get_json()
    action = data.get('action')
    ticket_ids = data.get('ticket_ids', [])
    if not ticket_ids or not action:
        return jsonify({'success': False, 'error': 'Missing ticket IDs or action.'}), 400

    tickets = Ticket.query.filter(Ticket.id.in_(ticket_ids)).all()
    affected = 0
    for ticket in tickets:
        if action == 'close' and ticket.status != 'Closed':
            ticket.status = 'Closed'
            db.session.add(TicketLog(user='system', action='Bulk Close', details=f'Ticket closed in bulk for ticket {ticket.id}'))
            affected += 1
        elif action == 'open' and ticket.status != 'Open':
            ticket.status = 'Open'
            db.session.add(TicketLog(user='system', action='Bulk Open', details=f'Ticket opened in bulk for ticket {ticket.id}'))
            affected += 1
        elif action == 'delete':
            db.session.add(TicketLog(user='system', action='Bulk Delete', details=f'Ticket deleted in bulk for ticket {ticket.id}'))
            db.session.delete(ticket)
            affected += 1
        # Future actions can be added here
    try:
        db.session.commit()
        return jsonify({'success': True, 'affected': affected})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
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
        from .models import Log
        log = Log(user=current_user.username, action='create_ticket', details=f"Created ticket '{ticket.subject}' (ID: {ticket.id})")
        db.session.add(log)
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
    status = request.args.get('status', 'All')
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
    all_categories = [c.name for c in Category.query.order_by(Category.name).all()]
    all_statuses = ['Open', 'Closed', 'All']

    user_map = {u.id: u.username for u in User.query.all()}
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
        most_common_requestor=most_common_requestor,
        user_map=user_map
    )

@main.route('/viewticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    all_categories = Category.query.order_by(Category.name).all()
    from .models import User, EmailMessage
    all_users = User.query.order_by(User.username).all()
    # Fetch all EmailMessages for this ticket's thread, ordered by sent_at
    thread_msgs = []
    if ticket.thread_id:
        thread_msgs = EmailMessage.query.filter_by(thread_id=ticket.thread_id).order_by(EmailMessage.sent_at.asc()).all()
    else:
        msg = EmailMessage.query.filter_by(ticket_id=ticket.id).first()
        if msg:
            thread_msgs = [msg]
    # Convert attachments JSON string to list for each message
    for msg in thread_msgs:
        try:
            import json
            msg.attachments = json.loads(msg.attachments) if msg.attachments else []
        except Exception:
            msg.attachments = []
    return render_template('viewticket.html', ticket=ticket, all_categories=all_categories, all_users=all_users, thread_msgs=thread_msgs)

# Route to serve attachments
import os
from flask import send_from_directory, abort
@main.route('/attachments/<path:filename>')
@login_required
def serve_attachment(filename):
    # attachments directory is at the project root
    # attachments directory is at the project root, not inside app/
    attachments_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'attachments'))
    file_path = os.path.join(attachments_dir, filename)
    if not os.path.isfile(file_path):
        abort(404)
    return send_from_directory(attachments_dir, filename, as_attachment=True)

# Admin: Edit Ticket page
@main.route('/edit_ticket/<int:ticket_id>', methods=['GET', 'POST'])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role != 'admin':
        return redirect(url_for('main.index'))
    infra_users = User.query.filter_by(role='infra').order_by(User.username).all()
    if request.method == 'POST':
        changes = []
        old = {
            'subject': ticket.subject,
            'category': ticket.category,
            'urgency': ticket.urgency,
            'status': ticket.status,
            'description': ticket.description,
            'assigned_to': ticket.assigned_to
        }
        new = {
            'subject': request.form.get('subject', ticket.subject),
            'category': request.form.get('category', ticket.category),
            'urgency': request.form.get('urgency', ticket.urgency),
            'status': request.form.get('status', ticket.status),
            'description': request.form.get('description', ticket.description),
            'assigned_to': int(request.form.get('assigned_to')) if request.form.get('assigned_to') else None
        }
        # For assigned_to, show username if possible
        user_map = {u.id: u.username for u in User.query.all()}
        for field in old:
            old_val = old[field]
            new_val = new[field]
            if field == 'assigned_to':
                old_disp = user_map.get(old_val, '-') if old_val else '-'
                new_disp = user_map.get(new_val, '-') if new_val else '-'
            else:
                old_disp = old_val if old_val is not None else '-'
                new_disp = new_val if new_val is not None else '-'
            if old_val != new_val:
                changes.append(f"{field} changed from '{old_disp}' to '{new_disp}'")
                setattr(ticket, field, new_val)
        db.session.commit()
        from .models import Log
        if changes:
            details = f"Edited ticket '{ticket.subject}' (ID: {ticket.id}):\n" + "; ".join(changes)
        else:
            details = f"Edited ticket '{ticket.subject}' (ID: {ticket.id}): No changes."
        log = Log(user=current_user.username, action='edit_ticket', details=details)
        db.session.add(log)
        db.session.commit()
        return redirect(url_for('main.tickets'))
    return render_template('edit_ticket.html', ticket=ticket, infra_users=infra_users)
