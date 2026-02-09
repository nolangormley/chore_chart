from flask import Flask
from flask_login import LoginManager
from app.extensions import db
from app.models import User
from flasgger import Swagger
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
# Assumes app/__init__.py is one level deep from root
dotenv_path = os.path.join(os.path.dirname(basedir), '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path, override=True)
else:
    load_dotenv(override=True)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-this-for-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///chore_chart.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.path.join('app', 'static', 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Mail Config
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

swagger = Swagger(app)
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register Blueprints
from app.routes.users import users_bp
from app.routes.chores import chores_bp
from app.routes.stats import stats_bp
from app.routes.main import main_bp
from app.routes.auth import auth_bp

app.register_blueprint(users_bp)
app.register_blueprint(chores_bp)
app.register_blueprint(stats_bp)
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp)

with app.app_context():
    db.create_all()
