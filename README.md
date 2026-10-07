# CareSync: AI-Driven Stroke Risk Prediction & Triage

CareSync is a clinical web application designed to evaluate patient stroke risk using machine learning. It accepts patient clinical metrics, computes real-time stroke risk probability, displays a qualitative risk classification (**Low risk** / **High risk** using a 50% cutoff), and renders automated clinical triage guidance.

---

## 🧠 Final Machine Learning Metrics (Seminar Presentation Slides)

Trained on the **Kaggle Healthcare Stroke Prediction Dataset** (`fedesoriano/stroke-prediction-dataset`) using a hybrid **SMOTE + NCR (Synthetic Minority Over-sampling Technique + Neighbourhood Cleaning Rule)** resampled Logistic Regression pipeline.

| Metric | Score | Clinical Context |
| :--- | :--- | :--- |
| **Recall (Positive Class)** | **`0.8000` (80.0%)** | Correctly identifies 80% of true stroke cases for early triage. |
| **Precision** | **`0.1351` (13.5%)** | Calibrated for high-sensitivity medical screening. |
| **ROC-AUC Score** | **`0.8387` (83.9%)** | Strong discrimination ability across risk thresholds. |
| **Overall Accuracy** | **`74.2%`** | Evaluated on holdout test set (1,022 patients). |

### Confusion Matrix
```text
               Predicted Negative (0)    Predicted Positive (1)
Actual Negative (0)         716                       256
Actual Positive (1)          10                        40
```

---

## 🏗️ Architecture Overview

- **Frontend**: HTML5, Vanilla CSS, JS (JustGage interactive gauge meter & risk badges).
- **Backend API**: Python 3.11 + Flask (`app.py`), served in production via **Gunicorn** (4 worker processes).
- **ML Engine**: `scikit-learn` & `imbalanced-learn` SMOTE + NCR pipeline exported as `stroke_model.pkl`.
- **Session Logging**: Asynchronous, fail-safe S3 logging (`boto3` background thread) to track non-identifying telemetry.
- **Containerization**: Docker (`python:3.11-slim` base image).
- **CI/CD**: GitHub Actions building & pushing to Amazon ECR, deploying to AWS EC2 via `deploy.sh`.
- **HTTPS**: Nginx reverse proxy + Certbot (Let's Encrypt SSL/TLS certificate).

---

## 🚀 Local Setup & Docker Commands

### Local Running (Development)
```bash
# Install dependencies
pip install -r requirements.txt

# Train model (optional, pre-trained pickle included)
python train.py

# Run Flask server locally
python app.py
```
Access dashboard at `http://localhost:5000/home.html`.

### Docker Build & Run (Production Container)
```bash
# 1. Build Docker Image
docker build -t caresync-stroke-app .

# 2. Run Docker Container
docker run -d -p 5000:5000 --name caresync-container caresync-stroke-app
```
Test prediction via `curl`:
```bash
curl -X POST http://localhost:5000/api/predict \
  -H "Content-Type: application/json" \
  -d '{"gender":"Female","age":79,"hypertension":1,"heart_disease":0,"ever_married":"Yes","work_type":"Self-employed","Residence_type":"Rural","avg_glucose_level":174.12,"bmi":24.0,"smoking_status":"never smoked"}'
```

---

## ☁️ AWS Deployment Setup

### 1. ECR Setup
```bash
aws ecr create-repository --repository-name caresync-stroke-app --region us-east-1
```

### 2. S3 Bucket Setup
```bash
aws s3api create-bucket --bucket caresync-session-logs --region us-east-1
```

### 3. GitHub Secrets Configured
- `AWS_ACCESS_KEY_ID`: IAM user key with ECR/S3 access.
- `AWS_SECRET_ACCESS_KEY`: IAM user secret key.
- `AWS_REGION`: `us-east-1`
- `EC2_HOST`: Elastic IP of EC2 instance.
- `EC2_USERNAME`: `ubuntu` or `ec2-user`
- `EC2_SSH_KEY`: Private key for SSH deployment.
- `S3_LOG_BUCKET`: `caresync-session-logs`

---

## ⚠️ Medical Disclaimer
*This tool is for educational/demonstration use only and does not replace consultation with a physician.*
