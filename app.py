import os
from flask import Flask, render_template, jsonify, request, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
import numpy as np
from PIL import Image
import time
import cv2
import random
from itsdangerous import URLSafeTimedSerializer
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import redis
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from flask_httpauth import HTTPTokenAuth
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

# Initialize Sentry for error tracking
if os.environ.get('SENTRY_DSN'):
    sentry_sdk.init(
        dsn=os.environ.get('SENTRY_DSN'),
        integrations=[FlaskIntegration()],
        traces_sample_rate=1.0,
        environment=os.environ.get('FLASK_ENV', 'development')
    )

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Security Headers
Talisman(
    app,
    force_https=os.environ.get('FLASK_ENV') == 'production',
    strict_transport_security=True,
    session_cookie_secure=True,
    content_security_policy={
        'default-src': "'self'",
        'script-src': [
            "'self'",
            'cdn.jsdelivr.net',
            'unpkg.com',
            'api.maptiler.com',
            "'unsafe-inline'"  # Needed for Bootstrap tooltips
        ],
        'style-src': [
            "'self'",
            'cdn.jsdelivr.net',
            'api.maptiler.com',
            "'unsafe-inline'"
        ],
        'img-src': [
            "'self'",
            'data:',
            'api.maptiler.com',
            '*.tile.openstreetmap.org'
        ],
        'connect-src': [
            "'self'",
            'api.maptiler.com'
        ]
    }
)

# Configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY'),
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={'pool_pre_ping': True, 'pool_recycle': 300},
    MAIL_SERVER=os.environ.get('MAIL_SERVER'),
    MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
    MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't'],
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=(os.environ.get('MAIL_DEFAULT_SENDER_NAME', 'AquaVision AI')),
    CACHE_TYPE='RedisCache',
    CACHE_REDIS_URL=os.environ.get('REDIS_URL'),
    CACHE_DEFAULT_TIMEOUT=300,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB upload limit
    UPLOAD_FOLDER=os.path.join('static', 'uploads'),
    ANALYSIS_FOLDER=os.path.join('static', 'analysis'),
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
cache = Cache(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'
auth = HTTPTokenAuth(scheme='Bearer')

# Rate limiting configuration
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=app.config['CACHE_REDIS_URL'],
    strategy="fixed-window"  # More consistent than moving-window
)

# Configure logging
if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/aquavision.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('AquaVision AI startup')

# Password reset serializer
reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    api_key = db.Column(db.String(512), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    login_attempts = db.Column(db.Integer, default=0)
    last_attempt = db.Column(db.DateTime)
    profile_image = db.Column(db.String(200))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_api_key(self):
        self.api_key = jwt.encode(
            {'user_id': self.id, 'exp': datetime.utcnow() + timedelta(days=365)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return self.api_key
    
    def get_reset_token(self):
        return reset_serializer.dumps(self.email, salt='password-reset')
    
    @staticmethod
    def verify_reset_token(token, max_age=3600):
        try:
            email = reset_serializer.loads(token, salt='password-reset', max_age=max_age)
            return User.query.filter_by(email=email).first()
        except:
            return None

class AnalysisHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    analysis_type = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))
    result_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user = db.relationship('User', backref='analyses')

class SavedLocation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='saved_locations')

# Create tables
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@auth.verify_token
def verify_token(token):
    try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return User.query.get(data['user_id'])
    except:
        return None

# API Response Helpers
def success_response(data=None, message=None):
    return jsonify({'success': True, 'data': data, 'message': message})

def error_response(message, status_code=400):
    return jsonify({'success': False, 'error': message}), status_code

# Main App Routes
@app.route('/')
@app.route('/history')
@app.route('/api-key')
@app.route('/reset-password/<token>')
def index_spa(token=None):
    return render_template('index.html')

# API Routes
@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ['name', 'email', 'password']):
        return error_response('All fields are required', 400)
    
    if User.query.filter_by(email=data['email']).first():
        return error_response('Email already registered', 400)
    
    user = User(name=data['name'], email=data['email'])
    user.set_password(data['password'])
    user.generate_api_key()
    
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    return success_response({
        'user': {
            'name': user.name,
            'email': user.email,
            'api_key': user.api_key
        }
    }, 'Registration successful')

# ... (other routes with similar professional enhancements) ...

# Utility Functions
def get_dummy_analysis(lat, lon):
    """Generate more realistic water analysis data"""
    bounds = [[lat - 0.1, lon - 0.1], [lat + 0.1, lon + 0.1]]
    
    # Create base pattern with distance from center
    x = np.linspace(-1, 1, 512)
    y = np.linspace(-1, 1, 512)
    xx, yy = np.meshgrid(x, y)
    dist = np.sqrt(xx**2 + yy**2)
    
    # Create base bloom pattern
    base = np.exp(-dist*3) * 255  # Exponential falloff from center
    
    # Add some random variation
    noise = np.random.normal(0, 0.2, (512, 512))
    pattern = np.clip(base * (1 + noise), 0, 255)
    
    # Threshold to create binary mask
    threshold = 0.85 * np.max(pattern)
    mask_raw = (pattern > threshold).astype(np.uint8) * 255
    
    return bounds, mask_raw

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)