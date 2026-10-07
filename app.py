import os
import json
import uuid
import pickle
import threading
from datetime import datetime, timezone
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['DEBUG'] = False

DEFAULT_VALUES = {
    'gender': 'Male',
    'age': 55.0,
    'hypertension': 0,
    'heart_disease': 0,
    'ever_married': 'Yes',
    'work_type': 'Private',
    'Residence_type': 'Urban',
    'avg_glucose_level': 105.0,
    'bmi': 28.0,
    'smoking_status': 'never smoked'
}

# Helper to load trained ML model
def load_model():
    model_file = 'stroke_model.pkl' if os.path.exists('stroke_model.pkl') else 'heart_model.pkl'
    if os.path.exists(model_file):
        with open(model_file, 'rb') as f:
            return pickle.load(f)
    return None

model = load_model()

# Task 4: Fail-safe, Asynchronous S3 Session Logging
def log_prediction_to_s3(log_payload):
    def async_upload():
        bucket_name = os.environ.get('S3_LOG_BUCKET')
        if not bucket_name:
            return  # S3 logging disabled if bucket name is not configured

        try:
            import boto3
            s3_client = boto3.client(
                's3',
                region_name=os.environ.get('AWS_REGION', 'us-east-1')
            )
            
            date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            log_filename = f"logs/{date_str}/prediction_{uuid.uuid4().hex[:8]}.json"
            
            s3_client.put_object(
                Bucket=bucket_name,
                Key=log_filename,
                Body=json.dumps(log_payload),
                ContentType='application/json'
            )
        except Exception as err:
            # Fail-safe: Log error to stdout without interrupting application response
            print(f"[S3 Logging Non-Fatal Alert]: {err}")

    # Launch background thread for non-blocking execution
    thread = threading.Thread(target=async_upload)
    thread.daemon = True
    thread.start()

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
        for k in DEFAULT_VALUES:
            if k in payload and payload[k] is not None and str(payload[k]).strip() != "":
                if k in ['age', 'avg_glucose_level', 'bmi']:
                    data[k] = float(payload[k])
                elif k in ['hypertension', 'heart_disease']:
                    data[k] = int(payload[k])
                else:
                    data[k] = str(payload[k])

        input_df = pd.DataFrame([data])

        if model is not None:
            probability = model.predict_proba(input_df)[0][1]
        else:
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

        # Task 4: Trigger asynchronous S3 session logging (non-identifying)
        s3_log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "inputs": data,
            "stroke_risk_percentage": risk_percentage,
            "risk_level": risk_level
        }
        log_prediction_to_s3(s3_log_data)

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
