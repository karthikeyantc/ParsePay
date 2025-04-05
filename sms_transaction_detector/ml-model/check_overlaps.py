import spacy
from spacy.tokens import DocBin
import json
import os
from spacy.training import Example

# Load training data
with open('/workspaces/ParsePay/sms_transaction_detector/ml-model/training_data.json', 'r') as f:
    training_data = json.load(f)

# Initialize spaCy model
nlp = spacy.blank('en')

# Check for overlapping entities in training data
for idx, (text, annotations) in enumerate(training_data):
    doc = nlp.make_doc(text)
    try:
        ents = []
        for start, end, label in sorted(annotations['entities']):
            span = doc.char_span(start, end, label=label, alignment_mode='contract')
            if span is not None:
                ents.append(span)
        doc.ents = ents
    except ValueError as e:
        print(f"Error in example {idx}: {text}")
        print(f"Annotations: {annotations['entities']}")
        print(f"Error: {e}")
        # Exit to allow manual fixing
        exit(1)

print("All examples checked, no overlapping entities found.")
# The rest of the training script would follow here...