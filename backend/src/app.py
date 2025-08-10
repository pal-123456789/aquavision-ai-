import os
from flask import Flask
from src.config import Config
from src.extensions import db, migrate, login_manager, mail, cache, limiter

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    
    # Configure application
    app.config.from_object(config_class)
    
    # Initialize extensions
    initialize_extensions(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Ensure upload directories exist
    create_upload_directories(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app

def initialize_extensions(app):
    """Initialize Flask extensions"""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    
    # Configure login manager
    from src.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

def register_blueprints(app):
    """Register Flask blueprints"""
    from src.auth.routes import auth_bp
    from src.analysis.routes import analysis_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')

def create_upload_directories(app):
    """Ensure upload directories exist"""
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['ANALYSIS_FOLDER'], exist_ok=True)
    except OSError as e:
        app.logger.error(f"Failed to create upload directories: {e}")
        if app.config['FLASK_ENV'] == 'production':
            raise

def register_error_handlers(app):
    """Register error handlers"""
    
    from flask import jsonify
    from werkzeug.exceptions import HTTPException
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Handle HTTP exceptions with JSON responses"""
        response = {
            "error": e.name,
            "message": e.description,
            "status": e.code
        }
        return jsonify(response), e.code
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        """Handle unexpected exceptions"""
        app.logger.error(f"Unexpected error: {e}")
        
        if app.config['FLASK_ENV'] == 'production':
            response = {
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "status": 500
            }
            return jsonify(response), 500
        raise e