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

# ─────────────────────────────────────────────────────────────────
# MODEL REGISTRY — loads all 3 trained models at startup
# ─────────────────────────────────────────────────────────────────
MODEL_FILES = {
    'lr':  ('model_lr.pkl',  'Logistic Regression'),
    'rf':  ('model_rf.pkl',  'Random Forest'),
    'xgb': ('model_xgb.pkl', 'XGBoost'),
}

DEFAULT_MODEL_KEY = 'lr'

_models = {}

def load_models():
    global _models
    for key, (filepath, label) in MODEL_FILES.items():
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                _models[key] = pickle.load(f)
            print(f"[CareSync] Loaded model '{label}' from {filepath}")
        else:
            print(f"[CareSync] Warning: {filepath} not found — run train.py first.")

    # Fallback: try legacy pickle names
    if not _models:
        for legacy in ['stroke_model.pkl', 'heart_model.pkl']:
            if os.path.exists(legacy):
                with open(legacy, 'rb') as f:
                    _models['lr'] = pickle.load(f)
                print(f"[CareSync] Loaded legacy model from {legacy}")
                break

load_models()

# ─────────────────────────────────────────────────────────────────
# DEFAULT INPUT VALUES
# ─────────────────────────────────────────────────────────────────
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

# ─────────────────────────────────────────────────────────────────
# S3 ASYNC LOGGING (fail-safe)
# ─────────────────────────────────────────────────────────────────
def log_prediction_to_s3(log_payload):
    def async_upload():
        bucket_name = os.environ.get('S3_LOG_BUCKET')
        if not bucket_name:
            return
        try:
            import boto3
            s3_client = boto3.client('s3', region_name=os.environ.get('AWS_REGION', 'us-east-1'))
            date_str = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            log_filename = f"logs/{date_str}/prediction_{uuid.uuid4().hex[:8]}.json"
            s3_client.put_object(
                Bucket=bucket_name, Key=log_filename,
                Body=json.dumps(log_payload), ContentType='application/json'
            )
        except Exception as err:
            print(f"[S3 Logging Non-Fatal Alert]: {err}")

    thread = threading.Thread(target=async_upload)
    thread.daemon = True
    thread.start()


# ─────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('.', 'home.html')

@app.route('/home.html')
def home():
    return send_from_directory('.', 'home.html')


@app.route('/api/models', methods=['GET'])
def get_models():
    """Returns available model keys, names, and comparison metrics."""
    available = {
        key: {'name': MODEL_FILES[key][1], 'loaded': key in _models}
        for key in MODEL_FILES
    }

    # Attach metrics from model_comparison.json if it exists
    metrics = {}
    if os.path.exists('model_comparison.json'):
        with open('model_comparison.json') as f:
            metrics = json.load(f)

    for key in available:
        if key in metrics:
            available[key]['metrics'] = metrics[key]

    return jsonify({'models': available, 'default': DEFAULT_MODEL_KEY}), 200


@app.route('/api/predict', methods=['POST'])
def predict():
    try:
        payload = request.get_json(silent=True) or request.form or {}

        # Which model to use (from dropdown)
        model_key = str(payload.get('model', DEFAULT_MODEL_KEY)).strip().lower()
        if model_key not in _models:
            model_key = DEFAULT_MODEL_KEY
        if model_key not in _models:
            return jsonify({'error': 'No trained model found. Run train.py first.'}), 503

        model = _models[model_key]
        model_name = MODEL_FILES.get(model_key, ('', 'Unknown'))[1]

        # Build input data
        data = DEFAULT_VALUES.copy()
        for k in DEFAULT_VALUES:
            if k in payload and payload[k] is not None and str(payload[k]).strip() != '':
                if k in ['age', 'avg_glucose_level', 'bmi']:
                    data[k] = float(payload[k])
                elif k in ['hypertension', 'heart_disease']:
                    data[k] = int(payload[k])
                else:
                    data[k] = str(payload[k])

        input_df = pd.DataFrame([data])
        probability = model.predict_proba(input_df)[0][1]
        risk_percentage = round(probability * 100, 2)

        if risk_percentage >= 50.0:
            risk_level = 'High risk'
            recommendation = 'Urgent clinical evaluation & stroke triage recommended.'
        else:
            risk_level = 'Low risk'
            recommendation = 'Stroke risk parameters are within healthy limits. Maintain healthy lifestyle.'

        response_data = {
            'inputs': data,
            'model_used': model_name,
            'model_key': model_key,
            'stroke_risk_percentage': risk_percentage,
            'probability_label': f'{risk_percentage}% stroke risk',
            'risk_level': risk_level,
            'recommendation': recommendation,
            'disclaimer': 'This tool is for educational/demonstration use only and does not replace consultation with a physician.'
        }

        log_prediction_to_s3({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'model_key': model_key,
            'inputs': data,
            'stroke_risk_percentage': risk_percentage,
            'risk_level': risk_level
        })

        return jsonify(response_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/<path:path>')
def static_files(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return send_from_directory('.', 'home.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
