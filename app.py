from flask import Flask, render_template, jsonify, request
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
from functools import wraps
import jwt

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a-very-secret-key-for-dev')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aquavision.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# CRITICAL FIX: Ensure the 'static' directory exists on startup.
os.makedirs('static', exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index' # Redirect to main page to show login modal

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    api_key = db.Column(db.String(512), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
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

class AnalysisHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    result_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Page Routes ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/api-docs')
def api_docs():
    return render_template('api-docs.html')

@app.route('/api-key')
@login_required
def api_key():
    if not current_user.api_key:
        current_user.generate_api_key()
        db.session.commit()
    return render_template('api_key.html', api_key=current_user.api_key)


# --- Auth Routes ---
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'success': False, 'error': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data.get('email')).first()
    if user and user.check_password(data.get('password')):
        login_user(user)
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'error': 'Invalid email or password'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    confirm_password = data.get('confirmPassword')
    
    if not all([name, email, password, confirm_password]):
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
    if password != confirm_password:
        return jsonify({'success': False, 'error': 'Passwords do not match'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'Email is already registered'}), 400
    
    new_user = User(email=email, name=name)
    new_user.set_password(password)
    new_user.generate_api_key()
    
    db.session.add(new_user)
    db.session.commit()
    
    login_user(new_user)
    return jsonify({'success': True}), 201

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'success': True})


# --- Frontend Endpoints (Dummy Data) ---
@app.route('/detect')
def detect_algae():
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'Location not provided.'}), 400
            
        bounds, mask_raw = get_dummy_analysis(lat, lon)
        
        rgba = np.zeros((256, 256, 4), dtype=np.uint8)
        rgba[mask_raw == 255, 0] = 255
        rgba[mask_raw == 255, 3] = 150
        img = Image.fromarray(rgba)
        timestamp = int(time.time())
        filename = f'current_algae_{timestamp}.png'
        output_path = os.path.join('static', filename)
        img.save(output_path)

        return jsonify({
            'success': True,
            'image_url': f'/{output_path}',
            'bounds': bounds
        })
    except Exception as e:
        app.logger.error(f"ERROR in /detect: {e}")
        return jsonify({'success': False, 'error': 'An internal error occurred.'}), 500

@app.route('/predict')
def predict_algae():
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'Location not provided.'}), 400

        _, current_mask_raw = get_dummy_analysis(lat, lon)
        predicted_mask = simulate_prediction(current_mask_raw)
        
        bounds = [[lat - 0.1, lon - 0.1], [lat + 0.1, lon + 0.1]]
        rgba = np.zeros((256, 256, 4), dtype=np.uint8)
        rgba[predicted_mask == 255, 0] = 255
        rgba[predicted_mask == 255, 1] = 255
        rgba[predicted_mask == 255, 3] = 130
        img = Image.fromarray(rgba)
        timestamp = int(time.time())
        filename = f'predicted_algae_{timestamp}.png'
        output_path = os.path.join('static', filename)
        img.save(output_path)

        return jsonify({
            'success': True,
            'image_url': f'/{output_path}',
            'bounds': bounds
        })
    except Exception as e:
        app.logger.error(f"ERROR in /predict: {e}")
        return jsonify({'success': False, 'error': 'An internal error occurred.'}), 500

@app.route('/history-data')
def history_data():
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    trend_data = [random.randint(5, 20) for _ in range(12)]
    severity_labels = ['Low', 'Medium', 'High']
    severity_data = [random.randint(10, 30), random.randint(5, 20), random.randint(1, 10)]
    
    timeline = []
    for i in range(5):
        date = f"{random.randint(2022, 2024)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        severity = random.choice(['Low', 'Medium', 'High'])
        timeline.append({
            'date': date, 'severity': severity,
            'description': f"Algal bloom detected with {severity.lower()} severity"
        })
    
    return jsonify({
        'success': True,
        'location_name': f"Lat: {lat:.4f}, Lon: {lon:.4f}",
        'trend_labels': months,
        'trend_data': trend_data,
        'severity_labels': severity_labels,
        'severity_data': severity_data,
        'timeline': sorted(timeline, key=lambda x: x['date'], reverse=True)
    })

# --- Utility Functions (Dummy Data) ---
def get_dummy_analysis(lat, lon):
    time.sleep(1)
    bounds = [[lat - 0.1, lon - 0.1], [lat + 0.1, lon + 0.1]]
    mask_raw = (np.random.rand(256, 256) > 0.9).astype(np.uint8) * 255
    return bounds, mask_raw

def simulate_prediction(current_mask_raw):
    time.sleep(1)
    kernel = np.ones((15, 15), np.uint8)
    return cv2.dilate(current_mask_raw, kernel, iterations=1)

if __name__ == '__main__':
    app.run(debug=True)