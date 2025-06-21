from app import create_app
from app.models import db, User
from werkzeug.security import generate_password_hash

def create_default_user():
    app = create_app()
    with app.app_context():
        db.create_all()  # Ensure tables exist

        # Check if user already exists
        if User.query.filter_by(username="admin").first():
            print("User 'admin' already exists.")
            return

        user = User(
            username="admin",
            password=generate_password_hash("admin123")
        )
        db.session.add(user)
        db.session.commit()
        print("User 'admin' created with password 'admin123'")

if __name__ == "__main__":
    create_default_user()
