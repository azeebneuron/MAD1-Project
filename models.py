from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from extensions import db
from flask_login import UserMixin

"""
models.py - Database Models for The webAPP

This contains the SQLAlchemy models for The webAPP, which is a platform to connect Sponsors and Influencers 
so that sponsors can get their product/service advertised and influencers can get monetary benefit.

It includes models for users, sponsors, influencers, campaigns, ad requests, metrics, conversations, and messages. 
I thought of conversations and message table in case I implemented chat feature between Influencer and Sponsor
but, things broke so many times that I didn't get any chance to implement it.

Key Features:
- User authentication and role-based access control
- Sponsor and Influencer profile management
- Campaign creation and management
- Ad request handling and negotiation
- Basic campaign performance metrics tracking 

Models:
1. User: Handles user authentication and role management
2. Sponsor: Represents a company or individual sponsoring campaigns
3. Influencer: Represents social media influencers
4. Campaign: Defines advertising campaigns created by sponsors
5. AdRequest: Manages the process of influencers applying to campaigns
6. CampaignMetrics: Tracks performance metrics for campaigns

Relationships:
- User <-> Sponsor/Influencer: One-to-One
- Sponsor <-> Campaign: One-to-Many
- Campaign <-> AdRequest: One-to-Many
- Influencer <-> AdRequest: One-to-Many
- Campaign <-> CampaignMetrics: One-to-Many
- Sponsor/Influencer <-> Conversation: One-to-Many
- Conversation <-> Message: One-to-Many
- User <-> Message: One-to-Many
"""

# Model definitions

class User(db.Model, UserMixin):

    """
    User model for authentication and role management
    
    Attributes:
        id (int): Primary key
        username (str): Unique username
        password (str): Hashed password
        email (str): Unique email address
        role (str): User role (admin, sponsor, or influencer)
        is_active (bool): Account status
        sponsor (Sponsor): Related Sponsor object (if applicable)
        influencer (Influencer): Related Influencer object (if applicable)
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(50), nullable=False)  # admin, sponsor, influencer
    is_active = db.Column(db.Boolean, default=True)
    sponsor = db.relationship('Sponsor', back_populates='user', uselist=False)
    influencer = db.relationship('Influencer', back_populates='user', uselist=False)

    def __repr__(self):
        return f'<User {self.username}>'


class Sponsor(db.Model):

    """
    Sponsor model representing companies or sponsors creating campaigns.
    
    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to User
        company_name (str): Name of the sponsoring company
        email (str): Contact email for the sponsor
        industry (str): Industry of the sponsor
        budget (float): Overall budget for campaigns
        description (text): Description of the sponsor
        is_flagged (bool): Flag for potential issues
        user (User): Related User object
        campaigns (list): List of related Campaign objects
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    company_name = db.Column(db.String(120))
    email = db.Column(db.String(120), nullable=False)  # Add this line
    industry = db.Column(db.String(120))
    budget = db.Column(db.Float)
    description = db.Column(db.Text)
    is_flagged = db.Column(db.Boolean, default=False)

    user = db.relationship('User', back_populates='sponsor')

    def __repr__(self):
        return f'<Sponsor {self.company_name}>'


class Influencer(db.Model):

    """
    Influencer model representing social media influencers.
    
    Attributes:
        id (int): Primary key
        user_id (int): Foreign key to User
        name (str): Name of the influencer
        contact_email (str): Contact email for the influencer
        category (str): General category of the influencer's content
        niche (str): Specific niche of the influencer
        is_flagged (bool): Flag for potential issues
        reach (int): Estimated reach of the influencer
        bio (text): Influencer's biography
        user (User): Related User object
        ad_requests (list): List of related AdRequest objects
    """

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name= db.Column(db.String(120))
    contact_email= db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(120))
    niche = db.Column(db.String(120))
    is_flagged = db.Column(db.Boolean, default=False)
    reach = db.Column(db.Integer)
    bio = db.Column(db.Text)
    user = db.relationship('User', back_populates='influencer')

    def __repr__(self):
        return f'<Influencer {self.id}>'


class Campaign(db.Model):

    """
    Campaign model representing advertising campaigns created by sponsors.
    
    Attributes:
        id (int): Primary key
        sponsor_id (int): Foreign key to Sponsor
        title (str): Campaign title
        company_name (str): Name of the company running the campaign
        description (text): Detailed campaign description
        budget (float): Budget for this specific campaign
        category (str): Category of the campaign
        status (str): Current status of the campaign (active, completed, flagged)
        start_date (datetime): Campaign start date
        end_date (datetime): Campaign end date
        is_public (bool): Whether the campaign is publicly visible
        sponsor (Sponsor): Related Sponsor object
        ad_requests (list): List of related AdRequest objects
        metrics (list): List of related CampaignMetrics objects
    """

    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id', ondelete='SET NULL'), nullable=True)
    title = db.Column(db.String(120), nullable=False)
    company_name= db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    budget = db.Column(db.Float)
    category = db.Column(db.String(120))
    status = db.Column(db.String(50), nullable=False)  # active, completed, flagged
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    is_public = db.Column(db.Boolean, default=True)

    sponsor = db.relationship('Sponsor', backref=db.backref('campaigns', lazy=True, cascade='all, delete-orphan'))


    def __repr__(self):
        return f'<Campaign {self.title}>'


class AdRequest(db.Model):

    """
    AdRequest model managing influencer applications to campaigns.
    
    Attributes:
        id (int): Primary key
        campaign_id (int): Foreign key to Campaign
        influencer_id (int): Foreign key to Influencer
        status (str): Current status of the request (pending, accepted, rejected, negotiated)
        details (text): Additional details of the request
        negotiation_terms (text): Terms of any ongoing negotiation
        communication_log (text): Log of communications
        renegotiation_email (str): Email for renegotiation communications
        company_name (str): Name of the company associated with the campaign
        created_at (datetime): Timestamp of creation
        updated_at (datetime): Timestamp of last update
        campaign (Campaign): Related Campaign object
        influencer (Influencer): Related Influencer object
    """

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id', ondelete='CASCADE'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # pending, accepted, rejected, negotiated
    details = db.Column(db.Text)
    negotiation_terms = db.Column(db.Text)
    communication_log = db.Column(db.Text)
    renegotiation_email = db.Column(db.String(120), nullable=False)
    company_name = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


    campaign = db.relationship('Campaign', backref=db.backref('ad_requests', lazy=True, cascade='all, delete-orphan'))
    influencer = db.relationship('Influencer', backref=db.backref('ad_requests', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<AdRequest {self.id}>'

# Useless tables, might use them in Future updates

class CampaignMetrics(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaign.id'), nullable=False)
    views = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    engagement_rate = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    campaign = db.relationship('Campaign', backref=db.backref('metrics', lazy=True))

    def __repr__(self):
        return f'<CampaignMetrics {self.id}>'


class Conversation(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey('sponsor.id'), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey('influencer.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sponsor = db.relationship('Sponsor', backref=db.backref('conversations', lazy=True))
    influencer = db.relationship('Influencer', backref=db.backref('conversations', lazy=True))

    def __repr__(self):
        return f'<Conversation {self.id}>'

class Message(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)

    conversation = db.relationship('Conversation', backref=db.backref('messages', lazy=True))
    sender = db.relationship('User', backref=db.backref('messages', lazy=True))

    def __repr__(self):
        return f'<Message {self.id}>'

