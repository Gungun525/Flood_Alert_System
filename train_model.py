# train_model.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

# Simulate data
np.random.seed(42)
df = pd.DataFrame({
    'rainfall': np.random.uniform(0, 300, 500),
    'river_level': np.random.uniform(1, 10, 500),
    'humidity': np.random.uniform(40, 100, 500),
    'temperature': np.random.uniform(15, 45, 500)
})
df['flood_occurred'] = ((df['rainfall'] > 30) & (df['river_level'] > 5)).astype(int)

# Train model
X = df[['rainfall', 'river_level', 'humidity', 'temperature']]
y = df['flood_occurred']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save
joblib.dump(model, 'flood_model.pkl')
print("✅ Model saved as flood_model.pkl")

