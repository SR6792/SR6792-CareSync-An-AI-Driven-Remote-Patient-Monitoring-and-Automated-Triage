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

def load_model():
    model_file = 'stroke_model.pkl' if os.path.exists('stroke_model.pkl') else 'heart_model.pkl'
    with open(model_file, 'rb') as f:
        return pickle.load(f)

def predict(data, model):
    if not isinstance(data, dict):
        raise ValueError("Prediction input must be a JSON object")

    values = DEFAULT_VALUES.copy()
    for key in DEFAULT_VALUES:
        if key in data and data[key] is not None and str(data[key]).strip() != "":
            values[key] = data[key]

    input_df = pd.DataFrame([values])

    probability = model.predict_proba(input_df)[0][1]
    risk_percentage = round(probability * 100, 2)

    if risk_percentage >= 50.0:
        risk_level = "High risk"
        recommendation = "Urgent clinical evaluation & stroke triage recommended."
    else:
        risk_level = "Low risk"
        recommendation = "Stroke risk parameters are within healthy limits. Maintain healthy lifestyle."

    disclaimer = "This tool is for educational/demonstration use only and does not replace consultation with a physician."

    return {
        "inputs": values,
        "stroke_risk_percentage": risk_percentage,
        "probability_label": f"{risk_percentage}% stroke risk",
        "risk_level": risk_level,
        "recommendation": recommendation,
        "disclaimer": disclaimer
    }

def run_worker():
    model = load_model()
    for line in sys.stdin:
        try:
            result = predict(json.loads(line), model)
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

        print(json.dumps(predict(data, load_model())))
    except Exception as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()

