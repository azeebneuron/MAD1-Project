from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask import Flask, render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from flask_login import LoginManager
from flask.cli import with_appcontext
from flask_login import login_user, logout_user, login_required, current_user
import click
from extensions import db, login_manager
from commands import init_app as init_commands
from models import User, Sponsor, Influencer, Campaign, AdRequest





# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
# app.config['SECRET_KEY'] = 'your_secret_key'

# db.init_app(app)

# with app.app_context():
#     db.create_all()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SECRET_KEY'] = 'your_secret_key'

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'signin'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()

    # Your route definitions go here
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
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password, password):
                login_user(user)  # Use Flask-Login to log in the user
                
                if user.role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif user.role == 'influencer':
                    return redirect(url_for('influencer'))
                elif user.role == 'sponsor':
                    return redirect(url_for('sponsor'))
                else:
                    flash('Invalid user role', 'danger')
                    return redirect(url_for('signin'))
            else:
                flash('Invalid credentials', 'danger')
        
        return render_template('signin.html')


    # def login_required(f):
    #     @wraps(f)
    #     def decorated_function(*args, **kwargs):
    #         if 'user_id' not in session:
    #             flash('Please log in to access this page.', 'warning')
    #             return redirect(url_for('signin'))
    #         return f(*args, **kwargs)
    #     return decorated_function


    def influencer_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('signin'))
            if current_user.role != 'influencer':
                flash('Access denied. Influencers only.', 'danger')
                return redirect(url_for('home'))
            
            influencer = Influencer.query.filter_by(user_id=current_user.id).first()
            if not influencer:
                flash('Your account is not properly set up as an influencer. Please contact support.', 'danger')
                return redirect(url_for('home'))
            
            return f(*args, **kwargs)
        return decorated_function

    def sponsor_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('signin'))
            if current_user.role != 'sponsor':
                flash('Access denied. Sponsors only.', 'danger')
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function

    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != 'admin':
                flash('You need to be an admin to access this page.', 'error')
                return redirect(url_for('signin'))
            return f(*args, **kwargs)
        return decorated_function

    @app.route('/influencer')
    @login_required
    @influencer_required
    def influencer():
        return render_template('influencer.html')

    @app.route('/sponsor')
    @login_required
    @sponsor_required
    def sponsor():
        campaigns = Campaign.query.filter_by(sponsor_id=current_user.id).all()
        return render_template('sponsor.html', campaigns=campaigns)


    @app.route('/error')
    def error():
        return render_template('error.html')



    @app.route('/campaigns')
    @login_required
    @sponsor_required
    def campaigns_list():
        campaigns = Campaign.query.filter_by(sponsor_id=current_user.id).all()
        return render_template('campaigns_list.html', campaigns=campaigns)

    @app.route('/campaigns/create', methods=['GET', 'POST'])


    @sponsor_required
    def create_campaign():
        if request.method == 'POST':
            new_campaign = Campaign(
                sponsor_id=current_user.id,
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
        if campaign.sponsor_id != current_user.id:
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
        if campaign.sponsor_id != current_user.id:
            flash('You do not have permission to delete this campaign.', 'danger')
            return redirect(url_for('campaigns_list'))
        
        db.session.delete(campaign)
        db.session.commit()
        flash('Campaign deleted successfully!', 'success')
        return redirect(url_for('campaigns_list'))

    @app.route('/logout')
    def logout():
        if current_user.is_authenticated:
            logout_user()
            session.clear()
            flash('You have been logged out successfully.', 'info')
        else:
            flash('You are not logged in.', 'info')
        return redirect(url_for('home'))

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



    @app.route('/influencer/ad_requests', methods=['GET'])
    @login_required
    @influencer_required
    def influencer_ad_requests():
        influencer = Influencer.query.filter_by(user_id=current_user.id).first()
        if not influencer:
            flash('You are not registered as an influencer.', 'error')
            return redirect(url_for('home'))
        
        ad_requests = AdRequest.query.filter_by(influencer_id=influencer.id).all()
        return render_template('influencer_ad_requests.html', ad_requests=ad_requests, influencer=influencer)

    @app.route('/influencer/ad_request/<int:id>/action', methods=['POST'])
    @login_required
    @influencer_required
    def influencer_ad_request_action(id):
        influencer = Influencer.query.filter_by(user_id=current_user.id).first()
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

    # Search Functions for Influencer and Sponsor

    @app.route('/search_influencers', methods=['GET', 'POST'])
    @login_required
    @sponsor_required
    def search_influencers():
        if request.method == 'POST':
            search_query = request.form.get('search_query', '')
            category = request.form.get('category', '')
            min_reach = request.form.get('min_reach', 0, type=int)

            influencers = Influencer.query.join(User).filter(
                or_(
                    User.username.ilike(f'%{search_query}%'),
                    Influencer.category.ilike(f'%{search_query}%'),
                    Influencer.niche.ilike(f'%{search_query}%')
                )
            )

            if category:
                influencers = influencers.filter(Influencer.category == category)
            
            if min_reach:
                influencers = influencers.filter(Influencer.reach >= min_reach)

            influencers = influencers.all()
            return render_template('search_influencers_results.html', influencers=influencers)

        return render_template('search_influencers.html')

    @app.route('/search_campaigns', methods=['GET', 'POST'])
    @login_required
    @influencer_required
    def search_campaigns():
        if request.method == 'POST':
            search_query = request.form.get('search_query', '')
            category = request.form.get('category', '')
            min_budget = request.form.get('min_budget', 0, type=float)

            campaigns = Campaign.query.filter(
                Campaign.status == 'active',
                or_(
                    Campaign.title.ilike(f'%{search_query}%'),
                    Campaign.description.ilike(f'%{search_query}%'),
                    Campaign.category.ilike(f'%{search_query}%')
                )
            )

            if category:
                campaigns = campaigns.filter(Campaign.category == category)
            
            if min_budget:
                campaigns = campaigns.filter(Campaign.budget >= min_budget)

            campaigns = campaigns.all()
            return render_template('search_campaigns_results.html', campaigns=campaigns)

        return render_template('search_campaigns.html')

    # Influener Profile
    @app.route('/influencer/profile', methods=['GET', 'POST'])
    @login_required
    @influencer_required
    def influencer_profile():
        influencer = Influencer.query.filter_by(user_id=current_user.id).first()
        if not influencer:
            flash('Influencer profile not found.', 'error')
            return redirect(url_for('home'))

        if request.method == 'POST':
            influencer.category = request.form['category']
            influencer.niche = request.form['niche']
            influencer.reach = int(request.form['reach'])
            influencer.bio = request.form['bio']

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('influencer_profile'))

        return render_template('influencer_profile.html', influencer=influencer)

    # Sponsor Profile

    @app.route('/sponsor/profile', methods=['GET', 'POST'])
    @login_required
    @sponsor_required
    def sponsor_profile():
        sponsor = Sponsor.query.filter_by(user_id=current_user.id).first()
        if not sponsor:
            flash('Sponsor profile not found.', 'error')
            return redirect(url_for('home'))

        if request.method == 'POST':
            sponsor.company_name = request.form['company_name']
            sponsor.industry = request.form['industry']
            sponsor.budget = float(request.form['budget'])
            # Add a new field for company description
            sponsor.description = request.form['description']

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('sponsor_profile'))

        return render_template('sponsor_profile.html', sponsor=sponsor)


    # Admin routes

    @app.route('/admin/dashboard')
    @login_required
    @admin_required
    def admin_dashboard():
        # Fetch statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_campaigns = Campaign.query.count()
        public_campaigns = Campaign.query.filter_by(is_public=True).count()
        private_campaigns = Campaign.query.filter_by(is_public=False).count()
        total_ad_requests = AdRequest.query.count()
        pending_ad_requests = AdRequest.query.filter_by(status='pending').count()
        accepted_ad_requests = AdRequest.query.filter_by(status='accepted').count()
        rejected_ad_requests = AdRequest.query.filter_by(status='rejected').count()
        flagged_sponsors = Sponsor.query.filter_by(is_flagged=True).count()
        flagged_influencers = Influencer.query.filter_by(is_flagged=True).count()

        return render_template('admin_dashboard.html',
                            total_users=total_users,
                            active_users=active_users,
                            total_campaigns=total_campaigns,
                            public_campaigns=public_campaigns,
                            private_campaigns=private_campaigns,
                            total_ad_requests=total_ad_requests,
                            pending_ad_requests=pending_ad_requests,
                            accepted_ad_requests=accepted_ad_requests,
                            rejected_ad_requests=rejected_ad_requests,
                            flagged_sponsors=flagged_sponsors,
                            flagged_influencers=flagged_influencers)
    
    @app.route('/admin/users')
    @login_required
    @admin_required
    def admin_users():
        users = User.query.all()
        return render_template('admin_users.html', users=users)

    @app.route('/admin/users/<int:user_id>')
    @login_required
    @admin_required
    def admin_user_detail(user_id):
        user = User.query.get_or_404(user_id)
        return render_template('admin_user_detail.html', user=user)

    @app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_user_edit(user_id):
        user = User.query.get_or_404(user_id)
        if request.method == 'POST':
            user.username = request.form['username']
            user.email = request.form['email']
            user.role = request.form['role']
            if request.form['password']:
                user.password = generate_password_hash(request.form['password'])
            db.session.commit()
            flash('User updated successfully', 'success')
            return redirect(url_for('admin_users'))
        return render_template('admin_user_edit.html', user=user)

    @app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_user_delete(user_id):
        user = User.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/campaigns')
    @login_required
    @admin_required
    def admin_campaigns():
        campaigns = Campaign.query.all()
        return render_template('admin_campaigns.html', campaigns=campaigns)

    @app.route('/admin/campaigns/<int:campaign_id>')
    @login_required
    @admin_required
    def admin_campaign_detail(campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        return render_template('admin_campaign_detail.html', campaign=campaign)

    @app.route('/admin/campaigns/<int:campaign_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_campaign_edit(campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        if request.method == 'POST':
            campaign.title = request.form['title']
            campaign.description = request.form['description']
            campaign.budget = float(request.form['budget'])
            campaign.status = request.form['status']
            db.session.commit()
            flash('Campaign updated successfully', 'success')
            return redirect(url_for('admin_campaigns'))
        return render_template('admin_campaign_edit.html', campaign=campaign)

    @app.route('/admin/campaigns/<int:campaign_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_campaign_delete(campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        db.session.delete(campaign)
        db.session.commit()
        flash('Campaign deleted successfully', 'success')
        return redirect(url_for('admin_campaigns'))

    @app.route('/admin/ad_requests')
    @login_required
    @admin_required
    def admin_ad_requests():
        ad_requests = AdRequest.query.all()
        return render_template('admin_ad_requests.html', ad_requests=ad_requests)

    @app.route('/admin/ad_requests/<int:ad_request_id>')
    @login_required
    @admin_required
    def admin_ad_request_detail(ad_request_id):
        ad_request = AdRequest.query.get_or_404(ad_request_id)
        return render_template('admin_ad_request_detail.html', ad_request=ad_request)

    @app.route('/admin/ad_requests/<int:ad_request_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_ad_request_edit(ad_request_id):
        ad_request = AdRequest.query.get_or_404(ad_request_id)
        if request.method == 'POST':
            ad_request.status = request.form['status']
            ad_request.details = request.form['details']
            db.session.commit()
            flash('Ad request updated successfully', 'success')
            return redirect(url_for('admin_ad_requests'))
        return render_template('admin_ad_request_edit.html', ad_request=ad_request)

    @app.route('/admin/ad_requests/<int:ad_request_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_ad_request_delete(ad_request_id):
        ad_request = AdRequest.query.get_or_404(ad_request_id)
        db.session.delete(ad_request)
        db.session.commit()
        flash('Ad request deleted successfully', 'success')
        return redirect(url_for('admin_ad_requests'))

    init_commands(app)
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
