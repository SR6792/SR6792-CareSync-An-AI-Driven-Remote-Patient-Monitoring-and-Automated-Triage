import pandas as pd
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

# 1. Dataset
data = {
    'age': [67, 79, 61, 32, 24, 45],
    'bmi': [36, 24, 28, 22, 24, 27],
    'stroke': [1, 1, 1, 0, 0, 0]
}
df = pd.DataFrame(data)

X = df[['age', 'bmi']]
y = df['stroke']

# 2. Pipeline: Scale inputs then apply Logistic Regression
# C=10.0 allows the small dataset to fit stronger weights
pipeline = Pipeline([
    ('scaler', StandardScaler()),
    ('classifier', LogisticRegression(C=10.0))
])

pipeline.fit(X, y)

# 3. Export pipeline to stroke_model.pkl
with open('stroke_model.pkl', 'wb') as f:
    pickle.dump(pipeline, f)

print("Pipeline saved successfully.")