from flask import Flask
from .config import Config
from .extensions import db, migrate, login_manager, mail, cache, limiter
# backend/src/__init__.py
from .app import create_app

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    
    # Register blueprints
    from .auth.routes import auth_bp
    from .analysis.routes import analysis_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')
    
    # Create upload directories
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['ANALYSIS_FOLDER'], exist_ok=True)
    
    return app