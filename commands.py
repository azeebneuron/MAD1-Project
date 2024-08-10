import click
from flask.cli import with_appcontext
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

'''
flask create-admin

use above command to create admin
'''

# The username is admin
# The password is secure_password, SECURITYYY IS MY FIRST PRIORITY

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

