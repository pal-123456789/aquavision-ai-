# Add at the top of app.py
from flask import Flask, render_template, jsonify, request, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import numpy as np
from PIL import Image
import time
import cv2
import os
import random
import jwt
from functools import wraps
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import logging
from logging.handlers import RotatingFileHandler
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import redis
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Configuration updates
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key'),
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///aquavision.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAIL_SERVER=os.environ.get('MAIL_SERVER', 'smtp.gmail.com'),
    MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
    MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true',
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=(os.environ.get('MAIL_DEFAULT_SENDER_NAME', 'AquaVision AI'),
                         os.environ.get('MAIL_DEFAULT_SENDER_EMAIL')),
    CACHE_TYPE='RedisCache',
    CACHE_REDIS_URL=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    CACHE_DEFAULT_TIMEOUT=300,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,  # 16MB upload limit
    UPLOAD_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads'),
    ANALYSIS_FOLDER=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'analysis'),
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

# Ensure upload directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['ANALYSIS_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
mail = Mail(app)
cache = Cache(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=app.config['CACHE_REDIS_URL']  # Use Redis for rate limiting
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
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    api_key = db.Column(db.String(512), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100))
    login_attempts = db.Column(db.Integer, default=0)
    last_attempt = db.Column(db.DateTime)
    
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
    
    def generate_verification_token(self):
        self.verification_token = reset_serializer.dumps(self.email, salt='email-verify')
        return self.verification_token

class AnalysisHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    analysis_type = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
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

# API Key Decorator
def api_key_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API key required'}), 401
        
        try:
            data = jwt.decode(api_key, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                raise ValueError("User not found")
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'error': 'API key expired'}), 401
        except (jwt.InvalidTokenError, ValueError) as e:
            app.logger.warning(f"Invalid API key attempt: {str(e)}")
            return jsonify({'success': False, 'error': 'Invalid API key'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated_function

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Resource not found'}), 404
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return render_template('errors/500.html'), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    if request.path.startswith('/api/'):
        return jsonify({
            "success": False,
            "error": "ratelimit exceeded",
            "message": str(e.description)
        }), 429
    return render_template('errors/429.html'), 429

# Routes
@app.route('/')
@cache.cached(timeout=60)
def index():
    return render_template('index.html')

@app.route('/about')
@cache.cached(timeout=3600)
def about():
    return render_template('about.html')

@app.route('/history')
@login_required
def history():
    return render_template('history.html')

@app.route('/api-docs')
@cache.cached(timeout=3600)
def api_docs():
    return render_template('api-docs.html')

@app.route('/api-key')
@login_required
def api_key():
    if not current_user.api_key:
        current_user.generate_api_key()
        db.session.commit()
    return render_template('api_key.html', api_key=current_user.api_key)

# Enhanced Auth Routes
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    if request.method == 'POST':
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=data.get('email')).first()
        
        # Brute force protection
        if user and user.login_attempts >= 5 and user.last_attempt and (datetime.utcnow() - user.last_attempt) < timedelta(minutes=15):
            return jsonify({
                'success': False,
                'error': 'Account temporarily locked. Try again later.'
            }), 429
        
        if user and user.check_password(data.get('password')):
            if not user.is_active:
                return jsonify({'success': False, 'error': 'Account disabled'}), 403
            if not user.email_verified:
                return jsonify({
                    'success': False, 
                    'error': 'Email not verified',
                    'resend_url': url_for('resend_verification')
                }), 403
            
            # Reset login attempts on successful login
            user.login_attempts = 0
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'redirect': url_for('index')
            })
        
        # Increment failed login attempts
        if user:
            user.login_attempts += 1
            user.last_attempt = datetime.utcnow()
            db.session.commit()
        
        return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    if request.method == 'POST':
        data = request.get_json()
        if not data or not all([data.get('name'), data.get('email'), data.get('password'), data.get('confirmPassword')]):
            return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
        if data.get('password') != data.get('confirmPassword'):
            return jsonify({'success': False, 'error': 'Passwords do not match'}), 400
        
        password = data.get('password')
        if len(password) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
        if not re.search(r'[A-Z]', password):
            return jsonify({'success': False, 'error': 'Password must contain at least one uppercase letter'}), 400
        if not re.search(r'[\W_]', password):
            return jsonify({'success': False, 'error': 'Password must contain at least one special character'}), 400
        
        if User.query.filter_by(email=data.get('email')).first():
            return jsonify({'success': False, 'error': 'Email already registered'}), 400
        
        user = User(email=data.get('email'), name=data.get('name'))
        user.set_password(password)
        user.generate_api_key()
        user.generate_verification_token()
        
        db.session.add(user)
        db.session.commit()
        
        try:
            send_verification_email(user)
            return jsonify({
                'success': True,
                'message': 'Registration successful! Please check your email to verify your account.'
            }), 201
        except Exception as e:
            app.logger.error(f"Failed to send verification email: {str(e)}")
            db.session.delete(user)
            db.session.commit()
            return jsonify({
                'success': False,
                'error': 'Failed to send verification email. Please try again later.'
            }), 500
    
    return render_template('auth/register.html')

# ... (Other auth routes remain similar but with password complexity checks added) ...

# API Endpoints
@app.route('/api/v1/detect')
@api_key_required
@limiter.limit("60 per hour")
@cache.cached(timeout=300, query_string=True)
def detect_algae(user):
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'Latitude and longitude required'}), 400
            
        # Validate coordinate ranges
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({'success': False, 'error': 'Invalid coordinates'}), 400
            
        bounds, mask_raw = get_dummy_analysis(lat, lon)
        
        # Use configured analysis folder
        os.makedirs(app.config['ANALYSIS_FOLDER'], exist_ok=True)
        
        rgba = np.zeros((512, 512, 4), dtype=np.uint8)  # Higher resolution
        rgba[mask_raw == 255, 0] = 255  # Red channel for bloom areas
        rgba[mask_raw == 255, 3] = 150  # Alpha channel for transparency
        img = Image.fromarray(rgba)
        timestamp = int(time.time())
        filename = f'current_{timestamp}.png'
        output_path = os.path.join(app.config['ANALYSIS_FOLDER'], filename)
        img.save(output_path, optimize=True, quality=85)

        # Save to history
        history = AnalysisHistory(
            user_id=user.id,
            analysis_type='detect',
            latitude=lat,
            longitude=lon,
            result_data={
                'image_url': f'/static/analysis/{filename}',
                'bounds': bounds,
                'bloom_coverage': round(random.uniform(5, 50), 1),
                'severity': random.choice(['low', 'medium', 'high'])
            }
        )
        db.session.add(history)
        db.session.commit()

        return jsonify(history.result_data)
    except Exception as e:
        app.logger.error(f"Error in detect_algae: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/v1/predict')
@api_key_required
@limiter.limit("60 per hour")
@cache.cached(timeout=300, query_string=True)
def predict_algae(user):
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        days = request.args.get('days', default=7, type=int)
        
        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'Latitude and longitude required'}), 400
            
        # Validate coordinate ranges
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return jsonify({'success': False, 'error': 'Invalid coordinates'}), 400
            
        if not 1 <= days <= 30:
            return jsonify({'success': False, 'error': 'Days must be between 1 and 30'}), 400
            
        bounds, mask_raw = get_dummy_analysis(lat, lon)
        predicted_mask = simulate_prediction(mask_raw, days)
        
        # Use configured analysis folder
        os.makedirs(app.config['ANALYSIS_FOLDER'], exist_ok=True)
        
        rgba = np.zeros((512, 512, 4), dtype=np.uint8)
        rgba[predicted_mask == 255, 0] = 255  # Red
        rgba[predicted_mask == 255, 1] = 165  # Orange
        rgba[predicted_mask == 255, 3] = 150  # Alpha
        img = Image.fromarray(rgba)
        timestamp = int(time.time())
        filename = f'predicted_{timestamp}.png'
        output_path = os.path.join(app.config['ANALYSIS_FOLDER'], filename)
        img.save(output_path, optimize=True, quality=85)

        # Save to history
        history = AnalysisHistory(
            user_id=user.id,
            analysis_type='predict',
            latitude=lat,
            longitude=lon,
            result_data={
                'image_url': f'/static/analysis/{filename}',
                'bounds': bounds,
                'risk_level': random.choice(['low', 'medium', 'high']),
                'confidence': round(random.uniform(0.7, 0.95), 2),
                'prediction_days': days
            }
        )
        db.session.add(history)
        db.session.commit()

        return jsonify(history.result_data)
    except Exception as e:
        app.logger.error(f"Error in predict_algae: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/api/v1/history')
@api_key_required
def get_history(user):
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 100)
        
        query = AnalysisHistory.query.filter_by(user_id=user.id)
        
        # Apply filters if provided
        if request.args.get('type'):
            query = query.filter_by(analysis_type=request.args.get('type'))
        
        if request.args.get('start_date'):
            try:
                start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
                query = query.filter(AnalysisHistory.created_at >= start_date)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid start_date format (YYYY-MM-DD)'}), 400
        
        if request.args.get('end_date'):
            try:
                end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')
                query = query.filter(AnalysisHistory.created_at <= end_date)
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid end_date format (YYYY-MM-DD)'}), 400
        
        # Order and paginate
        history = query.order_by(AnalysisHistory.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'success': True,
            'data': [{
                'id': item.id,
                'type': item.analysis_type,
                'latitude': item.latitude,
                'longitude': item.longitude,
                'date': item.created_at.isoformat(),
                'result': item.result_data
            } for item in history.items],
            'pagination': {
                'page': history.page,
                'per_page': history.per_page,
                'total': history.total,
                'pages': history.pages
            }
        })
    except Exception as e:
        app.logger.error(f"Error in get_history: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/health')
def health_check():
    # Database health check
    try:
        db.session.execute(db.text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        app.logger.error(f"Database health check failed: {str(e)}")
        db_status = 'disconnected'
    
    # Redis health check
    try:
        redis_conn = redis.from_url(app.config['CACHE_REDIS_URL'])
        redis_connected = redis_conn.ping()
    except Exception as e:
        app.logger.error(f"Redis health check failed: {str(e)}")
        redis_connected = False
    
    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'redis': 'connected' if redis_connected else 'disconnected'
    })

# Utility functions
def send_verification_email(user):
    verify_url = url_for('verify_email', token=user.verification_token, _external=True)
    
    msg = Message("Verify Your Email Address",
                recipients=[user.email])
    msg.body = f"""Welcome to AquaVision AI!

Please click the following link to verify your email address:
{verify_url}

This link will expire in 24 hours.

If you did not create an account, please ignore this email.
"""
    mail.send(msg)
    app.logger.info(f"Verification email sent to {user.email}")

def get_dummy_analysis(lat, lon):
    """Generate a more realistic looking bloom pattern"""
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

def simulate_prediction(current_mask, days=7):
    """Simulate bloom expansion over time"""
    # Convert to OpenCV format
    mask = current_mask.astype(np.uint8)
    
    # Simulate growth based on number of days
    kernel_size = min(5 + days, 21)  # Larger kernel for more days
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    
    # Dilate to simulate spread
    predicted = cv2.dilate(mask, kernel, iterations=1)
    
    # Add some random new spots
    if days > 3:
        spots = np.random.random((512, 512)) > 0.995
        predicted[spots] = 255
    
    return predicted

if __name__ == '__main__':
    # Run the app
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)