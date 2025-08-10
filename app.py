import os
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import numpy as np
from PIL import Image
import time
import cv2
import random
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'dev-secret-key-12345'),
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///aquavision.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'

# CRITICAL FIX: Configure Limiter and Cache to use memory, NOT Redis
limiter = Limiter(app=app, key_func=get_remote_address, storage_uri="memory://")
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# Ensure static directory exists for saving images
os.makedirs('static', exist_ok=True)

# --- Database Models ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- API Response Helpers ---
def success_response(data=None, message=""):
    return jsonify({'success': True, 'data': data, 'message': message})

def error_response(message, status_code=400):
    return jsonify({'success': False, 'error': message}), status_code

# --- Main App Routes ---
@app.route('/')
@app.route('/<path:path>') # Catch-all for SPA routing
def index_spa(path=None):
    return render_template('index.html')

# --- API Routes ---
@app.route('/api/auth/register', methods=['POST'])
@limiter.limit("5 per hour")
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return error_response('Email already registered', 400)
    user = User(name=data['name'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return success_response({'user': {'name': user.name}}, 'Registration successful')

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("20 per minute")
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if user and user.check_password(data.get('password')):
        login_user(user)
        return success_response({'user': {'name': user.name}})
    return error_response('Invalid credentials', 401)

@app.route('/api/auth/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return success_response()

@app.route('/api/auth/status')
def auth_status():
    if current_user.is_authenticated:
        return success_response({'isAuthenticated': True, 'user': {'name': current_user.name}})
    return success_response({'isAuthenticated': False})

# --- Dummy Analysis Route ---
@app.route('/api/analysis/detect')
@login_required
def detect_algae():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
        bounds = [[lat - 0.1, lon - 0.1], [lat + 0.1, lon + 0.1]]
        x = np.linspace(-1, 1, 512); y = np.linspace(-1, 1, 512)
        xx, yy = np.meshgrid(x, y); dist = np.sqrt(xx**2 + yy**2)
        pattern = np.sin(dist * 12 + np.random.uniform(0, 6)) * np.exp(-dist * 2.5)
        mask = (pattern > 0.6).astype(np.uint8) * 255
        rgba = np.zeros((512, 512, 4), dtype=np.uint8)
        rgba[mask == 255, 0] = 255; rgba[mask == 255, 3] = 150
        img = Image.fromarray(rgba)
        filename = f'current_{int(time.time())}.png'
        output_path = os.path.join('static', filename)
        img.save(output_path)
        return success_response({'image_url': f'/{output_path}', 'bounds': bounds})
    except Exception as e:
        app.logger.error(f"Analysis error: {e}")
        return error_response("Analysis failed", 500)

# --- Error Handlers ---
@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

# Create DB tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)