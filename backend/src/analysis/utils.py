import cv2
import numpy as np
from PIL import Image
import time
import os
from datetime import datetime
from flask import current_app

def get_dummy_analysis(lat, lon):
    """Generate realistic water analysis data"""
    bounds = [[lat - 0.1, lon - 0.1], [lat + 0.1, lon + 0.1]]
    
    # Create base pattern
    x = np.linspace(-1, 1, 512)
    y = np.linspace(-1, 1, 512)
    xx, yy = np.meshgrid(x, y)
    dist = np.sqrt(xx**2 + yy**2)
    
    # Create base bloom pattern
    base = np.exp(-dist*3) * 255
    
    # Add random variation
    noise = np.random.normal(0, 0.2, (512, 512))
    pattern = np.clip(base * (1 + noise), 0, 255)
    
    # Create binary mask
    threshold = 0.85 * np.max(pattern)
    mask_raw = (pattern > threshold).astype(np.uint8) * 255
    
    return bounds, mask_raw

def simulate_prediction(current_mask):
    """Simulate bloom expansion over time"""
    kernel_size = 15
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    predicted = cv2.dilate(current_mask, kernel, iterations=1)
    
    # Add random new spots
    spots = np.random.random((512, 512)) > 0.995
    predicted[spots] = 255
    
    return predicted

def create_analysis_visualization(mask, analysis_type):
    """Create visualization image from analysis mask"""
    if analysis_type == 'predict':
        color = [255, 165, 0]  # Orange for prediction
    else:
        color = [255, 0, 0]  # Red for detection
    
    # Create visualization
    rgba = np.zeros((512, 512, 4), dtype=np.uint8)
    rgba[mask == 255, 0:3] = color
    rgba[mask == 255, 3] = 150
    
    img = Image.fromarray(rgba)
    timestamp = int(time.time())
    filename = f'{analysis_type}_{timestamp}.png'
    output_path = os.path.join(current_app.config['ANALYSIS_FOLDER'], filename)
    img.save(output_path, optimize=True, quality=85)
    
    return filename