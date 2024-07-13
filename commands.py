import click
from flask.cli import with_appcontext
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

'''
flask create-admin

use above command to create admin
'''

@click.command('create-admin')
@with_appcontext
def create_admin_command():
    admin_user = User.query.filter_by(username='admin').first()
    if admin_user is None:
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('secure_password'),
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        click.echo("Admin user created successfully.")
    else:
        click.echo("Admin user already exists.")

def init_app(app):
    app.cli.add_command(create_admin_command)

'''

from models import db, User
from app import app

with app.app_context():
    users = User.query.all()
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}, Role: {user.role}")

-- to see all users

'''
