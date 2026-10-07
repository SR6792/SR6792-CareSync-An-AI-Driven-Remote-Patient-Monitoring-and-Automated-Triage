import sys
import json
import os
import pickle
import pandas as pd

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

def main():
    try:
        data = DEFAULT_VALUES.copy()

        if len(sys.argv) > 1:
            first_arg = sys.argv[1].strip()
            if first_arg.startswith('{'):
                parsed = json.loads(first_arg)
                for k in FEATURE_COLUMNS:
                    if k in parsed and parsed[k] is not None and str(parsed[k]).strip() != "":
                        data[k] = float(parsed[k])
            elif len(sys.argv) >= 14:
                for idx, col in enumerate(FEATURE_COLUMNS):
                    data[col] = float(sys.argv[idx + 1])
            elif len(sys.argv) == 3: # Legacy support (age, bmi/chol)
                data['age'] = float(sys.argv[1])
                data['chol'] = float(sys.argv[2])
        
        # Load model file (prefer heart_model.pkl, fallback to stroke_model.pkl)
        model_file = 'heart_model.pkl' if os.path.exists('heart_model.pkl') else 'stroke_model.pkl'
        with open(model_file, 'rb') as f:
            model = pickle.load(f)

        input_df = pd.DataFrame([[data[col] for col in FEATURE_COLUMNS]], columns=FEATURE_COLUMNS)

        # Predict probability of stroke (class 1)
        probability = model.predict_proba(input_df)[0][1]
        risk_percentage = round(probability * 100, 2)

        # Determine qualitative risk-group label using 50% cutoff
        if risk_percentage >= 50.0:
            risk_level = "High risk"
            recommendation = "Urgent clinical evaluation & lifestyle/medical stroke triage recommended."
        else:
            risk_level = "Low risk"
            recommendation = "Stroke risk parameters are within healthy limits. Maintain healthy lifestyle."

        disclaimer = "This tool is for educational/demonstration use only and does not replace consultation with a physician."

        result = {
            "inputs": data,
            "stroke_risk_percentage": risk_percentage,
            "probability_label": f"{risk_percentage}% stroke risk",
            "risk_level": risk_level,
            "recommendation": recommendation,
            "disclaimer": disclaimer
        }
        print(json.dumps(result))

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
