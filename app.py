from flask import Flask, render_template
from flask_login import LoginManager
from config import Config
from models import User, Company, db
from routes import register_blueprints
import secrets, string, sys, os


login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    instance_path = os.path.join(current_dir, 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    db_path = os.path.join(instance_path, 'ha_business.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['PERMANENT_SESSION_LIFETIME'] = 1800
    
    db.init_app(app)
    login_manager.init_app(app)

    from auth import auth_bp
    from utils import etb, format_date

    app.register_blueprint(auth_bp)
    register_blueprints(app)

    app.jinja_env.filters["etb"] = etb
    app.jinja_env.filters["et_date"] = format_date

    with app.app_context():
        db.create_all()

    # HOME ROUTE - Welcome Page
    @app.route('/')
    def home():
        try:
            company_count = Company.query.count()
            user_count = User.query.count()
            if company_count > 0 and user_count > 0:
                return render_template('welcome.html')
            return render_template('welcome.html')
        except:
            return render_template('welcome.html')

    return app


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)