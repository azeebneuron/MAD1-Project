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
from flask import send_file
import matplotlib.pyplot as plt
import io
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload




# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
# app.config['SECRET_KEY'] = 'your_secret_key'

# db.init_app(app)

# with app.app_context():
#     db.create_all()

def create_app():
    app = Flask(__name__)
    print(f"Template folder path: {app.template_folder}")

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

    @app.route('/')
    def home():
        try:
            return render_template('index.html')
        except Exception as e:
            print(f"Error rendering template: {str(e)}")
            return f"Error: {str(e)}", 500


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
                new_sponsor = Sponsor(user_id=new_user.id, email=email)  # Add email here
                db.session.add(new_sponsor)

            try:
                db.session.commit()
                flash('Account created successfully!', 'success')
                return redirect(url_for('signin'))
            except IntegrityError:
                db.session.rollback()
                flash('An error occurred. Please try again.', 'danger')
                return redirect(url_for('signup'))

        return render_template('signup.html')


    @app.route('/signin', methods=['GET', 'POST'])
    def signin():
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password, password):
                login_user(user)  # Use Flask-Login to log in the user
                session['username'] = user.username  # Store username in session
                session['user_id'] = user.id  # It's often useful to store the user ID as well
                
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
        
    
    @app.route('/test')
    def test():
        return "This is a test route"


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
    def influencer():
        if current_user.role != 'influencer':
            flash('Access denied. This page is for influencers only.', 'danger')
            return redirect(url_for('home'))

        # Fetch active campaigns
        active_campaigns = Campaign.query.filter_by(status='active', is_public=True).order_by(Campaign.start_date.desc()).limit(6).all()
        
        return render_template('influencer.html', current_user=current_user, active_campaigns=active_campaigns)


    @app.route('/sponsor')
    @login_required
    @sponsor_required
    def sponsor():
        username = session.get('username', 'Guest')
        campaigns = Campaign.query.filter_by(sponsor_id=current_user.id).all()
        print("Username:", username)
        return render_template('sponsor.html', username=username, campaigns=campaigns)


    @app.route('/campaigns')
    @login_required
    @sponsor_required
    def campaigns_list():
        campaigns = Campaign.query.filter_by(sponsor_id=current_user.id).all()
        return render_template('sponsor.html', campaigns=campaigns)

    # @app.route('/campaigns/create', methods=['GET', 'POST'])

    @app.route('/campaign/<int:campaign_id>')
    @login_required
    def campaign_details(campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        return render_template('campaign_details.html', campaign=campaign)
    
    #TODO: Add the apply_campaign route
    @app.route('/apply_campaign/<int:campaign_id>')
    @login_required
    def apply_campaign(campaign_id):
        # Add your logic here for applying to a campaign
        flash('Your application has been submitted!', 'success')
        return redirect(url_for('campaign_details', campaign_id=campaign_id))

    @app.route('/create_campaign', methods=['GET', 'POST'])
    @login_required
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
                company_name=request.form['company_name'],
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
            return redirect(url_for('sponsor'))
        return render_template('update_campaign.html', campaign=campaign)

    @app.route('/campaigns/<int:campaign_id>/delete', methods=['GET', 'POST'])
    @login_required
    @sponsor_required
    def delete_campaign(campaign_id):
        campaign = Campaign.query.get_or_404(campaign_id)
        if campaign.sponsor_id != current_user.id:
            flash('You do not have permission to delete this campaign.', 'danger')
            return redirect(url_for('sponsor'))
        
        db.session.delete(campaign)
        db.session.commit()
        flash('Campaign deleted successfully!', 'success')
        return redirect(url_for('sponsor'))

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
        ad_requests = AdRequest.query.filter(AdRequest.campaign.has(sponsor_id=current_user.id)).all()
        return render_template('ad_requests_list.html', ad_requests=ad_requests)

    @app.route('/ad_requests/create', methods=['GET', 'POST'])
    def create_ad_request():
        if request.method == 'POST':
            campaign_id = request.form.get('campaign_id')
            influencer_username = request.form.get('influencer_username')
            status = request.form.get('status')
            details = request.form.get('details')
            renegotiation_email = request.form.get('renegotiation_email')
            company_name = request.form.get('company_name')


            # Find the influencer by username
            influencer = Influencer.query.join(User).filter(User.username == influencer_username).first()
            if not influencer:
                flash('Influencer not found. Please check the username and try again.', 'error')
                return redirect(url_for('create_ad_request'))

            # Create new ad request
            new_ad_request = AdRequest(
                campaign_id=campaign_id,
                influencer_id=influencer.id,
                status=status,
                details=details,
                renegotiation_email=renegotiation_email,
                company_name=company_name
            )
            
            try:
                db.session.add(new_ad_request)
                db.session.commit()
                flash('Ad request created successfully!', 'success')
                return redirect(url_for('list_ad_requests'))
            except Exception as e:
                db.session.rollback()
                flash(f'An error occurred while creating the ad request: {str(e)}', 'error')
                return redirect(url_for('create_ad_request'))

        # GET request
        campaigns = Campaign.query.filter_by(sponsor_id=current_user.id).all()
        return render_template('create_ad_request.html', campaigns=campaigns)

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
        
        ad_requests = AdRequest.query.options(
            joinedload(AdRequest.campaign).joinedload(Campaign.sponsor)
        ).filter_by(influencer_id=influencer.id).all()

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
        else:
            flash('Invalid action.', 'error')
            return redirect(url_for('influencer_ad_requests'))
        
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

            # Start with a base query
            query = Influencer.query

            # Apply search filter if a search query is provided
            if search_query:
                query = query.filter(
                    or_(
                        Influencer.name.ilike(f'%{search_query}%'),
                        Influencer.category.ilike(f'%{search_query}%'),
                        Influencer.niche.ilike(f'%{search_query}%')
                    )
                )

            # Apply category filter if a category is selected
            if category:
                query = query.filter(Influencer.category == category)

            # Apply minimum reach filter if provided
            if min_reach:
                query = query.filter(Influencer.reach >= min_reach)

            # Execute the query
            influencers = query.all()

            print(f"Number of influencers found: {len(influencers)}")
            for inf in influencers:
                print(f"Influencer: {inf.name}, Category: {inf.category}, Reach: {inf.reach}")

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
            influencer.name = request.form['name']
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
        
        # Delete associated sponsor or influencer
        if user.role == 'sponsor':
            sponsor = Sponsor.query.filter_by(user_id=user.id).first()
            if sponsor:
                db.session.delete(sponsor)
        elif user.role == 'influencer':
            influencer = Influencer.query.filter_by(user_id=user.id).first()
            if influencer:
                db.session.delete(influencer)
        
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
        
        # Delete associated ad requests
        ad_requests = AdRequest.query.filter_by(campaign_id=campaign.id).all()
        for ad_request in ad_requests:
            db.session.delete(ad_request)
        
        # Delete the campaign
        db.session.delete(campaign)
        
        try:
            db.session.commit()
            flash('Campaign and associated ad requests deleted successfully', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while deleting the campaign: {str(e)}', 'error')
        
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
    
    # Error handling

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('funny_error.html', error_type='404 Not Found', error_message='The page you are looking for does not exist.'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('funny_error.html', error_type='500 Internal Server Error', error_message='Something went wrong on our end.'), 500

    @app.errorhandler(TypeError)
    def handle_type_error(e):
        app.logger.error(f'TypeError: {str(e)}')
        return render_template('funny_error.html', error_type='TypeError', error_message=str(e)), 400

    @app.errorhandler(Exception)
    def handle_exception(e):
        error_type = type(e).__name__
        error_message = str(e)
        app.logger.error(f'Unhandled Exception: {error_type} - {error_message}')
        return render_template('funny_error.html', error_type=error_type, error_message=error_message), 500

    @app.route('/oops')
    def oops():
        error_type = request.args.get('error_type', 'UnknownError')
        error_message = request.args.get('error_message', 'An unexpected error occurred')
        return render_template('funny_error.html', error_type=error_type, error_message=error_message), 

    init_commands(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)