import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'super-secret-key')
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') == 'production'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///aquavision.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 't']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = (
        os.environ.get('MAIL_DEFAULT_SENDER_NAME', 'AquaVision AI'),
        os.environ.get('MAIL_DEFAULT_SENDER_EMAIL')
    )
    
    # Caching
    CACHE_TYPE = 'RedisCache'
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # File Uploads
    BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
    INSTANCE_PATH = BASE_DIR.parent / 'instance'
    UPLOAD_FOLDER = INSTANCE_PATH / 'uploads'
    ANALYSIS_FOLDER = INSTANCE_PATH / 'analysis'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Application
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    @classmethod
    def init_app(cls, app):
        """Initialize application with this configuration"""
        # Ensure upload directories exist
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(cls.ANALYSIS_FOLDER, exist_ok=True)
        
        # Configure logging based on environment
        if cls.FLASK_ENV == 'production':
            app.config['PROPAGATE_EXCEPTIONS'] = True