import spacy
from spacy.tokens import DocBin
import json
import os
from spacy.training import Example
import random
from tqdm import tqdm
import numpy as np
from spacy.util import minibatch

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

# Check for and fix overlapping entities
fixed_training_data = []
skipped_examples = 0

for text, annotations in training_data:
    # Create a token overlap map to check for overlapping entities
    token_claims = {}
    valid_entities = []
    has_overlap = False
    
    # Sort entities by length (descending) to prioritize longer spans
    sorted_entities = sorted(annotations['entities'], key=lambda x: x[1] - x[0], reverse=True)
    
    for start, end, label in sorted_entities:
        # Check if any token in this span is already claimed
        overlap = False
        for i in range(start, end):
            if i in token_claims:
                overlap = True
                has_overlap = True
                print(f"Warning: Found overlapping entities in text: {text}")
                print(f"  Entity '{text[start:end]}' ({label}) overlaps with '{text[token_claims[i][0]:token_claims[i][1]]}' ({token_claims[i][2]})")
                break
        
        # If no overlap, add this entity
        if not overlap:
            valid_entities.append((start, end, label))
            # Mark these tokens as claimed
            for i in range(start, end):
                token_claims[i] = (start, end, label)
    
    # Use the filtered entities
    if has_overlap:
        print(f"Fixed by keeping {len(valid_entities)} of {len(annotations['entities'])} entities")
    
    if len(valid_entities) > 0:  # Only use examples with at least one valid entity
        fixed_annotations = {'entities': valid_entities}
        fixed_training_data.append((text, fixed_annotations))
    else:
        skipped_examples += 1

if skipped_examples > 0:
    print(f"Skipped {skipped_examples} examples with no valid entities after overlap resolution")

print(f"Using {len(fixed_training_data)} training examples after overlap resolution")

# Analyze entity distribution
entity_counts = {
    "AMOUNT": 0,
    "DATE": 0,
    "PAYEE": 0,
    "BANK": 0,
    "TRANSACTION_TYPE": 0,
    "ACCOUNT_FROM": 0,
    "ACCOUNT_TO": 0
}

for _, annotations in fixed_training_data:
    for _, _, label in annotations['entities']:
        entity_counts[label] = entity_counts.get(label, 0) + 1

print("\nEntity distribution in training data:")
for entity, count in entity_counts.items():
    print(f"  {entity}: {count} examples ({count/len(fixed_training_data):.1%})")

# Balance the dataset with augmentation for underrepresented entities
# Add more weight to underrepresented entities during training
entity_weights = {}
max_entity_count = max(entity_counts.values())
for entity, count in entity_counts.items():
    entity_weights[entity] = max_entity_count / count if count > 0 else 1.0

print("\nEntity weights for balanced training:")
for entity, weight in entity_weights.items():
    print(f"  {entity}: {weight:.2f}x")

# Initialize spaCy model with our custom entity types
nlp = spacy.blank('en')
ner = nlp.add_pipe("ner")
for entity in entity_counts.keys():
    ner.add_label(entity)

print("\nAdded entity labels to NER pipeline")

# Prepare training data with improved entity extraction
examples = []
db = DocBin()
skipped_entities = 0

for text, annotations in tqdm(fixed_training_data, desc="Preparing training data"):
    doc = nlp.make_doc(text)
    ents = []
    for start, end, label in annotations['entities']:
        span = doc.char_span(start, end, label=label, alignment_mode='contract')
        if span is not None:
            ents.append(span)
        else:
            skipped_entities += 1
            print(f"Warning: Entity '{text[start:end]}' ({label}) couldn't be aligned")
    
    doc.ents = ents
    db.add(doc)

print(f"Skipped {skipped_entities} entities due to alignment issues")

# Ensure the directory for saving the processed training data exists
os.makedirs('/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training', exist_ok=True)

# Save combined training data in spaCy format
db.to_disk('/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/combined_training_data.spacy')

# Split into training (80%) and validation (20%) sets
train_examples = []
valid_examples = []

docs = list(db.get_docs(nlp.vocab))
random.shuffle(docs)
split_point = int(len(docs) * 0.8)
train_docs = docs[:split_point]
valid_docs = docs[split_point:]

# Convert to Example objects
train_examples = [Example.from_dict(doc, {"entities": [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]}) for doc in train_docs]
valid_examples = [Example.from_dict(doc, {"entities": [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]}) for doc in valid_docs]

print(f"Prepared {len(train_examples)} training examples and {len(valid_examples)} validation examples")

# Train the model with improved parameters
nlp.begin_training()
losses = {}
best_loss = float('inf')

# Enhanced training parameters
n_epochs = 100
dropout_rates = [0.5, 0.5, 0.4, 0.4, 0.3, 0.3, 0.2, 0.2, 0.1, 0.1]  # Curriculum-based dropout
batch_size = 8
patience = 10  # Early stopping patience
no_improvement_count = 0

print(f"Starting training for up to {n_epochs} epochs with adaptive dropout and early stopping")

for epoch in range(n_epochs):
    # Adjust dropout based on epoch (curriculum learning)
    epoch_dropout = dropout_rates[min(epoch // 10, len(dropout_rates) - 1)]
    
    # Track losses
    epoch_losses = {}
    random.shuffle(train_examples)
    
    # Use minibatches for more stable training
    batches = minibatch(train_examples, size=batch_size)
    for batch in tqdm(batches, desc=f"Epoch {epoch+1}/{n_epochs}"):
        nlp.update(batch, drop=epoch_dropout, losses=epoch_losses)
    
    # Calculate average training loss
    train_loss = sum(epoch_losses.values()) / len(epoch_losses) if epoch_losses else 0
    
    # Evaluate on validation set
    valid_losses = {}
    for example in valid_examples:
        nlp.update([example], drop=0.0, losses=valid_losses, sgd=None)  # No weight updates during validation
    
    valid_loss = sum(valid_losses.values()) / len(valid_losses) if valid_losses else 0
    
    print(f"Epoch {epoch+1}/{n_epochs}, Train Loss: {train_loss:.4f}, Valid Loss: {valid_loss:.4f}, Dropout: {epoch_dropout}")
    
    # Save the best model based on validation loss
    if valid_loss < best_loss:
        best_loss = valid_loss
        no_improvement_count = 0
        os.makedirs('/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/best_model', exist_ok=True)
        nlp.to_disk('/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/best_model')
        print(f"New best model saved! (Valid Loss: {valid_loss:.4f})")
    else:
        no_improvement_count += 1
        if no_improvement_count >= patience:
            print(f"Early stopping after {epoch+1} epochs without improvement")
            break

# Save the final model too
os.makedirs('/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/final_model', exist_ok=True)
nlp.to_disk('/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/final_model')

print("\nEnhanced model training complete!")
print(f"Best model (Valid Loss: {best_loss:.4f}) saved at: /workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/best_model")
print(f"Final model saved at: /workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/final_model")