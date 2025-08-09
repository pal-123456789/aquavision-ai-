import os
import cv2
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from itsdangerous import URLSafeTimedSerializer
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import redis
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from flask_httpauth import HTTPTokenAuth
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
from sklearn.ensemble import RandomForestClassifier
import joblib
import rasterio
import geopandas as gpd
import folium
from folium.plugins import HeatMap
import requests
from io import BytesIO
from PIL import Image

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
            "'unsafe-inline'"
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
            'api.maptiler.com',
            'api.nasa.gov'
        ]
    }
)

# Configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY'),
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///instance/aquavision.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={'pool_pre_ping': True, 'pool_recycle': 300},
    MAIL_SERVER=os.environ.get('MAIL_SERVER'),
    MAIL_PORT=int(os.environ.get('MAIL_PORT', 587)),
    MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't'],
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=(os.environ.get('MAIL_DEFAULT_SENDER_NAME', 'AquaVision AI')),
    CACHE_TYPE='RedisCache',
    CACHE_REDIS_URL=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
    CACHE_DEFAULT_TIMEOUT=300,
    MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    UPLOAD_FOLDER=os.path.join('static', 'uploads'),
    ANALYSIS_FOLDER=os.path.join('static', 'analysis'),
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    NASA_API_KEY=os.environ.get('NASA_API_KEY', 'DEMO_KEY')
)

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
cache = Cache(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'
auth = HTTPTokenAuth(scheme='Bearer')

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=app.config['CACHE_REDIS_URL'],
    strategy="fixed-window"
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

# Load ML model (simplified example)
try:
    BLOOM_MODEL = joblib.load('models/bloom_detector.pkl')
except:
    app.logger.warning("No pre-trained model found, using dummy model")
    BLOOM_MODEL = None

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

# Helper functions
def success_response(data=None, message=None):
    return jsonify({'success': True, 'data': data, 'message': message})

def error_response(message, status_code=400):
    return jsonify({'success': False, 'error': message}), status_code

def detect_blooms(image_path):
    """Advanced bloom detection using computer vision"""
    try:
        # Load satellite image
        img = cv2.imread(image_path)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # Define color ranges for algal blooms
        lower_green = np.array([30, 40, 40])
        upper_green = np.array([90, 255, 255])
        
        # Create mask
        mask = cv2.inRange(hsv, lower_green, upper_green)
        result = cv2.bitwise_and(img, img, mask=mask)
        
        # Calculate coverage percentage
        total_pixels = mask.size
        bloom_pixels = np.count_nonzero(mask)
        coverage = (bloom_pixels / total_pixels) * 100
        
        # Determine severity
        if coverage < 5:
            severity = "low"
        elif coverage < 20:
            severity = "medium"
        else:
            severity = "high"
            
        return {
            "coverage": round(coverage, 2),
            "severity": severity,
            "mask": mask,
            "result_image": result
        }
    except Exception as e:
        app.logger.error(f"Error in bloom detection: {str(e)}")
        return None

def predict_bloom_risk(lat, lon):
    """Predict future bloom risk using environmental data"""
    try:
        # Get weather data (simplified example)
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={app.config['NASA_API_KEY']}"
        response = requests.get(weather_url)
        weather_data = response.json()
        
        # Get water temperature (mock data)
        water_temp = 18 + (np.random.random() * 10)  # Simulated data
        
        # Predict using model (or simulated logic)
        if BLOOM_MODEL:
            features = [[lat, lon, water_temp, weather_data['main']['temp']]]
            risk = BLOOM_MODEL.predict_proba(features)[0][1]
        else:
            # Fallback simulation
            risk = 0.3 + (water_temp - 15) * 0.02
        
        risk = min(max(risk, 0), 1)  # Clamp between 0-1
        
        if risk < 0.4:
            risk_level = "low"
        elif risk < 0.7:
            risk_level = "medium"
        else:
            risk_level = "high"
            
        return {
            "risk_score": round(risk, 2),
            "risk_level": risk_level,
            "water_temp": round(water_temp, 1),
            "air_temp": round(weather_data['main']['temp'] - 273.15, 1)  # Convert K to C
        }
    except Exception as e:
        app.logger.error(f"Error in bloom prediction: {str(e)}")
        return None

# API Routes
@app.route('/api/detect', methods=['POST'])
@auth.login_required
def detect_bloom():
    try:
        data = request.json
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
        radius = int(data.get('radius', 10))
        
        # Get satellite image (simulated)
        image_url = f"https://api.nasa.gov/planetary/earth/imagery?lon={lon}&lat={lat}&date=2023-11-01&dim={radius}&api_key={app.config['NASA_API_KEY']}"
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        
        # Save and analyze
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], f"detect_{datetime.now().timestamp()}.jpg")
        img.save(img_path)
        
        analysis = detect_blooms(img_path)
        if not analysis:
            return error_response("Analysis failed", 500)
            
        # Save result image
        result_path = os.path.join(app.config['ANALYSIS_FOLDER'], f"result_{datetime.now().timestamp()}.jpg")
        cv2.imwrite(result_path, analysis['result_image'])
        
        # Save to history
        if current_user.is_authenticated:
            history = AnalysisHistory(
                user_id=current_user.id,
                analysis_type="detection",
                latitude=lat,
                longitude=lon,
                image_url=result_path,
                result_data=analysis
            )
            db.session.add(history)
            db.session.commit()
        
        return success_response({
            "image_url": url_for('static', filename=f"analysis/{os.path.basename(result_path)}"),
            "bounds": [[lat-0.1, lon-0.1], [lat+0.1, lon+0.1]],
            "coverage": analysis['coverage'],
            "severity": analysis['severity'],
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        app.logger.error(f"API error: {str(e)}")
        return error_response("Server error", 500)

@app.route('/api/predict', methods=['POST'])
@auth.login_required
def predict_bloom():
    try:
        data = request.json
        lat = float(data.get('lat'))
        lon = float(data.get('lon'))
        days = int(data.get('days', 7))
        
        prediction = predict_bloom_risk(lat, lon)
        if not prediction:
            return error_response("Prediction failed", 500)
            
        # Save to history
        if current_user.is_authenticated:
            history = AnalysisHistory(
                user_id=current_user.id,
                analysis_type="prediction",
                latitude=lat,
                longitude=lon,
                result_data=prediction
            )
            db.session.add(history)
            db.session.commit()
        
        return success_response({
            "risk_score": prediction['risk_score'],
            "risk_level": prediction['risk_level'],
            "water_temp": prediction['water_temp'],
            "air_temp": prediction['air_temp'],
            "prediction_date": (datetime.utcnow() + timedelta(days=days)).isoformat()
        })
    except Exception as e:
        app.logger.error(f"API error: {str(e)}")
        return error_response("Server error", 500)

# Main App Routes
@app.route('/')
@app.route('/history')
@app.route('/api-key')
@app.route('/reset-password/<token>')
def index_spa(token=None):
    return render_template('index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)