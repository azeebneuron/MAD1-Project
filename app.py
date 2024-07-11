from flask import Flask, render_template, redirect, url_for, request, flash, session
from models import db, User, Sponsor, Influencer, Campaign, datetime, AdRequest
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from flask_login import login_required, current_user
from flask_login import LoginManager



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SECRET_KEY'] = 'your_secret_key'

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='sha256')
        email = request.form['email']
        role = request.form['user-type']
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email is already registered', 'danger')
            return redirect(url_for('signup'))

        new_user = User(username=username, password=password, email=email, role=role)
        db.session.add(new_user)
        db.session.flush()  # This will assign an id to new_user without committing the transaction

        if role == 'influencer':
            new_influencer = Influencer(user_id=new_user.id)
            db.session.add(new_influencer)
        elif role == 'sponsor':
            new_sponsor = Sponsor(user_id=new_user.id)
            db.session.add(new_sponsor)

        db.session.commit()

        flash('Account created successfully!', 'success')
        return redirect(url_for('signin'))

    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    try:
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['user_role'] = user.role
                session['username'] = user.username

                if user.role == 'influencer':
                    return redirect(url_for('influencer'))
                elif user.role == 'sponsor':
                    return redirect(url_for('sponsor'))
            else:
                flash('Invalid credentials', 'danger')
    except Exception as e:
        print(f"An error occurred: {e}")
        return redirect(url_for('error'))

    return render_template('signin.html')

@app.route('/influencer')
def influencer():
    return render_template('influencer.html')

@app.route('/sponsor/profile')
def sponsor_profile():
    return render_template('sponsor.html')

@app.route('/error')
def error():
    return render_template('error.html')


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('signin'))
        return f(*args, **kwargs)
    return decorated_function

def sponsor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or session['user_role'] != 'sponsor':
            flash('Access denied. Sponsors only.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/campaigns')
@login_required
@sponsor_required
def campaigns_list():
    campaigns = Campaign.query.filter_by(sponsor_id=session['user_id']).all()
    return render_template('campaigns_list.html', campaigns=campaigns)

@app.route('/campaigns/create', methods=['GET', 'POST'])
@login_required
@sponsor_required
def create_campaign():
    if request.method == 'POST':
        new_campaign = Campaign(
            sponsor_id=session['user_id'],
            title=request.form['title'],
            description=request.form['description'],
            budget=float(request.form['budget']) if request.form['budget'] else None,
            category=request.form['category'],
            status=request.form['status'],
            start_date=datetime.strptime(request.form['start_date'], '%Y-%m-%d') if request.form['start_date'] else None,
            end_date=datetime.strptime(request.form['end_date'], '%Y-%m-%d') if request.form['end_date'] else None
        )
        db.session.add(new_campaign)
        db.session.commit()
        flash('Campaign created successfully!', 'success')

        return redirect(url_for('campaigns_list'))
    return render_template('create_campaign.html')

@app.route('/campaigns/<int:campaign_id>/update', methods=['GET', 'POST'])
@login_required
@sponsor_required
def update_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.sponsor_id != session['user_id']:
        flash('You do not have permission to edit this campaign.', 'danger')
        return redirect(url_for('campaigns_list'))
    
    if request.method == 'POST':
        campaign.title = request.form['title']
        campaign.description = request.form['description']
        campaign.budget = float(request.form['budget']) if request.form['budget'] else None
        campaign.category = request.form['category']
        campaign.status = request.form['status']
        campaign.start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d') if request.form['start_date'] else None
        campaign.end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d') if request.form['end_date'] else None
        db.session.commit()
        flash('Campaign updated successfully!', 'success')
        return redirect(url_for('campaigns_list'))
    return render_template('update_campaign.html', campaign=campaign)

@app.route('/campaigns/<int:campaign_id>/delete', methods=['POST'])
@login_required
@sponsor_required
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    if campaign.sponsor_id != session['user_id']:
        flash('You do not have permission to delete this campaign.', 'danger')
        return redirect(url_for('campaigns_list'))
    
    db.session.delete(campaign)
    db.session.commit()
    flash('Campaign deleted successfully!', 'success')
    return redirect(url_for('campaigns_list'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/sponsor')
@login_required
@sponsor_required
def sponsor():
    campaigns = Campaign.query.filter_by(sponsor_id=session['user_id']).all()
    return render_template('sponsor.html', campaigns=campaigns)


def parse_date(date_string):
    if date_string:
        try:
            return datetime.strptime(date_string, '%Y-%m-%d')
        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
            return None
    return None

# Ad requests

@app.route('/ad_requests', methods=['GET'])
def list_ad_requests():
    ad_requests = AdRequest.query.all()
    return render_template('ad_requests_list.html', ad_requests=ad_requests)

@app.route('/ad_requests/create', methods=['GET', 'POST'])
def create_ad_request():
    if request.method == 'POST':
        campaign_id = request.form['campaign_id']
        influencer_id = request.form['influencer_id']
        status = request.form['status']
        details = request.form['details']
        
        new_ad_request = AdRequest(
            campaign_id=campaign_id,
            influencer_id=influencer_id,
            status=status,
            details=details
        )
        
        db.session.add(new_ad_request)
        db.session.commit()
        
        flash('Ad request created successfully', 'success')
        return redirect(url_for('list_ad_requests'))
    
    campaigns = Campaign.query.all()
    influencers = Influencer.query.all()
    return render_template('create_ad_request.html', campaigns=campaigns, influencers=influencers)

@app.route('/ad_requests/edit/<int:id>', methods=['GET', 'POST'])
def edit_ad_request(id):
    ad_request = AdRequest.query.get_or_404(id)
    
    if request.method == 'POST':
        ad_request.influencer_id = request.form['influencer_id']
        ad_request.status = request.form['status']
        ad_request.details = request.form['details']
        ad_request.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Ad request updated successfully', 'success')
        return redirect(url_for('list_ad_requests'))
    
    influencers = Influencer.query.all()
    return render_template('edit_ad_request.html', ad_request=ad_request, influencers=influencers)

@app.route('/ad_requests/delete/<int:id>', methods=['POST'])
def delete_ad_request(id):
    ad_request = AdRequest.query.get_or_404(id)
    db.session.delete(ad_request)
    db.session.commit()
    
    flash('Ad request deleted successfully', 'success')
    return redirect(url_for('list_ad_requests'))

# Influencers ad requests

def influencer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('signin'))
        if session['user_role'] != 'influencer':
            flash('Access denied. Influencers only.', 'danger')
            return redirect(url_for('home'))
        
        influencer = Influencer.query.filter_by(user_id=session['user_id']).first()
        if not influencer:
            flash('Your account is not properly set up as an influencer. Please contact support.', 'danger')
            return redirect(url_for('home'))
        
        return f(*args, **kwargs)
    return decorated_function


@app.route('/influencer/ad_requests', methods=['GET'])
@login_required
@influencer_required
def influencer_ad_requests():
    influencer = Influencer.query.filter_by(user_id=session['user_id']).first()
    if not influencer:
        flash('You are not registered as an influencer.', 'error')
        return redirect(url_for('home'))
    
    ad_requests = AdRequest.query.filter_by(influencer_id=influencer.id).all()
    return render_template('influencer_ad_requests.html', ad_requests=ad_requests, influencer=influencer)

@app.route('/influencer/ad_request/<int:id>/action', methods=['POST'])
@login_required
@influencer_required
def influencer_ad_request_action(id):
    influencer = Influencer.query.filter_by(user_id=session['user_id']).first()
    if not influencer:
        flash('You are not registered as an influencer.', 'error')
        return redirect(url_for('home'))
    
    ad_request = AdRequest.query.get_or_404(id)
    if ad_request.influencer_id != influencer.id:
        flash('You are not authorized to perform this action.', 'error')
        return redirect(url_for('influencer_ad_requests'))
    
    action = request.form.get('action')
    if action == 'accept':
        ad_request.status = 'accepted'
        flash('Ad request accepted successfully.', 'success')
    elif action == 'reject':
        ad_request.status = 'rejected'
        flash('Ad request rejected successfully.', 'success')
    elif action == 'negotiate':
        new_terms = request.form.get('new_terms')
        if new_terms:
            ad_request.status = 'negotiated'
            ad_request.negotiation_terms = new_terms
            ad_request.communication_log += f"\n[{datetime.utcnow()}] Influencer negotiated: {new_terms}"
            flash('Negotiation submitted successfully.', 'success')
        else:
            flash('Please provide terms for negotiation.', 'error')
    
    ad_request.updated_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('influencer_ad_requests'))



if __name__ == '__main__':
    app.run(debug=True)
