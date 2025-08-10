from ..models.user import User
from ..extensions import db, mail
from flask import current_app, url_for, render_template
from .schemas import UserCreateSchema, UserLoginSchema
from werkzeug.exceptions import BadRequest, Unauthorized
from flask_mail import Message
from datetime import datetime

def register_user(data):
    # Validate input
    try:
        user_data = UserCreateSchema(**data)
    except Exception as e:
        raise BadRequest(str(e))
    
    # Check if user exists
    if User.query.filter_by(email=user_data.email).first():
        raise BadRequest('Email already registered')
    
    # Create user
    user = User(name=user_data.name, email=user_data.email)
    user.set_password(user_data.password)
    user.generate_api_key()
    
    db.session.add(user)
    db.session.commit()
    
    # Send welcome email
    send_welcome_email(user)
    
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'api_key': user.api_key
    }

def login_user(data):
    try:
        login_data = UserLoginSchema(**data)
    except Exception as e:
        raise BadRequest(str(e))
    
    user = User.query.filter_by(email=login_data.email).first()
    
    # Brute force protection
    if user and user.login_attempts >= 5 and user.last_attempt and (datetime.utcnow() - user.last_attempt).seconds < 900:
        raise Unauthorized('Account temporarily locked. Try again later.')
    
    if not user or not user.check_password(login_data.password):
        if user:
            user.login_attempts += 1
            user.last_attempt = datetime.utcnow()
            db.session.commit()
        raise Unauthorized('Invalid email or password')
    
    # Reset login attempts
    user.login_attempts = 0
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'api_key': user.api_key
    }

def send_password_reset(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return  # Don't reveal if user exists
    
    reset_token = user.get_reset_token()
    reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
    
    msg = Message('Password Reset Request', recipients=[user.email])
    msg.body = render_template('email/reset_password.txt', reset_url=reset_url)
    msg.html = render_template('email/reset_password.html', reset_url=reset_url)
    
    mail.send(msg)

def reset_password(token, new_password):
    user = User.verify_reset_token(token)
    if not user:
        raise BadRequest('Invalid or expired token')
    
    user.set_password(new_password)
    db.session.commit()
    return user

def send_welcome_email(user):
    msg = Message('Welcome to AquaVision AI', recipients=[user.email])
    msg.body = render_template('email/welcome.txt', name=user.name)
    msg.html = render_template('email/welcome.html', name=user.name)
    mail.send(msg)