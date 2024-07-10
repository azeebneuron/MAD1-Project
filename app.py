from flask import Flask, render_template, redirect, url_for, request, flash, session
from models import db, User, Sponsor, Influencer, Campaign, datetime
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps


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
    try:
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
            db.session.commit()

            flash('Account created successfully!', 'success')
            return redirect(url_for('signin'))
    except Exception as e:
        print(f"An error occurred: {e}")
        return redirect(url_for('error'))

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

if __name__ == '__main__':
    app.run(debug=True)
