from ..models.analysis import AnalysisHistory
from ..models.user import User
from ..extensions import db
from .utils import get_dummy_analysis, simulate_prediction, create_analysis_visualization
import numpy as np

def analyze_water_quality(lat, lon, user_id, analysis_type='detect'):
    # Generate analysis data
    bounds, mask = get_dummy_analysis(lat, lon)
    
    if analysis_type == 'predict':
        mask = simulate_prediction(mask)
    
    # Create visualization
    filename = create_analysis_visualization(mask, analysis_type)
    
    # Calculate metrics
    coverage = round(np.count_nonzero(mask) / mask.size * 100, 2)
    severity = 'low'
    if coverage > 30:
        severity = 'high'
    elif coverage > 15:
        severity = 'medium'
    
    # Save to history
    history = AnalysisHistory(
        user_id=user_id,
        analysis_type=analysis_type,
        latitude=lat,
        longitude=lon,
        image_url=f'/static/analysis/{filename}',
        result_data={
            'coverage': coverage,
            'severity': severity,
            'bounds': bounds
        }
    )
    db.session.add(history)
    db.session.commit()
    
    return {
        'id': history.id,
        'image_url': history.image_url,
        'coverage': coverage,
        'severity': severity,
        'bounds': bounds,
        'created_at': history.created_at.isoformat()
    }