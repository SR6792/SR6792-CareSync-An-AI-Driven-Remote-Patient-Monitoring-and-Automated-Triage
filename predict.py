import sys
import json
import os
import pickle
import pandas as pd

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

MODEL_FILES = {
    'lr': ('model_lr.pkl', 'Logistic Regression'),
    'rf': ('model_rf.pkl', 'Random Forest'),
    'xgb': ('model_xgb.pkl', 'XGBoost')
}

DEFAULT_MODEL_KEY = 'lr'

def load_models():
    models = {}
    base_dir = os.path.dirname(os.path.abspath(__file__))

    for key, (filename, _) in MODEL_FILES.items():
        model_path = os.path.join(base_dir, filename)
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    models[key] = pickle.load(f)
            except Exception as error:
                raise RuntimeError(
                    f"Could not load {filename}. Check that this Python environment "
                    f"has the project dependencies installed: {error}"
                ) from error

    if not models:
        for legacy in ('stroke_model.pkl', 'heart_model.pkl'):
            model_path = os.path.join(base_dir, legacy)
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    models[DEFAULT_MODEL_KEY] = pickle.load(f)
                break

    if not models:
        raise FileNotFoundError(
            'No trained model found. Run train.py to generate the model files.'
        )

    return models

def predict(data, model, model_key=DEFAULT_MODEL_KEY):
    if not isinstance(data, dict):
        raise ValueError("Prediction input must be a JSON object")

    values = DEFAULT_VALUES.copy()
    for key in DEFAULT_VALUES:
        if key in data and data[key] is not None and str(data[key]).strip() != "":
            values[key] = data[key]

    input_df = pd.DataFrame([values])

    probability = float(model.predict_proba(input_df)[0][1])
    risk_percentage = round(probability * 100, 2)

    if risk_percentage >= 50.0:
        risk_level = "High risk"
        recommendation = "Urgent clinical evaluation & stroke triage recommended."
    else:
        risk_level = "Low risk"
        recommendation = "Stroke risk parameters are within healthy limits. Maintain healthy lifestyle."

    disclaimer = "This tool is for educational/demonstration use only and does not replace consultation with a physician."
    model_name = MODEL_FILES.get(model_key, ('', 'Legacy model'))[1]

    return {
        "inputs": values,
        "model_used": model_name,
        "model_key": model_key,
        "stroke_risk_percentage": risk_percentage,
        "probability_label": f"{risk_percentage}% stroke risk",
        "risk_level": risk_level,
        "recommendation": recommendation,
        "disclaimer": disclaimer
    }

def run_worker():
    models = load_models()
    for line in sys.stdin:
        try:
            data = json.loads(line)
            model_key = str(data.get('model', DEFAULT_MODEL_KEY)).strip().lower()
            if model_key not in models:
                available = ', '.join(models)
                raise ValueError(
                    f"Model '{model_key}' is unavailable. Available models: {available}"
                )
            result = predict(data, models[model_key], model_key)
        except Exception as error:
            result = {"error": str(error)}
        print(json.dumps(result), flush=True)

def main():
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "--worker":
            run_worker()
            return

        data = {}
        if len(sys.argv) > 1:
            first_arg = sys.argv[1].strip()
            if first_arg.startswith('{'):
                data = json.loads(first_arg)

        models = load_models()
        model_key = str(data.get('model', DEFAULT_MODEL_KEY)).strip().lower()
        if model_key not in models:
            raise ValueError(f"Model '{model_key}' is unavailable.")
        print(json.dumps(predict(data, models[model_key], model_key)))
    except Exception as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

