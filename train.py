import os
import pickle
import kagglehub
from kagglehub import KaggleDatasetAdapter

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score, recall_score, confusion_matrix

from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import NeighbourhoodCleaningRule
from imblearn.pipeline import Pipeline as ImbPipeline

def train_model():
    print("=" * 60)
    print(" CareSync ML Pipeline Training: Stroke Risk (SMOTE + NCR)")
    print("=" * 60)

    # 1. Load dataset from Kaggle via kagglehub
    file_path = "heart.csv"
    print("\n[1/4] Loading dataset via kagglehub...")
    df = kagglehub.load_dataset(
        KaggleDatasetAdapter.PANDAS,
        "sonialikhan/heart-attack-analysis-and-prediction-dataset",
        file_path,
    )

    print("First 5 records:", df.head())

    # 2. Extract Features (X) and Target Label (y)
    X = df.drop('output', axis=1)
    y = df['output']
    
    print(f"\nDataset shape: {df.shape} | Target distribution:\n{y.value_counts()}")

    # Train/Test Split for Evaluation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. Build SMOTE + NCR Resampled Classification Pipeline
    print("\n[2/4] Building SMOTE + NCR Resampling Pipeline...")
    pipeline = ImbPipeline([
        ('smote', SMOTE(random_state=42)),
        ('ncr', NeighbourhoodCleaningRule(n_neighbors=3)),
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(C=0.5, class_weight='balanced', random_state=42))
    ])

    # 4. Evaluate Model Performance on Holdout Test Set
    print("\n[3/4] Training model on train set and evaluating on test set...")
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    recall = recall_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_proba)
    cm = confusion_matrix(y_test, y_pred)

    print("\n" + "-" * 40)
    print(" Model Evaluation Summary")
    print("-" * 40)
    print(f" Positive Class Recall: {recall:.4f} (~{recall*100:.1f}%)")
    print(f" ROC-AUC Score        : {roc_auc:.4f} (~{roc_auc*100:.1f}%)")
    print(f"\nConfusion Matrix:\n{cm}")
    print(f"\nDetailed Classification Report:\n{classification_report(y_test, y_pred)}")

    # 5. Fit full dataset and export model artifact
    print("\n[4/4] Retraining pipeline on full dataset & saving model pickles...")
    pipeline.fit(X, y)

    with open('stroke_model.pkl', 'wb') as f:
        pickle.dump(pipeline, f)

    with open('heart_model.pkl', 'wb') as f:
        pickle.dump(pipeline, f)

    print("\n" + "=" * 60)
    print(" Stroke prediction model (SMOTE + NCR) saved successfully!")
    print(" Saved model artifacts: stroke_model.pkl & heart_model.pkl")
    print("=" * 60)

if __name__ == '__main__':
    train_model()
