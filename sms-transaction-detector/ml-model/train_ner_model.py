import spacy
from spacy.tokens import DocBin
import json

# Load training data
with open('ml-model/training_data.json', 'r') as f:
    training_data = json.load(f)

# Initialize spaCy model
nlp = spacy.blank('en')

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

# Save training data in spaCy format
db.to_disk('ml-model/training_data.spacy')

# Train the model
nlp.begin_training()
for epoch in range(10):
    for doc in db:
        nlp.update([doc])

# Save the trained model
nlp.to_disk('ml-model/ner_model')