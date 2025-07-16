from app import create_app
from app.models import db

app = create_app()

# Initialize the database
with app.app_context():
    db.create_all()
    print("Database created.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)