import os
import time
import json
import pickle
import warnings
import pandas as pd
import numpy as np
import kagglehub
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend (no display needed)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, recall_score, precision_score,
    f1_score, roc_auc_score, confusion_matrix, classification_report
)

from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import NeighbourhoodCleaningRule
from imblearn.pipeline import Pipeline as ImbPipeline

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = Trueo
except ImportError:
    XGBOOST_AVAILABLE = False
    print("[WARNING] XGBoost not installed. Run: pip install xgboost")

warnings.filterwarnings('ignore')

os.makedirs('static', exist_ok=True)

# ─────────────────────────────────────────────────────────────────
# 1. LOAD DATASET
# ─────────────────────────────────────────────────────────────────
def load_data():
    print("\n[1/5] Loading Kaggle Stroke Prediction Dataset...")
    path = kagglehub.dataset_download('fedesoriano/stroke-prediction-dataset')
    csv_file = os.path.join(path, 'healthcare-dataset-stroke-data.csv')
    df = pd.read_csv(csv_file)

    # Filter rare 'Other' gender row
    df = df[df['gender'] != 'Other'].copy()

    print(f"    Dataset shape: {df.shape}")
    print(f"    Stroke cases : {df['stroke'].sum()} ({df['stroke'].mean()*100:.2f}%)")
    print(f"    Columns      : {list(df.columns)}")
    return df


# ─────────────────────────────────────────────────────────────────
# 2. PREPROCESSING
# ─────────────────────────────────────────────────────────────────
def build_preprocessor():
    num_cols = ['age', 'avg_glucose_level', 'bmi']
    cat_cols = [
        'gender', 'hypertension', 'heart_disease',
        'ever_married', 'work_type', 'Residence_type', 'smoking_status'
    ]
    preprocessor = ColumnTransformer(transformers=[
        ('num', ImbPipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ]), num_cols),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), cat_cols)
    ])
    return preprocessor, num_cols, cat_cols


# ─────────────────────────────────────────────────────────────────
# 3. DEFINE 3 MODEL CONFIGS
# ─────────────────────────────────────────────────────────────────
def get_model_configs():
    configs = {
        'lr': {
            'name': 'Logistic Regression',
            'clf': LogisticRegression(C=0.5, class_weight='balanced', max_iter=1000, random_state=42),
            'pkl': 'model_lr.pkl'
        },
        'rf': {
            'name': 'Random Forest',
            'clf': RandomForestClassifier(
                n_estimators=200, class_weight='balanced',
                max_depth=10, random_state=42, n_jobs=-1
            ),
            'pkl': 'model_rf.pkl'
        },
    }
    if XGBOOST_AVAILABLE:
        configs['xgb'] = {
            'name': 'XGBoost',
            'clf': XGBClassifier(
                n_estimators=200, learning_rate=0.05,
                scale_pos_weight=20, max_depth=4,
                random_state=42, eval_metric='logloss',
                verbosity=0
            ),
            'pkl': 'model_xgb.pkl'
        }
    else:
        print("[WARNING] Skipping XGBoost — not installed.")
    return configs


# ─────────────────────────────────────────────────────────────────
# 4. TRAIN ALL MODELS + COMPARE
# ─────────────────────────────────────────────────────────────────
def train_all_models(df, preprocessor):
    X = df.drop(['id', 'stroke'], axis=1)
    y = df['stroke']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    configs = get_model_configs()
    results = {}

    print("\n[3/5] Training models with SMOTE + NCR resampling...\n")
    print(f"{'Model':<25} {'Train (s)':>9} {'Acc':>7} {'Recall':>8} {'Prec':>8} {'F1':>7} {'AUC':>7}")
    print("-" * 75)

    for key, cfg in configs.items():
        pipeline = ImbPipeline([
            ('prep', preprocessor),
            ('smote', SMOTE(random_state=42)),
            ('ncr', NeighbourhoodCleaningRule(n_neighbors=3)),
            ('clf', cfg['clf'])
        ])

        t_start = time.perf_counter()
        pipeline.fit(X_train, y_train)
        t_train = round(time.perf_counter() - t_start, 3)

        y_pred  = pipeline.predict(X_test)
        y_proba = pipeline.predict_proba(X_test)[:, 1]

        acc   = round(accuracy_score(y_test, y_pred)  * 100, 2)
        rec   = round(recall_score(y_test, y_pred)    * 100, 2)
        prec  = round(precision_score(y_test, y_pred) * 100, 2)
        f1    = round(f1_score(y_test, y_pred)        * 100, 2)
        auc   = round(roc_auc_score(y_test, y_proba)  * 100, 2)
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()

        results[key] = {
            'name': cfg['name'],
            'pkl': cfg['pkl'],
            'train_time_s': t_train,
            'accuracy':    acc,
            'recall':      rec,
            'precision':   prec,
            'f1':          f1,
            'roc_auc':     auc,
            'true_neg':    int(tn),
            'false_pos':   int(fp),
            'false_neg':   int(fn),
            'true_pos':    int(tp)
        }

        print(f"{cfg['name']:<25} {t_train:>9.3f} {acc:>6.1f}% {rec:>7.1f}% {prec:>7.1f}% {f1:>6.1f}% {auc:>6.1f}%")

        # Now retrain on full dataset and save
        pipeline.fit(X, y)
        with open(cfg['pkl'], 'wb') as f:
            pickle.dump(pipeline, f)
        print(f"    → Saved {cfg['pkl']}")

    # Save JSON comparison
    with open('model_comparison.json', 'w') as f:
        json.dump(results, f, indent=2)
    print("\n    → Saved model_comparison.json")

    return results


# ─────────────────────────────────────────────────────────────────
# 5. GENERATE GRAPHS
# ─────────────────────────────────────────────────────────────────
def generate_graphs(results):
    print("\n[4/5] Generating comparison graphs...")

    models  = [v['name'] for v in results.values()]
    keys    = list(results.keys())
    colors  = ['#6366f1', '#10b981', '#f59e0b'][:len(keys)]

    metrics = {
        'Accuracy (%)':       [results[k]['accuracy']    for k in keys],
        'Recall (%)':         [results[k]['recall']      for k in keys],
        'Precision (%)':      [results[k]['precision']   for k in keys],
        'F1 Score (%)':       [results[k]['f1']          for k in keys],
        'ROC-AUC (%)':        [results[k]['roc_auc']     for k in keys],
        'Train Time (sec)':   [results[k]['train_time_s'] for k in keys],
    }

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))
    fig.suptitle('CareSync: Multi-Model Comparison\n(SMOTE + NCR Resampled)', fontsize=14, fontweight='bold', y=1.01)

    axes_flat = axes.flatten()
    for i, (metric_name, values) in enumerate(metrics.items()):
        ax = axes_flat[i]
        bars = ax.bar(models, values, color=colors, edgecolor='white', width=0.5)
        ax.set_title(metric_name, fontsize=11, fontweight='bold')
        ax.set_ylim(0, max(values) * 1.25 if max(values) > 0 else 1)
        ax.set_ylabel(metric_name)
        ax.set_xticks(range(len(models)))
        ax.set_xticklabels(models, rotation=10, ha='right', fontsize=9)
        ax.grid(axis='y', linestyle='--', alpha=0.4)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + max(values) * 0.02,
                f'{val:.1f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold'
            )

    plt.tight_layout()
    out_path = os.path.join('static', 'comparison.png')
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"    → Saved {out_path}")

    # Also save individual confusion matrix chart
    fig2, axes2 = plt.subplots(1, len(keys), figsize=(5 * len(keys), 4))
    if len(keys) == 1:
        axes2 = [axes2]
    for i, k in enumerate(keys):
        r = results[k]
        cm = np.array([[r['true_neg'], r['false_pos']], [r['false_neg'], r['true_pos']]])
        im = axes2[i].imshow(cm, cmap='Blues')
        axes2[i].set_title(r['name'], fontweight='bold')
        axes2[i].set_xticks([0, 1]); axes2[i].set_xticklabels(['Pred No Stroke', 'Pred Stroke'])
        axes2[i].set_yticks([0, 1]); axes2[i].set_yticklabels(['Actual No Stroke', 'Actual Stroke'])
        for row in range(2):
            for col in range(2):
                axes2[i].text(col, row, str(cm[row, col]),
                              ha='center', va='center', fontsize=14,
                              color='white' if cm[row, col] > cm.max() / 2 else 'black')
        plt.colorbar(im, ax=axes2[i])
    plt.suptitle('Confusion Matrices (Test Set)', fontweight='bold')
    plt.tight_layout()
    cm_path = os.path.join('static', 'confusion_matrices.png')
    plt.savefig(cm_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"    → Saved {cm_path}")


# ─────────────────────────────────────────────────────────────────
# 6. MAIN
# ─────────────────────────────────────────────────────────────────
def train_all():
    print("=" * 65)
    print("  CareSync: Multi-Model Training Pipeline")
    print("  Models: Logistic Regression | Random Forest | XGBoost")
    print("  Resampling: SMOTE + Neighbourhood Cleaning Rule (NCR)")
    print("=" * 65)

    df = load_data()

    print("\n[2/5] Building preprocessing pipeline...")
    preprocessor, num_cols, cat_cols = build_preprocessor()
    print(f"    Numerical features : {num_cols}")
    print(f"    Categorical features: {cat_cols}")

    results = train_all_models(df, preprocessor)
    generate_graphs(results)

    print("\n[5/5] Summary")
    print("=" * 65)
    best_recall = max(results, key=lambda k: results[k]['recall'])
    best_auc    = max(results, key=lambda k: results[k]['roc_auc'])
    fastest     = min(results, key=lambda k: results[k]['train_time_s'])

    print(f"  Best recall    : {results[best_recall]['name']} ({results[best_recall]['recall']:.1f}%)")
    print(f"  Best ROC-AUC   : {results[best_auc]['name']} ({results[best_auc]['roc_auc']:.1f}%)")
    print(f"  Fastest train  : {results[fastest]['name']} ({results[fastest]['train_time_s']:.3f}s)")
    print("\n  Saved models   :", [v['pkl'] for v in results.values()])
    print("  Comparison JSON: model_comparison.json")
    print("  Graphs         : static/comparison.png | static/confusion_matrices.png")
    print("=" * 65)


if __name__ == '__main__':
    train_all()
