# app.py (Advanced Version with Prediction)

from flask import Flask, render_template, jsonify, request
import numpy as np
from PIL import Image
import time
import cv2 # Make sure you have opencv-python installed
import os

app = Flask(__name__)

# --- CONFIGURATION ---
OUTPUT_FOLDER = 'static'

# --- CORE FUNCTIONS ---

def get_dummy_analysis(lat, lon):
    """
    This function simulates finding and processing real data.
    In a real-world scenario, this would involve downloading and analyzing
    a satellite image. Here, we just generate a random pattern.
    """
    # Create a dummy analysis at the user's location
    dummy_bounds = [[lat - 0.5, lon - 0.5], [lat + 0.5, lon + 0.5]]
    dummy_mask_raw = (np.random.rand(256, 256) > 0.9).astype(np.uint8) * 255
    
    return dummy_bounds, dummy_mask_raw

def simulate_prediction(current_mask_raw):
    """
    Simulates a future prediction by making the algae blooms larger (dilation).
    This function is identical to the one from our simple prototype.
    """
    kernel = np.ones((15, 15), np.uint8)
    predicted_mask = cv2.dilate(current_mask_raw, kernel, iterations=1)
    
    # Create a transparent YELLOW image for display
    rgba = np.zeros((predicted_mask.shape[0], predicted_mask.shape[1], 4), dtype=np.uint8)
    rgba[predicted_mask == 255, 0] = 255 # Red channel
    rgba[predicted_mask == 255, 1] = 255 # Green channel (R+G = Yellow)
    rgba[predicted_mask == 255, 3] = 130 # Alpha channel (semi-transparent)
    
    img = Image.fromarray(rgba)
    timestamp = int(time.time())
    output_path = f'{OUTPUT_FOLDER}/predicted_algae_{timestamp}.png'
    img.save(output_path)
    
    return output_path

# --- API ENDPOINTS ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/detect')
def detect_algae():
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'Latitude and Longitude are required.'})
            
        dummy_bounds, dummy_mask_raw = get_dummy_analysis(lat, lon)
        
        # Create transparent RED image for display
        rgba = np.zeros((256, 256, 4), dtype=np.uint8)
        rgba[dummy_mask_raw == 255, 0] = 255 # Red channel
        rgba[dummy_mask_raw == 255, 3] = 150 # Alpha channel

        img = Image.fromarray(rgba)
        timestamp = int(time.time())
        output_path = f'{OUTPUT_FOLDER}/current_algae_{timestamp}.png'
        img.save(output_path)

        return jsonify({'success': True, 'image_url': output_path, 'bounds': dummy_bounds})
        
    except Exception as e:
        print(f"ERROR in /detect: {e}")
        return jsonify({'success': False, 'error': str(e)})

# --- NEW CODE STARTS HERE ---

@app.route('/predict')
def predict_algae():
    """
    New endpoint for handling prediction requests.
    """
    try:
        lat = request.args.get('lat', type=float)
        lon = request.args.get('lon', type=float)
        if lat is None or lon is None:
            return jsonify({'success': False, 'error': 'Latitude and Longitude are required.'})

        # Step 1: Get the current state of the blooms, just like in /detect
        dummy_bounds, current_mask_raw = get_dummy_analysis(lat, lon)

        # Step 2: Pass the current mask to the simulation function
        predicted_path = simulate_prediction(current_mask_raw)

        # Step 3: Return the new predicted image path and the same bounds
        return jsonify({'success': True, 'image_url': predicted_path, 'bounds': dummy_bounds})

    except Exception as e:
        print(f"ERROR in /predict: {e}")
        return jsonify({'success': False, 'error': str(e)})

# --- NEW CODE ENDS HERE ---

if __name__ == '__main__':
    app.run(debug=True)