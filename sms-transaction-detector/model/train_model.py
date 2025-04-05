import json
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Path to training data JSON
DATA_FILE = os.path.join(os.path.dirname(__file__), "training_data.json")
MODEL_FILE = os.path.join(os.path.dirname(__file__), "transaction_model.pkl")

# Load training data
with open(DATA_FILE, "r") as f:
    data = json.load(f)

texts = [item["text"] for item in data]
labels = [item["label"] for item in data]

# Create model pipeline with TfidfVectorizer instead of CountVectorizer
model = Pipeline([
    ('vectorizer', TfidfVectorizer(min_df=1, max_df=0.9, sublinear_tf=True)),
    ('classifier', MultinomialNB())
])

# Train model
model.fit(texts, labels)

# Save model
joblib.dump(model, MODEL_FILE)

print(f"✅ Model trained and saved to {MODEL_FILE}")
