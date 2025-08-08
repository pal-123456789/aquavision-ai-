# app.py (Version 2.0)

from flask import Flask, render_template, jsonify, request
import numpy as np
from PIL import Image
import time
import cv2
import os

app = Flask(__name__)

OUTPUT_FOLDER = 'static'
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

def get_dummy_analysis(lat, lon):
    # Simulating a delay to make it feel like a real, heavy computation
    time.sleep(2) 
    
    bounds = [[lat - 0.5, lon - 0.5], [lat + 0.5, lon + 0.5]]
    mask_raw = (np.random.rand(256, 256) > 0.9).astype(np.uint8) * 255
    return bounds, mask_raw

def simulate_prediction(current_mask_raw):
    time.sleep(2) # Simulate prediction time
    kernel = np.ones((15, 15), np.uint8)
    predicted_mask = cv2.dilate(current_mask_raw, kernel, iterations=1)
    return predicted_mask

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/detect')
def detect_algae():
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'Location not provided.'}), 400
            
        bounds, mask_raw = get_dummy_analysis(lat, lon)
        
        rgba = np.zeros((256, 256, 4), dtype=np.uint8)
        rgba[mask_raw == 255, 0] = 255 # Red
        rgba[mask_raw == 255, 3] = 150 # Alpha
        img = Image.fromarray(rgba)
        timestamp = int(time.time())
        output_path = os.path.join(OUTPUT_FOLDER, f'current_algae_{timestamp}.png')
        img.save(output_path)

        return jsonify({'success': True, 'image_url': output_path, 'bounds': bounds})
        
    except Exception as e:
        print(f"ERROR in /detect: {e}")
        return jsonify({'success': False, 'error': 'An internal error occurred.'}), 500

@app.route('/predict')
def predict_algae():
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'Location not provided.'}), 400

        _, current_mask_raw = get_dummy_analysis(lat, lon)
        predicted_mask = simulate_prediction(current_mask_raw)
        
        bounds = [[lat - 0.5, lon - 0.5], [lat + 0.5, lon + 0.5]]
        rgba = np.zeros((256, 256, 4), dtype=np.uint8)
        rgba[predicted_mask == 255, 0] = 255 # Yellow
        rgba[predicted_mask == 255, 1] = 255
        rgba[predicted_mask == 255, 3] = 130 # Alpha
        img = Image.fromarray(rgba)
        timestamp = int(time.time())
        output_path = os.path.join(OUTPUT_FOLDER, f'predicted_algae_{timestamp}.png')
        img.save(output_path)

        return jsonify({'success': True, 'image_url': output_path, 'bounds': bounds})

    except Exception as e:
        print(f"ERROR in /predict: {e}")
        return jsonify({'success': False, 'error': 'An internal error occurred.'}), 500

if __name__ == '__main__':
    app.run(debug=True)