
from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models import User, Company, db
from routes import register_blueprints

# Initialize extensions
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"

def create_app():
    """Creates and configures the Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # The SQLALCHEMY_DATABASE_URI is now set dynamically in run.py
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from auth import auth_bp
    app.register_blueprint(auth_bp)
    register_blueprints(app)

    # Register custom Jinja2 filters
    from utils import etb, format_date
    app.jinja_env.filters["etb"] = etb
    app.jinja_env.filters["et_date"] = format_date

    # Define the main welcome/home page
    @app.route('/')
    def home():
        try:
            # This check determines if the setup wizard should run.
            # The redirection logic is handled in run.py.
            Company.query.count()
            return render_template('welcome.html')
        except Exception:
            # This typically happens on the very first run before the DB is created.
            return render_template('welcome.html')

    return app

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login hook to load a user by ID."""
    return User.query.get(int(user_id))

# Create the application instance.
# run.py will import this instance and modify its config before running the server.
app = create_app()

