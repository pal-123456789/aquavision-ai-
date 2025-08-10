from datetime import datetime
from flask import current_app
from ..extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import timedelta

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    api_key = db.Column(db.String(512), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    email_verified = db.Column(db.Boolean, default=False)
    login_attempts = db.Column(db.Integer, default=0)
    last_attempt = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_api_key(self):
        self.api_key = jwt.encode(
            {'user_id': self.id, 'exp': datetime.utcnow() + timedelta(days=365)},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return self.api_key
    
    def get_reset_token(self, expires_sec=1800):
        return jwt.encode(
            {'user_id': self.id, 'exp': datetime.utcnow() + timedelta(seconds=expires_sec)},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_token(token):
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            return User.query.get(data['user_id'])
        except:
            return None