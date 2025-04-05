import spacy
import sys
import os

# Load the trained NER model
try:
    print("Loading model from:", '/workspaces/ParsePay/sms_transaction_detector/ml-model/ner_model')
    nlp = spacy.load('/workspaces/ParsePay/sms_transaction_detector/ml-model/ner_model')
    
    # Test a simple SMS
    test_sms = "Sent Rs.73.00 From HDFC Bank A/C x2228 To Marvel On 04/04/25 Ref 509482752071"
    
    # Process the SMS
    doc = nlp(test_sms)
    
    # Print all recognized entities
    print("\nEntities recognized in:", test_sms)
    if len(doc.ents) == 0:
        print("No entities found!")
    else:
        for ent in doc.ents:
            print(f"  - {ent.text} ({ent.label_})")
    
    # Print token information
    print("\nToken details:")
    for token in doc:
        print(f"  - {token.text} (POS: {token.pos_}, TAG: {token.tag_})")
        
except Exception as e:
    print("Error:", str(e))