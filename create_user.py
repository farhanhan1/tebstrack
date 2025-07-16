from app import create_app
from app.models import db, User
from werkzeug.security import generate_password_hash

def ensure_user(username, password, role):
    user = User.query.filter_by(username=username).first()
    if not user:
        new_user = User(
            username=username,
            role=role,
            password=generate_password_hash(password)
        )
        db.session.add(new_user)
        db.session.commit()
        print(f"Created user '{username}' with role '{role}' and password '{password}'")
    else:
        print(f"User '{username}' already exists.")

def create_default_users():
    app = create_app()
    with app.app_context():
        db.create_all()
        # # Delete all users first
        # User.query.delete()
        # db.session.commit()
        ensure_user("admin", "admin", "admin")
        ensure_user("farhan", "123", "infra")

if __name__ == "__main__":
    create_default_users()
