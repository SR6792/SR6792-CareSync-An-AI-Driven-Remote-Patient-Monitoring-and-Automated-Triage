import os
import json
import pickle
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['DEBUG'] = False

FEATURE_COLUMNS = [
    'age', 'sex', 'cp', 'trtbps', 'chol', 'fbs', 
    'restecg', 'thalachh', 'exng', 'oldpeak', 'slp', 'caa', 'thall'
]

DEFAULT_VALUES = {
    'age': 50.0,
    'sex': 1.0,
    'cp': 0.0,
    'trtbps': 120.0,
    'chol': 200.0,
    'fbs': 0.0,
    'restecg': 0.0,
    'thalachh': 150.0,
    'exng': 0.0,
    'oldpeak': 0.0,
    'slp': 1.0,
    'caa': 0.0,
    'thall': 2.0
}

# Helper to load trained ML model
def load_model():
    model_file = 'stroke_model.pkl' if os.path.exists('stroke_model.pkl') else 'heart_model.pkl'
    if os.path.exists(model_file):
        with open(model_file, 'rb') as f:
            return pickle.load(f)
    return None

model = load_model()

@app.route('/')
def index():
    return send_from_directory('.', 'home.html')

@app.route('/home.html')
def home():
    return send_from_directory('.', 'home.html')

@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        global model
        if model is None:
            model = load_model()

        payload = request.get_json(silent=True) or request.form or {}
        
        data = DEFAULT_VALUES.copy()
        for k in FEATURE_COLUMNS:
            if k in payload and payload[k] is not None and str(payload[k]).strip() != "":
                data[k] = float(payload[k])

        input_df = pd.DataFrame([[data[col] for col in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)

        if model is not None:
            probability = model.predict_proba(input_df)[0][1]
        else:
            # Fallback estimation if model pickle not loaded
            probability = 0.5

        risk_percentage = round(probability * 100, 2)

        # Qualitative risk-group label: 50% cutoff threshold
        if risk_percentage >= 50.0:
            risk_level = "High risk"
            recommendation = "Urgent clinical evaluation & stroke triage recommended."
        else:
            risk_level = "Low risk"
            recommendation = "Stroke risk parameters are within healthy limits. Maintain healthy lifestyle."

        disclaimer = "This tool is for educational/demonstration use only and does not replace consultation with a physician."

        response_data = {
            "inputs": data,
            "stroke_risk_percentage": risk_percentage,
            "probability_label": f"{risk_percentage}% stroke risk",
            "risk_level": risk_level,
            "recommendation": recommendation,
            "disclaimer": disclaimer
        }
        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return send_from_directory('.', 'home.html')

if __name__ == '__main__':
    # Debug mode is explicitly turned OFF for production safety
    app.run(host='0.0.0.0', port=5000, debug=False)
