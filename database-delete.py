from app import app
from models import db  # Import your Flask app and db instance

with app.app_context():
    # Drop all tables
    db.drop_all()
    
    # Recreate all tables
    db.create_all()

print("Database reinitialized.")