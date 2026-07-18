"""
Calmora - Flask Extensions
--------------------------
Extensions are instantiated here (without an app) and bound to the app
later inside the application factory (app/__init__.py). This is the
standard pattern for avoiding circular imports in larger Flask apps.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()

# Configure Flask-Login basics
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access Calmora."
login_manager.login_message_category = "info"
