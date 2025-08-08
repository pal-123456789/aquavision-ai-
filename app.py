from flask import Flask, render_template, jsonify, request, send_from_directory
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
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///aquavision.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    api_key = db.Column(db.String(100), unique=True)
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
        return self.api_key

class AnalysisHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    analysis_type = db.Column(db.String(50), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    result_data = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
        except:
            return jsonify({'success': False, 'error': 'Invalid API key'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated_function

# Routes
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

# API Endpoints
@app.route('/api/v1/detect')
@api_key_required
def api_detect_algae(user):
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        radius = request.args.get('radius', default=10, type=int)
        
        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'Latitude and longitude required'}), 400
            
        bounds, mask_raw = get_dummy_analysis(lat, lon)
        
        rgba = np.zeros((256, 256, 4), dtype=np.uint8)
        rgba[mask_raw == 255, 0] = 255  # Red
        rgba[mask_raw == 255, 3] = 150  # Alpha
        img = Image.fromarray(rgba)
        timestamp = int(time.time())
        filename = f'current_algae_{timestamp}.png'
        output_path = os.path.join('static', filename)
        img.save(output_path)
        
        # Log analysis in history
        history = AnalysisHistory(
            user_id=user.id,
            analysis_type='detect',
            latitude=lat,
            longitude=lon,
            result_data={
                'image_url': f'/static/{filename}',
                'bounds': bounds,
                'bloom_coverage': round(random.uniform(5, 50), 1),
                'severity': random.choice(['low', 'medium', 'high'])
            }
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'image_url': f'/static/{filename}',
            'bounds': bounds,
            'bloom_coverage': history.result_data['bloom_coverage'],
            'severity': history.result_data['severity'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
    except Exception as e:
        app.logger.error(f"ERROR in /api/v1/detect: {e}")
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500

@app.route('/api/v1/predict')
@api_key_required
def api_predict_algae(user):
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        days = request.args.get('days', default=7, type=int)
        
        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'Latitude and longitude required'}), 400

        _, current_mask_raw = get_dummy_analysis(lat, lon)
        predicted_mask = simulate_prediction(current_mask_raw)
        
        bounds = [[lat - 0.5, lon - 0.5], [lat + 0.5, lon + 0.5]]
        rgba = np.zeros((256, 256, 4), dtype=np.uint8)
        rgba[predicted_mask == 255, 0] = 255  # Yellow
        rgba[predicted_mask == 255, 1] = 255
        rgba[predicted_mask == 255, 3] = 130  # Alpha
        img = Image.fromarray(rgba)
        timestamp = int(time.time())
        filename = f'predicted_algae_{timestamp}.png'
        output_path = os.path.join('static', filename)
        img.save(output_path)
        
        # Log analysis in history
        history = AnalysisHistory(
            user_id=user.id,
            analysis_type='predict',
            latitude=lat,
            longitude=lon,
            result_data={
                'image_url': f'/static/{filename}',
                'bounds': bounds,
                'risk_level': random.choice(['low', 'medium', 'high']),
                'confidence': round(random.uniform(0.7, 0.95), 2)
            }
        )
        db.session.add(history)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'image_url': f'/static/{filename}',
            'bounds': bounds,
            'risk_level': history.result_data['risk_level'],
            'confidence': history.result_data['confidence'],
            'prediction_date': (datetime.utcnow() + timedelta(days=days)).isoformat() + 'Z'
        })

    except Exception as e:
        app.logger.error(f"ERROR in /api/v1/predict: {e}")
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500

@app.route('/api/v1/history')
@api_key_required
def api_history(user):
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', default=100, type=int)
        
        query = AnalysisHistory.query.filter_by(user_id=user.id)
        
        if lat is not None and lon is not None:
            query = query.filter(
                db.func.abs(AnalysisHistory.latitude - lat) < 1,
                db.func.abs(AnalysisHistory.longitude - lon) < 1
            )
        
        if start_date:
            query = query.filter(AnalysisHistory.created_at >= start_date)
        if end_date:
            query = query.filter(AnalysisHistory.created_at <= end_date)
        
        history = query.order_by(AnalysisHistory.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'success': True,
            'data': [{
                'date': h.created_at.isoformat() + 'Z',
                'location': [h.latitude, h.longitude],
                'type': h.analysis_type,
                'result': h.result_data
            } for h in history],
            'count': len(history)
        })
        
    except Exception as e:
        app.logger.error(f"ERROR in /api/v1/history: {e}")
        return jsonify({'success': False, 'error': 'An internal error occurred'}), 500

# Frontend Endpoints
@app.route('/detect')
def detect_algae():
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'Location not provided.'}), 400
            
        bounds, mask_raw = get_dummy_analysis(lat, lon)
        
        rgba = np.zeros((256, 256, 4), dtype=np.uint8)
        rgba[mask_raw == 255, 0] = 255  # Red
        rgba[mask_raw == 255, 3] = 150  # Alpha
        img = Image.fromarray(rgba)
        timestamp = int(time.time())
        output_path = os.path.join('static', f'current_algae_{timestamp}.png')
        img.save(output_path)

        return jsonify({
            'success': True,
            'image_url': f'/static/current_algae_{timestamp}.png',
            'bounds': bounds,
            'bloom_coverage': round(random.uniform(5, 50), 1),
            'severity': random.choice(['low', 'medium', 'high'])
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
        
        bounds = [[lat - 0.5, lon - 0.5], [lat + 0.5, lon + 0.5]]
        rgba = np.zeros((256, 256, 4), dtype=np.uint8)
        rgba[predicted_mask == 255, 0] = 255  # Yellow
        rgba[predicted_mask == 255, 1] = 255
        rgba[predicted_mask == 255, 3] = 130  # Alpha
        img = Image.fromarray(rgba)
        timestamp = int(time.time())
        output_path = os.path.join('static', f'predicted_algae_{timestamp}.png')
        img.save(output_path)

        return jsonify({
            'success': True,
            'image_url': f'/static/predicted_algae_{timestamp}.png',
            'bounds': bounds,
            'risk_level': random.choice(['low', 'medium', 'high']),
            'confidence': round(random.uniform(0.7, 0.95), 2)
        })

    except Exception as e:
        app.logger.error(f"ERROR in /predict: {e}")
        return jsonify({'success': False, 'error': 'An internal error occurred.'}), 500

@app.route('/history-data')
def history_data():
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        
        # Generate dummy historical data
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        trend_data = [random.randint(5, 20) for _ in range(12)]
        
        severity_labels = ['Low', 'Medium', 'High']
        severity_data = [random.randint(10, 30), random.randint(5, 20), random.randint(1, 10)]
        
        timeline = []
        for i in range(5):
            date = f"{random.randint(2020, 2023)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
            severity = random.choice(['Low', 'Medium', 'High'])
            timeline.append({
                'date': date,
                'severity': severity,
                'description': f"Algal bloom detected with {severity.lower()} severity"
            })
        
        return jsonify({
            'success': True,
            'location_name': "Selected Location" if not lat or not lon else f"Lat: {lat:.4f}, Lon: {lon:.4f}",
            'trend_labels': months,
            'trend_data': trend_data,
            'severity_labels': severity_labels,
            'severity_data': severity_data,
            'timeline': sorted(timeline, key=lambda x: x['date'], reverse=True)
        })
        
    except Exception as e:
        app.logger.error(f"ERROR in /history-data: {e}")
        return jsonify({'success': False, 'error': 'An internal error occurred.'}), 500

# Auth Routes
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
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
    
    if password != confirm_password:
        return jsonify({'success': False, 'error': 'Passwords do not match'}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'error': 'Email already registered'}), 400
    
    user = User(email=email, name=name)
    user.set_password(password)
    user.generate_api_key()
    
    db.session.add(user)
    db.session.commit()
    
    login_user(user)
    return jsonify({'success': True})

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'success': True})

# Utility Functions
def get_dummy_analysis(lat, lon):
    time.sleep(1)  # Simulate processing time
    bounds = [[lat - 0.5, lon - 0.5], [lat + 0.5, lon + 0.5]]
    mask_raw = (np.random.rand(256, 256) > 0.9).astype(np.uint8) * 255
    return bounds, mask_raw

def simulate_prediction(current_mask_raw):
    time.sleep(1)  # Simulate prediction time
    kernel = np.ones((15, 15), np.uint8)
    predicted_mask = cv2.dilate(current_mask_raw, kernel, iterations=1)
    return predicted_mask

if __name__ == '__main__':
    app.run(debug=True)