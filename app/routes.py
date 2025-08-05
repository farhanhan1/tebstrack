
import logging

from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app, jsonify, send_from_directory
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Length
from flask_login import login_user, login_required, logout_user, current_user
from app.models import User, Ticket, db, Category
from app.models import Log as TicketLog
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import func
import datetime
from .fetch_emails_util import fetch_and_store_emails
from app.extensions import csrf
main = Blueprint('main', __name__)

# Flask-WTF LoginForm for CSRF and validation
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=1, max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=1, max=128)])

# Favicon route (must be after Blueprint definition)
@main.route('/favicon.ico')
def favicon():
    return send_from_directory(current_app.root_path + '/../lib', 'tebstrack.ico', mimetype='image/vnd.microsoft.icon')

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
@csrf.exempt
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
        from .models import Log
        log = Log(user=current_user.username, action='create_ticket', details=f"Created ticket '{ticket.subject}' (ID: {ticket.id})")
        db.session.add(log)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})
@main.route('/bulk_ticket_action', methods=['POST'])
def bulk_ticket_action():
    data = request.get_json()
    action = data.get('action')
    ticket_ids = data.get('ticket_ids', [])
    if not ticket_ids or not action:
        return jsonify({'success': False, 'error': 'Missing ticket IDs or action.'}), 400

    tickets = Ticket.query.filter(Ticket.id.in_(ticket_ids)).all()
    affected = 0
    from flask_login import current_user
    username = current_user.username if hasattr(current_user, 'username') else 'Unknown'
    debug_info = {}
    from app.models import EmailMessage
    deleted_email_count = 0
    for ticket in tickets:
        if action == 'close' and ticket.status != 'Closed':
            ticket.status = 'Closed'
            db.session.add(TicketLog(user=username, action='Bulk Close', details=f'Ticket closed in bulk for ticket {ticket.id}'))
            affected += 1
        elif action == 'open' and ticket.status != 'Open':
            ticket.status = 'Open'
            db.session.add(TicketLog(user=username, action='Bulk Open', details=f'Ticket opened in bulk for ticket {ticket.id}'))
            affected += 1
        elif action == 'delete':
            # Delete related EmailMessages
            count = EmailMessage.query.filter(EmailMessage.ticket_id == ticket.id).delete(synchronize_session=False)
            deleted_email_count += count
            db.session.add(TicketLog(user=username, action='Bulk Delete', details=f'Ticket deleted in bulk for ticket {ticket.id} (deleted {count} related emails)'))
            db.session.delete(ticket)
            affected += 1
        # Future actions can be added here
    if action == 'delete':
        debug_info['deleted_email_count'] = deleted_email_count
        debug_info['deleted_ticket_count'] = affected
        print(f"[DEBUG] Bulk delete: {debug_info}", flush=True)
        logging.warning(f"[DEBUG] Bulk delete: {debug_info}")
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
@csrf.exempt
def fetch_emails():
    try:
        count = fetch_and_store_emails()
        return jsonify({'success': True, 'new_tickets': count}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 200



# Delete tickets route (must be after Blueprint definition, and only defined once)
@main.route('/delete_tickets', methods=['POST'])
@login_required
def delete_tickets():
    ids = request.form.getlist('ticket_ids')
    if not ids and request.is_json:
        ids = request.get_json().get('ticket_ids', [])
    if ids:
        from app.models import EmailMessage, Ticket
        # Convert ids to integers to avoid type mismatch
        ticket_ids = [int(i) for i in ids]
        # Debug info
        debug_info = {}
        debug_info['ticket_ids'] = ticket_ids
        # Delete all EmailMessages with ticket_id in ticket_ids
        deleted_emails = EmailMessage.query.filter(EmailMessage.ticket_id.in_(ticket_ids)).delete(synchronize_session=False)
        debug_info['deleted_emails'] = deleted_emails
        # Now delete the tickets
        deleted_tickets = Ticket.query.filter(Ticket.id.in_(ticket_ids)).delete(synchronize_session=False)
        debug_info['deleted_tickets'] = deleted_tickets
        # Use both print and logging to ensure output appears in VS Code
        print(f"[DEBUG] Ticket deletion: {debug_info}", flush=True)
        logging.warning(f"[DEBUG] Ticket deletion: {debug_info}")
        # If you still do not see output, run Flask with unbuffered output:
        #   python -u run.py
        db.session.commit()
        if request.is_json:
            return jsonify({'success': True, 'debug': debug_info})
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
    import datetime
    import logging
    import time
    form = LoginForm()
    # Brute force protection: server-side using LoginAttempt model
    from app.models import LoginAttempt
    max_attempts = 5
    lockout_minutes = 15
    ip = request.remote_addr
    now_ts = time.time()
    attempt = LoginAttempt.query.filter_by(ip=ip).first()
    from app.models import Log
    if attempt and attempt.lockout_until and now_ts < attempt.lockout_until:
        flash('Too many failed login attempts. Try again later.', 'error')
        logging.warning(f"Locked out login attempt from {ip}")
        # Log to DB
        log = Log(user=ip, action='login_lockout', details=f"Locked out login attempt from {ip}")
        db.session.add(log)
        db.session.commit()
        return render_template('login.html', form=form)
    # Reset fail count if lockout expired
    if attempt and attempt.lockout_until and now_ts >= attempt.lockout_until:
        attempt.fail_count = 0
        attempt.lockout_until = 0
        from app import db
        db.session.commit()
    if form.validate_on_submit():
        username = form.username.data.strip()
        password = form.password.data
        # Backend input validation: reject empty or whitespace-only username/password
        if not username or not password or username.isspace() or password.isspace():
            flash('Invalid username or password.', 'error')
            logging.warning(f"Login input validation failed from {ip} (username: '{username}')")
            log = Log(user=ip, action='login_input_invalid', details=f"Input validation failed (username: '{username}')")
            db.session.add(log)
            db.session.commit()
            return render_template('login.html', form=form)
        # Optionally: add regex for allowed characters here
        user = User.query.filter_by(username=username).first()
        from app import db
        if user and check_password_hash(user.password, password):
            login_user(user)
            # Reset fail count on successful login
            if attempt:
                attempt.fail_count = 0
                attempt.lockout_until = 0
                db.session.commit()
            logging.info(f"Login success for {username} from {ip}")
            log = Log(user=username, action='login_success', details=f"Login success from {ip}")
            db.session.add(log)
            db.session.commit()
            return redirect(url_for('main.index'))
        else:
            # Brute force: increment fail count in DB
            if not attempt:
                attempt = LoginAttempt(ip=ip, fail_count=1, lockout_until=0)
                db.session.add(attempt)
            else:
                attempt.fail_count += 1
            attempts_left = max_attempts - attempt.fail_count
            if attempt.fail_count >= max_attempts:
                attempt.lockout_until = now_ts + (lockout_minutes * 60)
                db.session.commit()
                flash('Too many failed login attempts. Try again later.', 'error')
                logging.warning(f"Account lockout for {username} from {ip}")
                log = Log(user=username, action='login_lockout', details=f"Account lockout from {ip}")
                db.session.add(log)
                db.session.commit()
            else:
                db.session.commit()
                flash(f'Login failed. {attempts_left} attempt(s) left before lockout.', 'error')
                logging.warning(f"Login failed for {username} from {ip} (attempt {attempt.fail_count})")
                log = Log(user=username, action='login_failed', details=f"Login failed from {ip} (attempt {attempt.fail_count})")
                db.session.add(log)
                db.session.commit()
            return render_template('login.html', form=form)
    # Always pass form to template
    return render_template('login.html', form=form)

@main.route('/logout')
@login_required
def logout():
    from app.models import Log
    username = current_user.username if hasattr(current_user, 'username') else 'Unknown'
    log = Log(user=username, action='logout', details=f"User {username} logged out.")
    db.session.add(log)
    db.session.commit()
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

    month = request.args.get('month', 'All')
    status = request.args.get('status', 'All')
    category = request.args.get('category')
    import datetime
    query = Ticket.query
    if month != 'All':
        try:
            month_start = datetime.datetime.strptime(month, '%Y-%m')
            next_month = (month_start + datetime.timedelta(days=32)).replace(day=1)
            query = query.filter(Ticket.created_at >= month_start, Ticket.created_at < next_month)
        except Exception:
            pass  # fallback: show all if parsing fails
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


from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Optional

class EditTicketForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired()])
    category = StringField('Category', validators=[DataRequired()])
    urgency = SelectField('Urgency', choices=[('Low','Low'),('Medium','Medium'),('High','High'),('Urgent','Urgent')], validators=[DataRequired()])
    status = SelectField('Status', choices=[('Open','Open'),('Closed','Closed')], validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    assigned_to = IntegerField('Assignee', validators=[Optional()])
    resolution = StringField('Resolution', validators=[Optional()])
    sender = StringField('Request by', validators=[Optional()])
    created_at = StringField('Issue Reported Date', validators=[Optional()])  # Will parse as date
    updated_at = StringField('Date of Completion', validators=[Optional()])  # Will parse as date

@main.route('/viewticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    all_categories = Category.query.order_by(Category.name).all()
    from .models import User, EmailMessage
    all_users = User.query.order_by(User.username).all()
    # Fetch all EmailMessages for this ticket's thread, ordered by sent_at
    thread_msgs = []
    import os
    GMAIL_USER = os.environ.get('GMAIL_USER', 'tebstrack@gmail.com').lower()
    from sqlalchemy import or_, and_
    if ticket.thread_id:
        # Build the set of message_ids in the thread chain
        all_msgs = EmailMessage.query.filter(
            EmailMessage.thread_id == ticket.thread_id
        ).order_by(EmailMessage.sent_at.desc()).all()
        # Build a map of message_id -> EmailMessage
        msg_map = {m.message_id: m for m in all_msgs if m.message_id}
        # Find the root message (the one with in_reply_to=None or not in msg_map)
        root_msgs = [m for m in all_msgs if not m.in_reply_to or m.in_reply_to not in msg_map]
        thread_chain = []
        # For each root, walk the chain
        for root in root_msgs:
            chain = []
            current = root
            while current:
                chain.append(current)
                # Find the next message that replies to this one
                next_msg = None
                for m in all_msgs:
                    if m.in_reply_to and m.in_reply_to == current.message_id:
                        next_msg = m
                        break
                current = next_msg
            thread_chain.extend(chain)
        # Remove duplicates and sort by sent_at
        seen_ids = set()
        thread_msgs = []
        for m in sorted(thread_chain, key=lambda x: x.sent_at, reverse=True):
            if m.id not in seen_ids:
                thread_msgs.append(m)
                seen_ids.add(m.id)
    else:
        msg = EmailMessage.query.filter_by(ticket_id=ticket.id).first()
        if msg:
            thread_msgs = [msg]
    # Convert attachments JSON string to list for each message, and mark if sent by GMAIL_USER
    import re
    for msg in thread_msgs:
        try:
            import json
            msg.attachments = json.loads(msg.attachments) if msg.attachments else []
        except Exception:
            msg.attachments = []
        msg.is_self = (msg.sender or '').strip().lower() == GMAIL_USER
        # Remove quoted message history (e.g., lines starting with 'On ... wrote:')
        if msg.body:
            # Remove everything from the first occurrence of a quoted reply marker
            msg.body = re.split(r'\n?On .+wrote:', msg.body)[0].strip()
    form = EditTicketForm(obj=ticket)
    return render_template('viewticket.html', ticket=ticket, all_categories=all_categories, all_users=all_users, thread_msgs=thread_msgs, GMAIL_USER=GMAIL_USER, form=form)

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
    form = EditTicketForm(obj=ticket)
    if form.validate_on_submit():
        changes = []
        old = {
            'subject': ticket.subject,
            'category': ticket.category,
            'urgency': ticket.urgency,
            'status': ticket.status,
            'description': ticket.description,
            'assigned_to': ticket.assigned_to,
            'resolution': ticket.resolution,
            'sender': ticket.sender,
            'created_at': ticket.created_at.strftime('%Y-%m-%d') if ticket.created_at else '',
            'updated_at': ticket.updated_at.strftime('%Y-%m-%d') if ticket.updated_at else ''
        }
        new = {
            'subject': form.subject.data,
            'category': form.category.data,
            'urgency': form.urgency.data,
            'status': form.status.data,
            'description': form.description.data,
            'assigned_to': form.assigned_to.data if form.assigned_to.data else None,
            'resolution': form.resolution.data if hasattr(form, 'resolution') and form.resolution.data else None,
            'sender': form.sender.data if hasattr(form, 'sender') and form.sender.data else ticket.sender,
            'created_at': form.created_at.data if hasattr(form, 'created_at') and form.created_at.data else old['created_at'],
            'updated_at': form.updated_at.data if hasattr(form, 'updated_at') and form.updated_at.data else old['updated_at']
        }
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
                if field in ['created_at', 'updated_at']:
                    # Parse date string to datetime
                    import datetime
                    try:
                        setattr(ticket, field, datetime.datetime.strptime(new_val, '%Y-%m-%d'))
                    except Exception:
                        pass  # Ignore parse errors
                else:
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
    # Pre-populate form with ticket data for GET
    if request.method == 'GET':
        form = EditTicketForm(obj=ticket)
    return render_template('edit_ticket.html', ticket=ticket, infra_users=infra_users, form=form)
