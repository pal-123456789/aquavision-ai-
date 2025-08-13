import os
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
import numpy as np
from PIL import Image
import time
import cv2

# Initialize Flask app
app = Flask(__name__)

# --- Configuration ---
app.config.update(
    SECRET_KEY=os.environ.get('SECRET_KEY', 'a-very-secret-key-for-local-dev'),
    SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///aquavision.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# --- Extensions ---
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'index'

# Reconfigure Limiter and Cache to use memory, which fixes server crashes
limiter = Limiter(app=app, key_func=get_remote_address, storage_uri="memory://")
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# Ensure the 'static' directory exists for saving analysis images
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

# --- Main App Route ---
@app.route('/')
def index():
    # This route serves your main index.html file
    return render_template('./templates/index.html')

# --- API Routes for Login/Registration ---
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if User.query.filter_by(email=data['email']).first():
        return error_response('Email is already registered.', 400)
    user = User(name=data['name'], email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return success_response({'user': {'name': user.name}}, 'Registration successful!')

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if user and user.check_password(data.get('password')):
        login_user(user)
        return success_response({'user': {'name': user.name}})
    return error_response('Invalid email or password.', 401)

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

# --- API Route for Analysis ---
@app.route('/api/analysis/detect')
@login_required
def detect_algae():
    # This is a dummy analysis function for demonstration
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    bounds = [[lat - 0.2, lon - 0.2], [lat + 0.2, lon + 0.2]]
    mask = (np.random.rand(256, 256) > 0.9).astype(np.uint8) * 255
    rgba = np.zeros((256, 256, 4), dtype=np.uint8)
    rgba[mask == 255, 0] = 255
    rgba[mask == 255, 3] = 150
    img = Image.fromarray(rgba)
    filename = f'analysis_{int(time.time())}.png'
    output_path = os.path.join('static', filename)
    img.save(output_path)
    return success_response({'image_url': f'/{output_path}', 'bounds': bounds})

# --- Final Setup ---
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)