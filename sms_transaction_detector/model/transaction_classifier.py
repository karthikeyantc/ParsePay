import os
import joblib

# Load the trained model
MODEL_FILE = os.path.join(os.path.dirname(__file__), "transaction_model.pkl")

# Load the model only once when the module is imported
model = joblib.load(MODEL_FILE)

def is_financial_transaction(message: str) -> bool:
    """
    Predicts whether the given SMS message is a financial transaction.
    Returns True if it is, else False.
    """
    prediction = model.predict([message])
    return prediction[0] == 1
