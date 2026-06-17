import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

print("Loading dataset...")

df = pd.read_csv("college_data.csv")

print("Encoding branch...")

df["branch"] = df["branch"].astype("category").cat.codes

X = df[["branch", "cutoff"]]
y = df["college"]

print("Training model...")

model = RandomForestClassifier()
model.fit(X, y)

joblib.dump(model, "college_model.pkl")

print("Model trained successfully")