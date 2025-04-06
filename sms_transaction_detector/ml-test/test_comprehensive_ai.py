import sys
import os
import importlib.util
from datetime import datetime
import json
import colorama
from colorama import Fore, Style
import spacy
import unittest
import pandas as pd
from tabulate import tabulate
import argparse

# Add the parent directory to sys.path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Direct import with proper path handling
fallback_rules_path = os.path.join(parent_dir, "ml-model", "fallback_rules.py")
spec = importlib.util.spec_from_file_location("fallback_rules", fallback_rules_path)
fallback_rules = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fallback_rules)
apply_fallback_rules = fallback_rules.apply_fallback_rules

# Initialize colorama
colorama.init()

# Parse command line arguments to choose model
parser = argparse.ArgumentParser(description='Test SMS transaction detection models')
parser.add_argument('--model', choices=['original', 'enhanced'], default='enhanced',
                    help='Choose which model to test (original or enhanced)')
args = parser.parse_args()

# Set model path based on command line argument
if args.model == 'enhanced':
    MODEL_PATH = '/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/best_model'
    print(f"{Fore.GREEN}Using enhanced model from: {MODEL_PATH}{Style.RESET_ALL}")
else:
    MODEL_PATH = '/workspaces/ParsePay/sms_transaction_detector/ml-model/ner_model'
    print(f"{Fore.YELLOW}Using original model from: {MODEL_PATH}{Style.RESET_ALL}")

# Function to extract transaction details with detection source tracking
def extract_transaction_details(sms_text):
    # Load the trained NER model
    try:
        loaded_nlp = spacy.load(MODEL_PATH)
        
        # Process the SMS text
        doc = loaded_nlp(sms_text)
        
        # Initialize results dictionary with default structure
        result = {
            "bank": {"value": None, "confidence": 0.0, "source": "none"},
            "amount": {"value": None, "confidence": 0.0, "source": "none"},
            "date": {"value": None, "confidence": 0.0, "source": "none"},
            "payee": {"value": None, "confidence": 0.0, "source": "none"},
            "transaction_type": {"value": None, "confidence": 0.0, "source": "none"},
            "account_from": {"value": None, "confidence": 0.0, "source": "none"},
            "account_to": {"value": None, "confidence": 0.0, "source": "none"}
        }
        
        # Track which fields are found by the ML model
        ml_found = set()
        
        # Extract entities from the processed document
        for ent in doc.ents:
            entity_label = ent.label_.lower()
            if entity_label in result:
                result[entity_label]["value"] = ent.text
                result[entity_label]["confidence"] = 0.85
                result[entity_label]["source"] = "ml"
                ml_found.add(entity_label)
        
        # Apply fallback rules if necessary
        # Store the original state before applying fallback rules
        pre_fallback_state = {k: v["value"] for k, v in result.items()}
        
        # Only apply fallback rules for fields not found by ML
        if any(result[key]["value"] is None for key in result):
            apply_fallback_rules(sms_text, result)
            
            # Mark which fields were found by fallback rules
            for field in result:
                if field not in ml_found and result[field]["value"] is not None:
                    result[field]["source"] = "fallback"
        
        return result
    except Exception as e:
        print(f"Error loading model: {e}")
        print("Please ensure the model is trained before running tests.")
        sys.exit(1)

# Define test categories
simple_test_messages = [
    "Sent Rs.73.00 From HDFC Bank A/C x2228 To Marvel On 04/04/25 Ref 509482752071",
    "Rs.652 spent on HDFC Bank Card x1135 at PAY*Flipkart Internet on 2025-03-25:06:43:19",
    "Credit Alert! Rs.10.00 credited to HDFC Bank A/c xx2228 on 03-04-25 from VPA one97735@icici",
]

complex_test_messages = [
    "Dear Customer, Your Acct XX5678 is debited with Rs.1,23,456.78 on 05.04.2025 for Flipkart order #FLP87654321 (UPI Ref: 123456789012). Avl Bal: Rs.987654.32",
    "ALERT: INR 42,599.00 debited from a/c XX3487 on 01-Apr-25 at AMAZON.IN/BILL. Avl bal: INR 15,736.88. Dispute? Call 1800-425-3800 within 7 days.",
    "SBI: Rs.13750.00 transferred to Mrs. Sharmila J (A/c xxxxxxxx5432) on 04-04-2025 from A/c xxxxxxxx9876 using SBI YONO. Ref # YBT123456789.",
    "IDFC FIRST Bank: Your salary of Rs.87,500.00 has been credited to your account XX9876 on 04/04/2025. Subject: APR-25 SALARY. Balance: Rs.1,12,453.28",
]

# Add more test categories
upi_test_messages = [
    "UPI transaction successful! Rs.500.00 sent to john.doe@okicici from XX5678 on 05-04-2025.",
    "Payment of Rs.1,200 to sam.smith@ybl completed via UPI ID Reference: UPI/123456789.",
    "SBI Alert: Rs.245.00 debited from account XX1234 to merchant.payment@okaxis via UPI.",
    "ALERT: Transaction of INR 350.00 to coffee.shop@paytm is successful. UPI Ref: 20250405112233.",
]

service_payment_messages = [
    "Thank you for paying Rs.1,250.00 towards your Electricity Bill from your ICICI Bank a/c XX5432.",
    "HDFC Bank: INR 899.00 debited for Mobile Bill Payment to Airtel from XX7654.",
    "SBI Alert: Rs.450.00 paid for DTH Recharge - Tata Sky from your account XX3456.",
    "Payment of Rs.2,199.00 towards Broadband Bill - Jio Fiber is complete. Ref: BILL12345.",
]

# Function to format confidence level with color
def format_confidence(confidence):
    if confidence >= 0.8:
        return f"{Fore.GREEN}{confidence:.2f}{Style.RESET_ALL}"
    elif confidence >= 0.6:
        return f"{Fore.YELLOW}{confidence:.2f}{Style.RESET_ALL}"
    else:
        return f"{Fore.RED}{confidence:.2f}{Style.RESET_ALL}"

# Function to format entity value with color and source
def format_entity(value, confidence, source='none'):
    if value is None:
        return f"{Fore.RED}Not Found{Style.RESET_ALL}"
    
    # Source-based formatting
    source_indicator = ""
    if source == 'ml':
        source_indicator = f"{Fore.BLUE}[ML]{Style.RESET_ALL} "
    elif source == 'fallback':
        source_indicator = f"{Fore.YELLOW}[Rules]{Style.RESET_ALL} "
    
    # Confidence-based color for the value
    if confidence >= 0.8:
        return f"{source_indicator}{Fore.GREEN}{value}{Style.RESET_ALL}"
    elif confidence >= 0.6:
        return f"{source_indicator}{Fore.YELLOW}{value}{Style.RESET_ALL}"
    else:
        return f"{source_indicator}{Fore.RED}{value}{Style.RESET_ALL}"

# Function to run tests with improved output formatting
def run_tests(test_messages, category_name):
    print("\n" + "=" * 80)
    print(f"{Fore.CYAN}📊 TESTING CATEGORY: {category_name}{Style.RESET_ALL}")
    print("=" * 80)

    results_summary = {
        "total": len(test_messages),
        "bank_found": 0,
        "amount_found": 0,
        "date_found": 0,
        "payee_found": 0,
        "transaction_type_found": 0,
        "account_from_found": 0,
        "account_to_found": 0,
        # Add tracking for ML vs fallback rule usage
        "bank_by_ml": 0,
        "amount_by_ml": 0,
        "date_by_ml": 0,
        "payee_by_ml": 0,
        "transaction_type_by_ml": 0,
        "account_from_by_ml": 0,
        "account_to_by_ml": 0
    }

    for idx, sms in enumerate(test_messages, 1):
        print(f"\n{Fore.BLUE}Test #{idx}: {Style.RESET_ALL}")
        print(f"{Fore.BLUE}📩 SMS:{Style.RESET_ALL} {sms}")
        
        result = extract_transaction_details(sms)
        
        # Update results summary
        for field in result:
            if result[field]["value"] is not None:
                results_summary[f"{field}_found"] += 1
                if result[field]["source"] == "ml":
                    results_summary[f"{field}_by_ml"] += 1
        
        # Print results in a more readable format
        print(f"\n{Fore.BLUE}📋 Extracted Details:{Style.RESET_ALL}")
        print(f"  {Fore.CYAN}Bank:{Style.RESET_ALL} {format_entity(result['bank']['value'], result['bank']['confidence'], result['bank']['source'])} " + 
              f"(Confidence: {format_confidence(result['bank']['confidence'])})")
        
        print(f"  {Fore.CYAN}Amount:{Style.RESET_ALL} {format_entity(result['amount']['value'], result['amount']['confidence'], result['amount']['source'])} " + 
              f"(Confidence: {format_confidence(result['amount']['confidence'])})")
        
        print(f"  {Fore.CYAN}Date:{Style.RESET_ALL} {format_entity(result['date']['value'], result['date']['confidence'], result['date']['source'])} " + 
              f"(Confidence: {format_confidence(result['date']['confidence'])})")
        
        print(f"  {Fore.CYAN}Payee:{Style.RESET_ALL} {format_entity(result['payee']['value'], result['payee']['confidence'], result['payee']['source'])} " + 
              f"(Confidence: {format_confidence(result['payee']['confidence'])})")
        
        print(f"  {Fore.CYAN}Transaction Type:{Style.RESET_ALL} {format_entity(result['transaction_type']['value'], result['transaction_type']['confidence'], result['transaction_type']['source'])} " + 
              f"(Confidence: {format_confidence(result['transaction_type']['confidence'])})")
        
        print(f"  {Fore.CYAN}Account From:{Style.RESET_ALL} {format_entity(result['account_from']['value'], result['account_from']['confidence'], result['account_from']['source'])} " + 
              f"(Confidence: {format_confidence(result['account_from']['confidence'])})")
        
        print(f"  {Fore.CYAN}Account To:{Style.RESET_ALL} {format_entity(result['account_to']['value'], result['account_to']['confidence'], result['account_to']['source'])} " + 
              f"(Confidence: {format_confidence(result['account_to']['confidence'])})")
        
        print("-" * 80)
    
    # Print category summary with ML vs rules breakdown
    print(f"\n{Fore.CYAN}📊 CATEGORY SUMMARY: {category_name}{Style.RESET_ALL}")
    total = results_summary["total"]
    
    for field in ["bank", "amount", "date", "payee", "transaction_type", "account_from", "account_to"]:
        found = results_summary[f"{field}_found"]
        found_by_ml = results_summary[f"{field}_by_ml"]
        found_by_rules = found - found_by_ml
        percent = (found / total) * 100
        
        # Color-code the percentages
        if percent >= 75:
            color = Fore.GREEN
        elif percent >= 50:
            color = Fore.YELLOW
        else:
            color = Fore.RED
        
        # Calculate percentage of ML vs fallback extraction
        ml_percent = (found_by_ml / found * 100) if found > 0 else 0
        rules_percent = 100 - ml_percent
            
        print(f"  {Fore.CYAN}{field.replace('_', ' ').title()}:{Style.RESET_ALL} {found}/{total} ({color}{percent:.1f}%{Style.RESET_ALL}) - " +
             f"{Fore.BLUE}ML:{found_by_ml}/{found} ({ml_percent:.1f}%){Style.RESET_ALL}, " +
             f"{Fore.YELLOW}Rules:{found_by_rules}/{found} ({rules_percent:.1f}%){Style.RESET_ALL}")
    
    return results_summary

# Create a dictionary of test categories
test_categories = {
    "Simple SMS Formats": simple_test_messages,
    "Complex SMS Formats": complex_test_messages,
    "UPI Transactions": upi_test_messages,
    "Service Payments": service_payment_messages
}

# Run all test categories
all_results = {}
for category, messages in test_categories.items():
    all_results[category] = run_tests(messages, category)

# Calculate and print overall statistics
print("\n" + "=" * 80)
print(f"{Fore.CYAN}📊 OVERALL TEST RESULTS{Style.RESET_ALL}")
print("=" * 80)

total_messages = sum(result["total"] for result in all_results.values())

# Print overall extraction success rates with ML vs rules breakdown
print(f"\n{Fore.CYAN}Overall Extraction Success Rates:{Style.RESET_ALL}")
for field in ["bank", "amount", "date", "payee", "transaction_type", "account_from", "account_to"]:
    field_found = sum(all_results[cat][f"{field}_found"] for cat in test_categories.keys())
    field_by_ml = sum(all_results[cat][f"{field}_by_ml"] for cat in test_categories.keys())
    field_by_rules = field_found - field_by_ml
    
    success_rate = (field_found / total_messages) * 100
    
    # Color-code the percentages
    if success_rate >= 75:
        color = Fore.GREEN
    elif success_rate >= 50:
        color = Fore.YELLOW
    else:
        color = Fore.RED
    
    # Calculate percentage of ML vs fallback extraction
    ml_percent = (field_by_ml / field_found * 100) if field_found > 0 else 0
    rules_percent = 100 - ml_percent
    
    print(f"  {Fore.CYAN}{field.replace('_', ' ').title()}:{Style.RESET_ALL} {field_found}/{total_messages} ({color}{success_rate:.1f}%{Style.RESET_ALL}) - " +
         f"{Fore.BLUE}ML:{field_by_ml}/{field_found} ({ml_percent:.1f}%){Style.RESET_ALL}, " +
         f"{Fore.YELLOW}Rules:{field_by_rules}/{field_found} ({rules_percent:.1f}%){Style.RESET_ALL}")

class TestComprehensiveAI(unittest.TestCase):
    
    def setUp(self):
        # Use the enhanced model instead of the original
        self.nlp = spacy.load("/workspaces/ParsePay/sms_transaction_detector/ml-model/enhanced_training/best_model")
        
    # ...existing code...