from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Create instances of the extensions

db = SQLAlchemy()
login_manager = LoginManager()