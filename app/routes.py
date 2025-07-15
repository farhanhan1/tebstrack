from flask import Blueprint, render_template, redirect, url_for, request, flash, session, current_app
from flask_login import login_user, login_required, logout_user, current_user
from .models import User, Ticket, db
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from sqlalchemy import func
import datetime

main = Blueprint('main', __name__)

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
