from app import create_app
from extensions import db
from models import User, Sponsor, Influencer, Campaign, AdRequest, CampaignMetrics, Conversation, Message


# Mistake happens
# So, just delete the whole database and recreate it, no big deal!!
# This Script does that

app = create_app()

with app.app_context():

    db.drop_all()
    
    db.create_all()

print("Database ka punar janam!!")