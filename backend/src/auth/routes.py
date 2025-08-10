from flask import Blueprint, request, jsonify
from .services import register_user, login_user, send_password_reset, reset_password
from .schemas import PasswordResetRequestSchema, PasswordResetSchema
from werkzeug.exceptions import BadRequest, Unauthorized

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        user = register_user(data)
        return jsonify({
            'success': True,
            'message': 'Registration successful',
            'user': user
        }), 201
    except BadRequest as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        user = login_user(data)
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'user': user
        })
    except (BadRequest, Unauthorized) as e:
        return jsonify({'success': False, 'error': str(e)}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.get_json()
        schema = PasswordResetRequestSchema(**data)
        send_password_reset(schema.email)
        return jsonify({
            'success': True,
            'message': 'If an account exists with that email, a reset link has been sent'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@auth_bp.route('/reset-password', methods=['POST'])
def reset_password_route():
    try:
        data = request.get_json()
        schema = PasswordResetSchema(**data)
        user = reset_password(schema.token, schema.new_password)
        return jsonify({
            'success': True,
            'message': 'Password reset successful',
            'user_id': user.id
        })
    except BadRequest as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': 'Internal server error'}), 500