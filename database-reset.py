from app import create_app
from extensions import db
from models import User, Sponsor, Influencer, Campaign, AdRequest, CampaignMetrics, Conversation, Message

app = create_app()

with app.app_context():
    # Drop all tables
    db.drop_all()
    
    # Recreate all tables
    db.create_all()

print("Database has been reinitialized.")