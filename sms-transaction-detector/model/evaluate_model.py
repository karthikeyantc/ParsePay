import json
import os
import joblib
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

# Path to training data JSON
DATA_FILE = os.path.join(os.path.dirname(__file__), "training_data.json")

# Load training data
with open(DATA_FILE, "r") as f:
    data = json.load(f)

texts = [item["text"] for item in data]
labels = [item["label"] for item in data]

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    texts, labels, test_size=0.25, random_state=42
)

# Create model pipeline
model = Pipeline([
    ('vectorizer', TfidfVectorizer(min_df=1, max_df=0.9, sublinear_tf=True)),
    ('classifier', MultinomialNB())
])

# Train model
model.fit(X_train, y_train)

# Make predictions
y_pred = model.predict(X_test)

# Print evaluation metrics
print("=" * 50)
print("Model Evaluation")
print("=" * 50)
print(f"Accuracy: {accuracy_score(y_test, y_pred):.4f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["Non-Financial", "Financial"]))

# Cross-validation
cv_scores = cross_val_score(model, texts, labels, cv=5)
print(f"\nCross-Validation Scores: {cv_scores}")
print(f"Mean CV Score: {cv_scores.mean():.4f}")

# Print confusion matrix
conf_matrix = confusion_matrix(y_test, y_pred)
print("\nConfusion Matrix:")
print(conf_matrix)
print("\nWhere:")
print("[True Negative, False Positive]")
print("[False Negative, True Positive]")