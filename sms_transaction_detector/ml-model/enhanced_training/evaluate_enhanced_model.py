import spacy
import json
import pandas as pd
from collections import defaultdict

def evaluate_model(model_path, test_data):
    # Load the model
    nlp = spacy.load(model_path)
    
    # Metrics tracking
    total_entities = defaultdict(int)
    correct_entities = defaultdict(int)
    extracted_entities = defaultdict(int)
    
    # Process each test example
    for text, annotations in test_data:
        # Get predicted entities
        doc = nlp(text)
        pred_entities = [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]
        
        # Get true entities
        true_entities = [(start, end, label) for start, end, label in annotations['entities']]
        
        # Track counts for each entity type
        for start, end, label in true_entities:
            total_entities[label] += 1
        
        for start, end, label in pred_entities:
            extracted_entities[label] += 1
            if (start, end, label) in true_entities:
                correct_entities[label] += 1
    
    # Calculate metrics
    results = {}
    all_labels = set(list(total_entities.keys()) + list(extracted_entities.keys()))
    
    for label in all_labels:
        precision = correct_entities[label] / extracted_entities[label] if extracted_entities[label] > 0 else 0
        recall = correct_entities[label] / total_entities[label] if total_entities[label] > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        results[label] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'support': total_entities[label],
            'correct': correct_entities[label],
            'extracted': extracted_entities[label]
        }
    
    # Overall metrics
    total = sum(total_entities.values())
    correct = sum(correct_entities.values())
    extracted = sum(extracted_entities.values())
    
    overall_precision = correct / extracted if extracted > 0 else 0
    overall_recall = correct / total if total > 0 else 0
    overall_f1 = 2 * overall_precision * overall_recall / (overall_precision + overall_recall) if (overall_precision + overall_recall) > 0 else 0
    
    results['overall'] = {
        'precision': overall_precision,
        'recall': overall_recall,
        'f1': overall_f1,
        'support': total,
        'correct': correct,
        'extracted': extracted
    }
    
    return results

# Test data - let's use the test cases from our existing test file
# In a real scenario, you would use a separate test set that wasn't used for training
test_data = [
    # Credit alert format
    [
        "Credit Alert! Rs.10,000.00 credited to HDFC Bank A/c xx2228 on 03-04-25 from VPA john123@okaxis",
        {
            "entities": [
                [14, 26, "AMOUNT"],
                [33, 42, "BANK"],
                [43, 54, "ACCOUNT_TO"],
                [58, 66, "DATE"],
                [72, 89, "PAYEE"],
                [0, 13, "TRANSACTION_TYPE"]
            ]
        }
    ],
    # Debit format
    [
        "Rs.545 spent on HDFC Bank Card xx8155 at FLIPKART on 2025-04-02",
        {
            "entities": [
                [0, 6, "AMOUNT"],
                [16, 25, "BANK"],
                [26, 40, "ACCOUNT_FROM"],
                [44, 52, "PAYEE"],
                [56, 66, "DATE"],
                [7, 12, "TRANSACTION_TYPE"]
            ]
        }
    ],
    # Alert payment format
    [
        "ALERT: Rs.500.00 sent via UPI app to Ram's vegetable stall (UPI ID: ram.veg@okicici).",
        {
            "entities": [
                [7, 16, "AMOUNT"],
                [17, 21, "TRANSACTION_TYPE"],
                [35, 53, "PAYEE"],
                [63, 78, "ACCOUNT_TO"]
            ]
        }
    ],
    # Standard bank format 
    [
        "HDFC Bank: INR 899.00 debited for Mobile Bill Payment to Airtel from XX7654.",
        {
            "entities": [
                [0, 9, "BANK"],
                [11, 21, "AMOUNT"],
                [22, 29, "TRANSACTION_TYPE"],
                [34, 55, "PAYEE"],
                [59, 65, "ACCOUNT_FROM"]
            ]
        }
    ],
    # UPI format
    [
        "UPI transaction successful! Rs.500.00 sent to john.doe@okicici from XX5678 on 05-04-2025.",
        {
            "entities": [
                [26, 35, "AMOUNT"],
                [36, 40, "TRANSACTION_TYPE"],
                [44, 60, "PAYEE"],
                [66, 72, "ACCOUNT_FROM"],
                [76, 86, "DATE"]
            ]
        }
    ],
    # New test case: Complex date format
    [
        "Payment of Rs.1,500.00 to Dr. John for Medical Consultation on 5th April, 2025 completed.",
        {
            "entities": [
                [12, 23, "AMOUNT"],
                [27, 60, "PAYEE"],
                [64, 79, "DATE"],
                [0, 7, "TRANSACTION_TYPE"]
            ]
        }
    ],
    # New test case: Account_to with different format
    [
        "Transferred INR 25,000 to ICICI Account ending with 4567 on 05.04.2025",
        {
            "entities": [
                [12, 22, "AMOUNT"],
                [26, 31, "BANK"],
                [32, 52, "ACCOUNT_TO"],
                [56, 66, "DATE"],
                [0, 11, "TRANSACTION_TYPE"]
            ]
        }
    ],
    # New test case: Multi-word bank name
    [
        "Axis Bank Ltd has deducted Rs.899 from your account (XX5678) for DTH subscription on 04/04/2025",
        {
            "entities": [
                [0, 13, "BANK"],
                [27, 33, "AMOUNT"],
                [44, 58, "ACCOUNT_FROM"],
                [63, 79, "PAYEE"],
                [83, 93, "DATE"],
                [14, 26, "TRANSACTION_TYPE"]
            ]
        }
    ]
]

# Evaluate both models
print("Evaluating the original model...")
original_model_path = "/workspaces/ParsePay/sms_transaction_detector/ml-model/ner_model"
original_results = evaluate_model(original_model_path, test_data)

print("Evaluating the enhanced model...")
enhanced_model_path = "/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/best_model"
enhanced_results = evaluate_model(enhanced_model_path, test_data)

# Create a comparison DataFrame
def create_comparison_df(original_results, enhanced_results):
    data = []
    
    all_labels = set(original_results.keys()).union(set(enhanced_results.keys()))
    
    for label in all_labels:
        if label in original_results and label in enhanced_results:
            orig = original_results[label]
            enh = enhanced_results[label]
            
            row = {
                'Entity': label,
                'Original F1': f"{orig['f1']:.1%}",
                'Enhanced F1': f"{enh['f1']:.1%}",
                'Change': f"{(enh['f1'] - orig['f1']):.1%}",
                'Original Precision': f"{orig['precision']:.1%}",
                'Enhanced Precision': f"{enh['precision']:.1%}",
                'Original Recall': f"{orig['recall']:.1%}",
                'Enhanced Recall': f"{enh['recall']:.1%}",
                'Support': orig['support']
            }
            data.append(row)
    
    df = pd.DataFrame(data)
    return df

# Display comparison
comparison = create_comparison_df(original_results, enhanced_results)
print("\nModel Performance Comparison:\n")
print(comparison.sort_values(by='Entity'))

# Display overall metrics
print("\nOverall Performance:\n")
print(f"Original Model - F1: {original_results['overall']['f1']:.1%}, Precision: {original_results['overall']['precision']:.1%}, Recall: {original_results['overall']['recall']:.1%}")
print(f"Enhanced Model - F1: {enhanced_results['overall']['f1']:.1%}, Precision: {enhanced_results['overall']['precision']:.1%}, Recall: {enhanced_results['overall']['recall']:.1%}")
print(f"Improvement - F1: {(enhanced_results['overall']['f1'] - original_results['overall']['f1']):.1%}, Precision: {(enhanced_results['overall']['precision'] - original_results['overall']['precision']):.1%}, Recall: {(enhanced_results['overall']['recall'] - original_results['overall']['recall']):.1%}")