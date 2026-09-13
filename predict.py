import sys
import json
import pickle
import pandas as pd

def main():
    try:
        age = float(sys.argv[1])
        bmi = float(sys.argv[2])

        with open('stroke_model.pkl', 'rb') as f:
            model = pickle.load(f)

        # Structure as DataFrame with exact feature names
        input_data = pd.DataFrame([[age, bmi]], columns=['age', 'bmi'])

        # Predict probability for class 1 (stroke)
        probability = model.predict_proba(input_data)[0][1]
        risk_percentage = round(probability * 100, 2)

        result = {
            "age": age,
            "bmi": bmi,
            "stroke_risk_percentage": risk_percentage
        }
        print(json.dumps(result))

    except Exception as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()