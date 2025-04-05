import sys
import os
from datetime import datetime

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.transaction_classifier import is_financial_transaction
from extractor.transaction_extractor import extract_transaction_details

# Define test categories
simple_test_messages = [
    # ✅ Financial messages with simple formats
    "Sent Rs.73.00 From HDFC Bank A/C x2228 To Marvel On 04/04/25 Ref 509482752071",
    "Rs.652 spent on HDFC Bank Card x1135 at PAY*Flipkart Internet on 2025-03-25:06:43:19",
    "Credit Alert! Rs.10.00 credited to HDFC Bank A/c xx2228 on 03-04-25 from VPA one97735@icici",
]

complex_test_messages = [
    # ✅ Complex financial messages with diverse formats
    "Dear Customer, Your Acct XX5678 is debited with Rs.1,23,456.78 on 05.04.2025 for Flipkart order #FLP87654321 (UPI Ref: 123456789012). Avl Bal: Rs.987654.32",
    "ALERT: INR 42,599.00 debited from a/c XX3487 on 01-Apr-25 at AMAZON.IN/BILL. Avl bal: INR 15,736.88. Dispute? Call 1800-425-3800 within 7 days.",
    "SBI: Rs.13750.00 transferred to Mrs. Sharmila J (A/c xxxxxxxx5432) on 04-04-2025 from A/c xxxxxxxx9876 using SBI YONO. Ref # YBT123456789.",
    "IDFC FIRST Bank: Your salary of Rs.87,500.00 has been credited to your account XX9876 on 04/04/2025. Subject: APR-25 SALARY. Balance: Rs.1,12,453.28",
]

bank_test_messages = [
    # ✅ Messages with various bank name formats
    "HDFC Bank: Your account XXXX1234 has been debited with Rs.5,678.90 on 04-Apr-25 at Swiggy. Avl bal: Rs.12,345.67",
    "ICICI: Rs.3,456.78 has been debited from your a/c XX9876 for BigBasket transaction on 05.04.2025. Balance: Rs.23,456.78",
    "SBI alert: Rs.750 transferred to Raghav (UPI ID raghav@okicici) from a/c XX1234 on 04/04/2025. YONO Ref #98765432.",
    "Transaction alert from Axis Bank: Your Debit Card XX5678 was used for Rs.1,200 at PVR Cinemas on 04-Apr-25.",
]

# New test cases for enhanced date detection
date_test_messages = [
    # ✅ Messages with various date formats
    "Your transaction of Rs.1,500 on 5th April 2025 at BigBazaar has been processed.",
    "Transaction successful: Rs.8,750 sent to Amit Kumar on April 4, 2025 via IMPS.",
    "Rs.3,299 debited on 02.04.2025 12:15:45 PM for Amazon Prime annual subscription.",
    "Payment of Rs.599 made today for Netflix subscription renewal.",
    "ALERT: Rs.12,000 withdrawn yesterday from ATM BKC-04. Avl Bal: Rs.34,567.89",
    "Your account XX4567 will be debited Rs.1,299 tomorrow for auto-renewal of Hotstar subscription.",
]

# New test cases for bank inference without explicit bank names
bank_inference_test_messages = [
    # ✅ Messages with bank references that need to be inferred
    "Your UPI payment of Rs.450 to rahul@okaxis has been successful. Ref: 987654321",
    "Rs.2,500 transferred to priya45@ybl from your account. UPI Ref: 456789123",
    "Payment of Rs.750 to merchant UPI 98765@icici has been completed. Ref# UPI/123456789012/752",
    "A/c XX4531 debited INR 4,599 on 05-Apr-25. Info: AMZN Shopping. Avl Bal: INR 15,432.10",
    "Card XX7842 used for Rs.899 at Dominos Pizza on 04-Apr-25 16:33:45. Not you? Call 18001234567",
]

# Non-financial messages for comparison
non_financial_messages = [
    # ❌ Non-financial messages
    "Your OTP for login is 234556. Valid for 10 minutes.",
    "Don't miss our sale! Up to 70% off on Myntra until Sunday!",
    "Reminder: Your HDFC home loan EMI is due on 10-04-2025.",
    "Your parcel has been shipped and will be delivered by tomorrow.",
    "Your Axis Bank Credit Card statement for March 2025 is ready. Due date: 18-Apr-2025. Min amount due: Rs.3,500. Total: Rs.42,678.",
    "ALERT: A login attempt was made to your Axis mobile banking from device SM-G998B at 15:45:23 on 04-Apr-25."
]

# Combine test cases or run separate categories
test_categories = {
    "Simple SMS Formats": simple_test_messages,
    "Complex SMS Formats": complex_test_messages,
    "Bank Name Formats": bank_test_messages,
    "Date Format Variations": date_test_messages,
    "Bank Inference Tests": bank_inference_test_messages,
    "Non-Financial Messages": non_financial_messages
}

# Function to run tests
def run_tests(test_messages, category_name):
    print("\n" + "=" * 40)
    print(f"TESTING CATEGORY: {category_name}")
    print("=" * 40)
    
    total_tests = len(test_messages)
    successful_classification = 0
    successful_extraction = {
        "bank": 0,
        "amount": 0,
        "date": 0,
        "payee": 0,
        "transaction_type": 0,
        "account_from": 0,
        "account_to": 0
    }
    
    for sms in test_messages:
        print("—" * 120)
        print(f"📩 SMS: {sms}")
        
        is_financial = is_financial_transaction(sms)
        
        # Check if it's a financial message from the category name (all are financial except non-financial)
        expected_financial = "Non-Financial" not in category_name
        
        if is_financial == expected_financial:
            successful_classification += 1
        
        if is_financial:
            print("✅ Detected financial message.")
            result = extract_transaction_details(sms)
            print("📊 Extracted details:")
            
            # Track successful extractions
            for field in successful_extraction.keys():
                if field in result and result[field].get("value") is not None:
                    successful_extraction[field] += 1

            def print_field(label: str, field_data: dict):
                if isinstance(field_data, dict):
                    value = field_data.get("value", "")
                    confidence = field_data.get("confidence", 0.0)
                    error = field_data.get("error", "")
                    if value:
                        print(f"  ✅ {label}: {value} (Confidence: {confidence:.2f})")
                    else:
                        print(f"  ⚠️ {label}: N/A (Confidence: {confidence:.2f})")
                        if error:
                            print(f"     ⚠️  Error: {error}")
                else:
                    print(f"  ⚠️ {label}: Unexpected format: {field_data}")

            # Print extraction results
            print_field("Bank", result.get("bank"))
            print_field("Amount", result.get("amount"))
            print_field("Date", result.get("date"))
            print_field("Payee", result.get("payee"))
            print_field("Transaction type", result.get("transaction_type"))
            print_field("Account from", result.get("account_from"))
            print_field("Account to", result.get("account_to"))
        else:
            print("❌ Not a financial transaction.")
    
    # Print category statistics
    print("\n" + "-" * 40)
    print(f"CATEGORY SUMMARY: {category_name}")
    print(f"Classification Accuracy: {successful_classification}/{total_tests} ({successful_classification/total_tests*100:.1f}%)")
    
    if "Non-Financial" not in category_name:
        print("\nField Extraction Success Rates:")
        for field, success_count in successful_extraction.items():
            print(f"  {field.capitalize()}: {success_count}/{total_tests} ({success_count/total_tests*100:.1f}%)")
    
    return {
        "total": total_tests,
        "classification_success": successful_classification,
        "extraction_success": successful_extraction
    }

# Run each test category
all_results = {}
for category, messages in test_categories.items():
    all_results[category] = run_tests(messages, category)

# Calculate and display overall statistics
print("\n" + "=" * 40)
print("OVERALL TEST RESULTS")
print("=" * 40)

total_messages = sum(result["total"] for result in all_results.values())
total_classification_success = sum(result["classification_success"] for result in all_results.values())

print(f"Total Messages Tested: {total_messages}")
print(f"Overall Classification Accuracy: {total_classification_success}/{total_messages} ({total_classification_success/total_messages*100:.1f}%)")

# Calculate extraction success rates for financial messages only
financial_categories = [cat for cat in test_categories.keys() if "Non-Financial" not in cat]
financial_total = sum(all_results[cat]["total"] for cat in financial_categories)

print("\nOverall Extraction Success Rates (Financial Messages Only):")
for field in ["bank", "amount", "date", "payee", "transaction_type", "account_from", "account_to"]:
    field_success = sum(all_results[cat]["extraction_success"][field] for cat in financial_categories)
    success_rate = field_success / financial_total * 100
    print(f"  {field.capitalize()}: {field_success}/{financial_total} ({success_rate:.1f}%)")