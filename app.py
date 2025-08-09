import os
from flask import Flask, render_template, jsonify, request, url_for
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
from dotenv import load_dotenv

# --- App Initialization ---
load_dotenv()
app = Flask(__name__)

# --- Configuration ---
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-super-secret-key-for-local-dev')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aquavision.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email Configuration for Password Reset
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME') # IMPORTANT: Set this in your Render environment
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD') # IMPORTANT: Use a Google App Password
app.config['MAIL_DEFAULT_SENDER'] = ('AquaVision AI', app.config['MAIL_USERNAME'])

db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index' # Redirect to main page

# CORRECTED: Configure limiter to use in-memory storage
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"], storage_uri="memory://")

os.makedirs('static', exist_ok=True)

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    api_key = db.Column(db.String(512), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    analyses = db.relationship('AnalysisHistory', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_api_key(self):
        self.api_key = jwt.encode({'user_id': self.id, 'exp': datetime.utcnow() + timedelta(days=365*5)}, app.config['SECRET_KEY'], algorithm='HS256')
        
    def get_reset_token(self):
        s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        return s.dumps(self.email, salt='password-reset-salt')
        
    @staticmethod
    def verify_reset_token(token, max_age=1800):
        s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            email = s.loads(token, salt='password-reset-salt', max_age=max_age)
            return User.query.filter_by(email=email).first()
        except:
            return None

class AnalysisHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    analysis_type = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200), nullable=False)
    result_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Main App Routes ---
@app.route('/')
@app.route('/history')
@app.route('/api-key')
@app.route('/reset-password/<token>')
def index_spa(token=None):
    return render_template('index.html')

# --- API Routes ---
@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'error': 'Email already registered'}), 400
    
    user = User(name=data['name'], email=data['email'])
    user.set_password(data['password'])
    user.generate_api_key()
    
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return jsonify({'success': True, 'user': {'name': user.name}})

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if user and user.check_password(data.get('password')):
        login_user(user)
        return jsonify({'success': True, 'user': {'name': user.name}})
    return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

@app.route('/api/auth/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'success': True})

@app.route('/api/auth/status')
def auth_status():
    if current_user.is_authenticated:
        return jsonify({'isAuthenticated': True, 'user': {'name': current_user.name}})
    return jsonify({'isAuthenticated': False})

@app.route('/api/auth/forgot_password', methods=['POST'])
@limiter.limit("3 per 15 minutes")
def forgot_password():
    data = request.get_json()
    user = User.query.filter_by(email=data['email']).first()
    if user:
        token = user.get_reset_token()
        msg = Message('Password Reset for AquaVision AI', recipients=[user.email])
        msg.html = render_template('email/reset_password.html', name=user.name, token=token)
        mail.send(msg)
    return jsonify({'success': True, 'message': 'If an account exists, a reset link has been sent.'})

@app.route('/api/auth/reset_password', methods=['POST'])
@limiter.limit("5 per hour")
def reset_password_with_token():
    data = request.get_json()
    user = User.verify_reset_token(data['token'])
    if not user:
        return jsonify({'success': False, 'error': 'Invalid or expired token.'}), 400
    user.set_password(data['password'])
    db.session.commit()
    login_user(user)
    return jsonify({'success': True, 'message': 'Password updated successfully!'})

@app.route('/api/analysis/detect')
@login_required
def detect_algae():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    bounds, mask = get_dummy_analysis(lat, lon)
    rgba = np.zeros((512, 512, 4), dtype=np.uint8)
    rgba[mask == 255, 0] = 255; rgba[mask == 255, 3] = 150
    img = Image.fromarray(rgba)
    filename = f'current_{int(time.time())}.png'
    output_path = os.path.join('static', filename)
    img.save(output_path)
    
    history = AnalysisHistory(user_id=current_user.id, analysis_type='detect', latitude=lat, longitude=lon, image_url=f'/{output_path}', result_data={'coverage': round(np.count_nonzero(mask) / mask.size * 100, 2)})
    db.session.add(history)
    db.session.commit()
    
    return jsonify({'success': True, 'image_url': f'/{output_path}', 'bounds': bounds})

@app.route('/api/analysis/predict')
@login_required
def predict_algae():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    bounds, mask = get_dummy_analysis(lat, lon)
    predicted_mask = simulate_prediction(mask)
    rgba = np.zeros((512, 512, 4), dtype=np.uint8)
    rgba[predicted_mask == 255, 0] = 255; rgba[predicted_mask == 255, 1] = 255; rgba[predicted_mask == 255, 3] = 130
    img = Image.fromarray(rgba)
    filename = f'predicted_{int(time.time())}.png'
    output_path = os.path.join('static', filename)
    img.save(output_path)
    
    history = AnalysisHistory(user_id=current_user.id, analysis_type='predict', latitude=lat, longitude=lon, image_url=f'/{output_path}', result_data={'risk': random.choice(['High', 'Medium', 'Low'])})
    db.session.add(history)
    db.session.commit()
    
    return jsonify({'success': True, 'image_url': f'/{output_path}', 'bounds': bounds})

@app.route('/api/history')
@login_required
def get_history():
    page = request.args.get('page', 1, type=int)
    paginated_history = current_user.analyses.order_by(AnalysisHistory.created_at.desc()).paginate(page=page, per_page=5)
    
    return jsonify({
        'success': True,
        'history': [{'id': h.id, 'type': h.analysis_type, 'lat': h.latitude, 'lon': h.longitude, 'date': h.created_at.strftime('%Y-%m-%d %H:%M'), 'image_url': h.image_url, 'data': h.result_data} for h in paginated_history.items],
        'pagination': {'page': page, 'total_pages': paginated_history.pages, 'has_next': paginated_history.has_next, 'has_prev': paginated_history.has_prev}
    })

# --- Utility Functions ---
def get_dummy_analysis(lat, lon):
    time.sleep(0.5)
    bounds = [[lat - 0.1, lon - 0.1], [lat + 0.1, lon + 0.1]]
    x, y = np.meshgrid(np.linspace(-1, 1, 512), np.linspace(-1, 1, 512))
    dist = np.sqrt(x**2 + y**2)
    pattern = np.sin(dist * 10 + np.random.uniform(0, 3.14)) * np.exp(-dist * 2)
    mask_raw = (pattern > 0.5).astype(np.uint8) * 255
    return bounds, mask_raw

def simulate_prediction(current_mask):
    time.sleep(0.5)
    kernel = np.ones((15, 15), np.uint8)
    return cv2.dilate(current_mask, kernel, iterations=1)

if __name__ == '__main__':
    app.run(debug=True)