import spacy
from spacy.tokens import DocBin
import json
import os
from spacy.training import Example
import random

# Load original training data
with open('/workspaces/ParsePay/sms_transaction_detector/ml-model/training_data.json', 'r') as f:
    original_training_data = json.load(f)

# Load additional training data
with open('/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/additional_training_data.json', 'r') as f:
    additional_training_data = json.load(f)

# Combine training data
training_data = original_training_data + additional_training_data

# Shuffle the combined data for better training
random.shuffle(training_data)

print(f"Loaded {len(original_training_data)} original examples")
print(f"Loaded {len(additional_training_data)} additional examples")
print(f"Combined into {len(training_data)} total training examples")

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
os.makedirs('/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training', exist_ok=True)

# Save combined training data in spaCy format
db.to_disk('/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/combined_training_data.spacy')

# Deserialize the DocBin object for training
training_docs = list(db.get_docs(nlp.vocab))

# Convert training_docs to Example objects
examples = [Example.from_dict(doc, {"entities": [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]}) for doc in training_docs]

print(f"Prepared {len(examples)} examples for training")

# Train the model with improved parameters
nlp.begin_training()
losses = {}
best_loss = float('inf')

# More epochs and better dropout rate for improved learning
n_epochs = 50
dropout_rate = 0.25

print(f"Starting training for {n_epochs} epochs with dropout rate {dropout_rate}")

for epoch in range(n_epochs):
    # Shuffle examples each epoch for better generalization
    random.shuffle(examples)
    
    # Track losses
    epoch_losses = {}
    for example in examples:
        nlp.update([example], drop=dropout_rate, losses=epoch_losses)
    
    # Calculate average loss for this epoch
    avg_loss = sum(epoch_losses.values()) / len(epoch_losses) if epoch_losses else 0
    
    # Save best model
    if avg_loss < best_loss:
        best_loss = avg_loss
        # Save the best model
        os.makedirs('/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/best_model', exist_ok=True)
        nlp.to_disk('/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/best_model')
        print(f"Epoch {epoch+1}/{n_epochs}, Loss: {avg_loss:.4f} - New best model saved!")
    else:
        print(f"Epoch {epoch+1}/{n_epochs}, Loss: {avg_loss:.4f}")

# Save the final model too
os.makedirs('/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/final_model', exist_ok=True)
nlp.to_disk('/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/final_model')

print("Enhanced model training complete!")
print(f"Best model saved at: /workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/best_model")
print(f"Final model saved at: /workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/final_model")