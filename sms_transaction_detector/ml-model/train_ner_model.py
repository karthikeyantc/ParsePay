import spacy
from spacy.tokens import DocBin
import json
import os
from spacy.training import Example

# Load training data
with open('/workspaces/ParsePay/sms_transaction_detector/ml-model/training_data.json', 'r') as f:
    training_data = json.load(f)

print(f"Loaded {len(training_data)} training examples")

# Initialize spaCy model with our custom entity types
nlp = spacy.blank('en')
ner = nlp.add_pipe("ner")
ner.add_label("AMOUNT")
ner.add_label("DATE")
ner.add_label("PAYEE")
ner.add_label("BANK")
ner.add_label("TRANSACTION_TYPE")
ner.add_label("ACCOUNT_FROM")
ner.add_label("ACCOUNT_TO")

print("Added entity labels to NER pipeline")

# Prepare training data
examples = []
db = DocBin()
for text, annotations in training_data:
    doc = nlp.make_doc(text)
    ents = []
    for start, end, label in annotations['entities']:
        span = doc.char_span(start, end, label=label, alignment_mode='contract')
        if span is not None:
            ents.append(span)
    doc.ents = ents
    db.add(doc)

# Ensure the directory for saving the processed training data exists
os.makedirs('/workspaces/ParsePay/sms_transaction_detector/ml-model', exist_ok=True)

# Save training data in spaCy format
db.to_disk('/workspaces/ParsePay/sms_transaction_detector/ml-model/training_data.spacy')

# Deserialize the DocBin object for training
training_docs = list(db.get_docs(nlp.vocab))

# Convert training_docs to Example objects
examples = [Example.from_dict(doc, {"entities": [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]}) for doc in training_docs]

print(f"Prepared {len(examples)} examples for training")

# Train the model
nlp.begin_training()
for epoch in range(30):  # Increased epochs for better training
    losses = {}
    for example in examples:
        nlp.update([example], drop=0.2, losses=losses)
    print(f"Epoch {epoch+1}, Losses: {losses}")

# Ensure the directory for saving the trained model exists
os.makedirs('/workspaces/ParsePay/sms_transaction_detector/ml-model/ner_model', exist_ok=True)

# Save the trained model
nlp.to_disk('/workspaces/ParsePay/sms_transaction_detector/ml-model/ner_model')
print("Model trained and saved successfully")

# Function to extract transaction details from SMS using the trained model
def extract_transaction_details(sms_text):
    # Load the trained NER model
    loaded_nlp = spacy.load('/workspaces/ParsePay/sms_transaction_detector/ml-model/ner_model')
    
    # Process the SMS text
    doc = loaded_nlp(sms_text)
    
    # Initialize results dictionary with default structure
    result = {
        "bank": {"value": None, "confidence": 0.0},
        "amount": {"value": None, "confidence": 0.0},
        "date": {"value": None, "confidence": 0.0},
        "payee": {"value": None, "confidence": 0.0},
        "transaction_type": {"value": None, "confidence": 0.0},
        "account_from": {"value": None, "confidence": 0.0},
        "account_to": {"value": None, "confidence": 0.0}
    }
    
    # Extract entities from the processed document
    for ent in doc.ents:
        entity_label = ent.label_.lower()
        if entity_label in result:
            result[entity_label]["value"] = ent.text
            # Fixed: Use a fixed confidence value since custom confidence not implemented
            result[entity_label]["confidence"] = 0.85
    
    # Only apply fallback rules if entities weren't found by the ML model
    if any(result[key]["value"] is None for key in result):
        apply_fallback_rules(sms_text, result)
    
    return result

# Fallback rules function to be called only when ML model fails to extract certain entities
def apply_fallback_rules(sms_text, result):
    import re
    
    # Amount extraction - if not found by ML model
    if not result["amount"]["value"]:
        amount_patterns = [
            r'Rs\.?\s*([0-9,]+\.?[0-9]*)', 
            r'INR\s*([0-9,]+\.?[0-9]*)',
            r'Rs\s*([0-9,]+\.?[0-9]*)',
            r'debited with\s*Rs\.?\s*([0-9,]+\.?[0-9]*)',
            r'([0-9,]+\.?[0-9]*)\s*(?:Rs\.?|INR)',
            r'of\s*Rs\.?\s*([0-9,]+\.?[0-9]*)',
            r'for\s*Rs\.?\s*([0-9,]+\.?[0-9]*)'
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, sms_text, re.IGNORECASE)
            if match:
                result["amount"]["value"] = match.group(0).strip()
                result["amount"]["confidence"] = 0.7
                break
    
    # Date extraction - if not found by ML model
    if not result["date"]["value"]:
        date_patterns = [
            r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})',  # DD-MM-YYYY, MM/DD/YYYY
            r'(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})',    # YYYY-MM-DD
            r'(\d{1,2}[-/\.][A-Za-z]{3,4}[-/\.]\d{2,4})',  # DD-MMM-YYYY
            r'on\s+(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})',
            r'on\s+(\d{1,2}[-/\.][A-Za-z]{3,4}[-/\.]\d{2,4})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, sms_text, re.IGNORECASE)
            if match:
                if match.group(0).startswith('on '):
                    result["date"]["value"] = match.group(1).strip()
                else:
                    result["date"]["value"] = match.group(0).strip()
                result["date"]["confidence"] = 0.65
                break
    
    # Bank extraction - if not found by ML model
    if not result["bank"]["value"]:
        banks = {
            "HDFC": ["HDFC", "HDFC Bank"],
            "SBI": ["SBI", "State Bank", "State Bank of India"],
            "ICICI": ["ICICI", "ICICI Bank"],
            "Axis": ["Axis", "Axis Bank"],
            "IDFC FIRST": ["IDFC", "IDFC FIRST", "IDFC Bank"],
            "Yes Bank": ["Yes Bank"],
            "Kotak": ["Kotak", "Kotak Bank", "Kotak Mahindra"],
            "PNB": ["PNB", "Punjab National Bank"],
            "Bank of Baroda": ["BOB", "Bank of Baroda"]
        }
        
        for bank, keywords in banks.items():
            for keyword in keywords:
                if keyword in sms_text:
                    result["bank"]["value"] = bank
                    result["bank"]["confidence"] = 0.75
                    break
            if result["bank"]["value"]:
                break
    
    # Transaction type detection - if not found by ML model
    if not result["transaction_type"]["value"]:
        transaction_patterns = {
            "CREDIT": [r'credited', r'received', r'credit', r'salary', r'deposited', r'added'],
            "DEBIT": [r'debited', r'spent', r'paid', r'payment', r'purchase', r'debit', r'withdrawn'],
            "TRANSFER": [r'transferred', r'transfer', r'sent', r'IMPS', r'NEFT', r'RTGS', r'UPI']
        }
        
        for txn_type, patterns in transaction_patterns.items():
            for pattern in patterns:
                if re.search(pattern, sms_text, re.IGNORECASE):
                    result["transaction_type"]["value"] = txn_type
                    result["transaction_type"]["confidence"] = 0.7
                    break
            if result["transaction_type"]["value"]:
                break
    
    # Payee extraction - if not found by ML model
    if not result["payee"]["value"]:
        payee_patterns = [
            r'to\s+([A-Za-z0-9\s\.\-\']+?)\s+(?:on|via|ref|from|a\/c)',
            r'at\s+([A-Z0-9\s\*\/\.\-]+?)(?:\s+on|\.|$)',
            r'for\s+([A-Za-z0-9\s\.\-\']+?)(?:\s+on|\.|$)',
            r'paid\s+to\s+([A-Za-z0-9\s\.\-\']+?)(?:\s+|\.|\(|$)',
            r'transferred\s+to\s+([A-Za-z0-9\s\.\-\']+?)(?:\s+|\.|\(|$)',
            r'credited\s+from\s+([A-Za-z0-9\s\.\-\']+?)(?:\s+|\.|\(|$)'
        ]
        
        for pattern in payee_patterns:
            match = re.search(pattern, sms_text, re.IGNORECASE)
            if match:
                result["payee"]["value"] = match.group(1).strip()
                result["payee"]["confidence"] = 0.6
                break
        
        # UPI ID pattern
        if not result["payee"]["value"] and "@" in sms_text:
            upi_pattern = r'([a-zA-Z0-9\.\-\_]+@[a-z]+)'
            match = re.search(upi_pattern, sms_text)
            if match:
                result["payee"]["value"] = match.group(1).strip()
                result["payee"]["confidence"] = 0.55
    
    # Account extraction - if not found by ML model
    account_patterns = [
        # From account patterns
        (r'from\s+(?:a\/c|account|acc\.?|ac)(?:\s+no\.?)?\s*[:\.#]?\s*([\dXx\*]{4,})', "account_from"),
        (r'from\s+(?:a\/c|account|acc\.?|ac)(?:\s+no\.?)?\s*[:\.#]?\s*([Xx\*]+\d{1,4})', "account_from"),
        (r'your\s+(?:a\/c|account|acc\.?|ac)(?:\s+no\.?)?\s*[:\.#]?\s*([\dXx\*]{4,})', "account_from"),
        (r'card\s+[\w\s\.\-\']+?\s*(X+\d+|x+\d+|\*+\d+)', "account_from"),
        
        # To account patterns
        (r'to\s+(?:a\/c|account|acc\.?|ac)(?:\s+no\.?)?\s*[:\.#]?\s*([\dXx\*]{4,})', "account_to"),
        (r'to\s+(?:a\/c|account|acc\.?|ac)(?:\s+no\.?)?\s*[:\.#]?\s*([Xx\*]+\d{1,4})', "account_to"),
        (r'credited\s+to\s+.{1,30}?\s*(?:a\/c|account|acc\.?|ac)(?:\s+no\.?)?\s*[:\.#]?\s*([\dXx\*]{4,})', "account_to")
    ]
    
    for pattern, field in account_patterns:
        if not result[field]["value"]:
            match = re.search(pattern, sms_text, re.IGNORECASE)
            if match:
                result[field]["value"] = match.group(1).strip()
                result[field]["confidence"] = 0.65