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

def main():
    try:
        data = DEFAULT_VALUES.copy()

        if len(sys.argv) > 1:
            first_arg = sys.argv[1].strip()
            if first_arg.startswith('{'):
                parsed = json.loads(first_arg)
                for k in DEFAULT_VALUES:
                    if k in parsed and parsed[k] is not None and str(parsed[k]).strip() != "":
                        data[k] = parsed[k]

        # Load trained stroke model
        model_file = 'stroke_model.pkl' if os.path.exists('stroke_model.pkl') else 'heart_model.pkl'
        with open(model_file, 'rb') as f:
            model = pickle.load(f)

        input_df = pd.DataFrame([data])

        # Predict probability of stroke (class 1)
        probability = model.predict_proba(input_df)[0][1]
        risk_percentage = round(probability * 100, 2)

        # Determine qualitative risk-group label using 50% cutoff
        if risk_percentage >= 50.0:
            risk_level = "High risk"
            recommendation = "Urgent clinical evaluation & stroke triage recommended."
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

