import spacy

# Load the trained model
nlp = spacy.load('ml-model/ner_model')

def extract_entities(text):
    """Extract entities from the given text using the trained NER model."""
    doc = nlp(text)
    entities = {}
    for ent in doc.ents:
        entities[ent.label_] = ent.text
    return entities

# Example usage
if __name__ == '__main__':
    sample_sms = "Your account has been credited with $500 on 2025-04-05."
    print(extract_entities(sample_sms))