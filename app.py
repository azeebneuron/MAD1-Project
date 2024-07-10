from flask import Flask, render_template, redirect, url_for, request, flash, session
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash

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

@app.route('/sponsor')
def sponsor():
    return render_template('sponsor.html')

@app.route('/error')
def error():
    return render_template('error.html')


if __name__ == '__main__':
    app.run(debug=True)
