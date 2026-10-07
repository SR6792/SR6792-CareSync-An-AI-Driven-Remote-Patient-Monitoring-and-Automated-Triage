import os
import pickle
import pandas as pd
import numpy as np
import kagglehub

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score, recall_score, precision_score, confusion_matrix

from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import NeighbourhoodCleaningRule
from imblearn.pipeline import Pipeline as ImbPipeline

def train_model():
    print("=" * 60)
    print(" CareSync ML Pipeline Training: Kaggle Stroke Prediction Dataset")
    print(" SMOTE + NCR Resampled Logistic Regression Model")
    print("=" * 60)

    # 1. Download & Load Kaggle Stroke Prediction Dataset
    print("\n[1/4] Loading real Kaggle Stroke Dataset (fedesoriano/stroke-prediction-dataset)...")
    path = kagglehub.dataset_download('fedesoriano/stroke-prediction-dataset')
    csv_file = os.path.join(path, 'healthcare-dataset-stroke-data.csv')
    df = pd.read_csv(csv_file)

    # Filter out rare 'Other' gender row
    df = df[df['gender'] != 'Other'].copy()

    print("\nFirst 5 records:")
    print(df.head())

    # 2. Separate Features (X) and Target (y)
    X = df.drop(['id', 'stroke'], axis=1)
    y = df['stroke']

    print(f"\nDataset shape: {df.shape} | Target distribution:\n{y.value_counts()}")

    # Define numerical and categorical columns
    num_cols = ['age', 'avg_glucose_level', 'bmi']
    cat_cols = ['gender', 'hypertension', 'heart_disease', 'ever_married', 'work_type', 'Residence_type', 'smoking_status']

    # Preprocessing Pipeline
    preprocessor = ColumnTransformer(transformers=[
        ('num', ImbPipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ]), num_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols)
    ])

    # 3. Split dataset for evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 4. Build SMOTE + NCR Resampling Pipeline
    print("\n[2/4] Building SMOTE + NCR Resampling Pipeline...")
    pipeline = ImbPipeline([
        ('prep', preprocessor),
        ('smote', SMOTE(random_state=42)),
        ('ncr', NeighbourhoodCleaningRule(n_neighbors=3)),
        ('clf', LogisticRegression(C=0.5, class_weight='balanced', max_iter=1000, random_state=42))
    ])

    # 5. Train & Evaluate
    print("\n[3/4] Training model on train set and evaluating on test set...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    rec = recall_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)

    print("\n" + "-" * 50)
    print(" FINAL METRICS SUMMARY (Real Stroke Training Run)")
    print("-" * 50)
    print(f" Recall (Positive Class) : {rec:.4f} (~{rec*100:.1f}%)")
    print(f" Precision              : {prec:.4f} (~{prec*100:.1f}%)")
    print(f" ROC-AUC Score          : {auc:.4f} (~{auc*100:.1f}%)")
    print(f"\nConfusion Matrix:\n{cm}")
    print(f"\nDetailed Classification Report:\n{classification_report(y_test, y_pred)}")

    # 6. Fit full dataset and save pickles
    print("\n[4/4] Retraining pipeline on full dataset & saving model pickles...")
    pipeline.fit(X, y)

    with open('stroke_model.pkl', 'wb') as f:
        pickle.dump(pipeline, f)

    with open('heart_model.pkl', 'wb') as f:
        pickle.dump(pipeline, f)

    print("\n" + "=" * 60)
    print(" Real Stroke Prediction Model (SMOTE + NCR) saved successfully!")
    print(" Saved model artifacts: stroke_model.pkl & heart_model.pkl")
    print("=" * 60)

if __name__ == '__main__':
    train_model()

