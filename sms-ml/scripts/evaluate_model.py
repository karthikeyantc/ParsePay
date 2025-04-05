import os
import pandas as pd
import pickle
from sklearn.metrics import classification_report
from test_cases import (
    simple_test_messages,
    complex_test_messages,
    bank_test_messages,
    date_test_messages,
    bank_inference_test_messages,
    non_financial_messages
)

# Placeholder for loading rule-based outputs
def load_rule_based_outputs(data_path):
    """Load outputs from the rule-based system."""
    # Replace with actual logic to load rule-based outputs
    return pd.DataFrame({"text": ["Sample SMS 1", "Sample SMS 2"], "rule_based_label": ["transaction", "non-transaction"]})

# Placeholder for loading model outputs
def load_model_outputs(model, vectorizer, data):
    """Generate outputs from the trained model."""
    X_vec = vectorizer.transform(data["text"])
    predictions = model.predict(X_vec)
    data["model_label"] = predictions
    return data

# Load the trained model and vectorizer
def load_model(model_path, vectorizer_path):
    """Load the trained model and vectorizer from disk."""
    with open(model_path, 'rb') as model_file:
        model = pickle.load(model_file)
    with open(vectorizer_path, 'rb') as vectorizer_file:
        vectorizer = pickle.load(vectorizer_file)
    return model, vectorizer

# Placeholder for evaluation
def evaluate_against_rule_based(data):
    """Evaluate the model's performance against the rule-based system."""
    print("Comparison with Rule-Based System:")
    print(classification_report(data["rule_based_label"], data["model_label"]))

# Function to test the model on predefined test cases
def test_model_on_cases(model, vectorizer):
    """Test the model on predefined test cases."""
    test_categories = {
        "Simple Test Messages": simple_test_messages,
        "Complex Test Messages": complex_test_messages,
        "Bank Test Messages": bank_test_messages,
        "Date Test Messages": date_test_messages,
        "Bank Inference Test Messages": bank_inference_test_messages,
        "Non-Financial Messages": non_financial_messages,
    }

    for category, messages in test_categories.items():
        print(f"\nCategory: {category}")
        for message in messages:
            vectorized_message = vectorizer.transform([message])
            prediction = model.predict(vectorized_message)[0]
            print(f"Message: {message}\nPrediction: {prediction}\n")

if __name__ == "__main__":
    # Define paths
    data_path = os.path.join("..", "data", "sms_data.csv")
    model_path = os.path.join("..", "models", "sms_model.pkl")
    vectorizer_path = os.path.join("..", "models", "sms_vectorizer.pkl")

    # Load rule-based outputs
    rule_based_data = load_rule_based_outputs(data_path)

    # Load the trained model and vectorizer
    model, vectorizer = load_model(model_path, vectorizer_path)

    # Generate model outputs
    model_data = load_model_outputs(model, vectorizer, rule_based_data)

    # Evaluate against rule-based system
    evaluate_against_rule_based(model_data)

    # Test the model on predefined test cases
    test_model_on_cases(model, vectorizer)