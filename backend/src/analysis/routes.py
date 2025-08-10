from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from .services import analyze_water_quality
from werkzeug.exceptions import BadRequest

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/detect', methods=['GET'])
@login_required
def detect_algae():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
    except (TypeError, ValueError):
        raise BadRequest('Invalid coordinates')
    
    result = analyze_water_quality(lat, lon, current_user.id, 'detect')
    return jsonify({
        'success': True,
        'result': result
    })

@analysis_bp.route('/predict', methods=['GET'])
@login_required
def predict_algae():
    try:
        lat = float(request.args.get('lat'))
        lon = float(request.args.get('lon'))
    except (TypeError, ValueError):
        raise BadRequest('Invalid coordinates')
    
    result = analyze_water_quality(lat, lon, current_user.id, 'predict')
    return jsonify({
        'success': True,
        'result': result
    })

@analysis_bp.route('/history', methods=['GET'])
@login_required
def get_history():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    
    query = AnalysisHistory.query.filter_by(user_id=current_user.id)
    pagination = query.order_by(AnalysisHistory.created_at.desc()).paginate(page=page, per_page=per_page)
    
    history = [{
        'id': item.id,
        'type': item.analysis_type,
        'latitude': item.latitude,
        'longitude': item.longitude,
        'image_url': item.image_url,
        'result': item.result_data,
        'created_at': item.created_at.isoformat()
    } for item in pagination.items]
    
    return jsonify({
        'success': True,
        'history': history,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })