import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.transaction_classifier import is_financial_transaction
from extractor.transaction_extractor import extract_transaction_details

# Original test messages
simple_test_messages = [
    # ✅ Financial messages
    "Sent Rs.73.00 From HDFC Bank A/C x2228 To Marvel On 04/04/25 Ref 509482752071",
    "Rs.652 spent on HDFC Bank Card x1135 at PAY*Flipkart Internet on 2025-03-25:06:43:19",
    "Credit Alert! Rs.10.00 credited to HDFC Bank A/c xx2228 on 03-04-25 from VPA one97735@icici",

    # ❌ Non-financial messages
    "Your OTP for login is 234556. Valid for 10 minutes.",
    "Don't miss our sale! Up to 70% off on Myntra until Sunday!",
    "Reminder: Your HDFC home loan EMI is due on 10-04-2025.",
    "Your parcel has been shipped and will be delivered by tomorrow."
]

# New complex test messages
complex_test_messages = [
    # ✅ Complex financial messages
    "Dear Customer, Your Acct XX5678 is debited with Rs.1,23,456.78 on 05.04.2025 for Flipkart order #FLP87654321 (UPI Ref: 123456789012). Avl Bal: Rs.987654.32",
    "ALERT: INR 42,599.00 debited from a/c XX3487 on 01-Apr-25 at AMAZON.IN/BILL. Avl bal: INR 15,736.88. Dispute? Call 1800-425-3800 within 7 days.",
    "SBI: Rs.13750.00 transferred to Mrs. Sharmila J (A/c xxxxxxxx5432) on 04-04-2025 from A/c xxxxxxxx9876 using SBI YONO. Ref # YBT123456789.",
    "IDFC FIRST Bank: Your salary of Rs.87,500.00 has been credited to your account XX9876 on 04/04/2025. Subject: APR-25 SALARY. Balance: Rs.1,12,453.28",
    
    # ❌ Complex non-financial messages
    "Your Axis Bank Credit Card statement for March 2025 is ready. Due date: 18-Apr-2025. Min amount due: Rs.3,500. Total: Rs.42,678. View on mobile app.",
    "ALERT: A login attempt was made to your Axis mobile banking from device SM-G998B at 15:45:23 on 04-Apr-25. Not you? Call 18605505555 immediately."
]

# Add more messages specifically for testing bank name extraction
bank_test_messages = [
    "HDFC Bank: Your account XXXX1234 has been debited with Rs.5,678.90 on 04-Apr-25 at Swiggy. Avl bal: Rs.12,345.67",
    "ICICI: Rs.3,456.78 has been debited from your a/c XX9876 for BigBasket transaction on 05.04.2025. Balance: Rs.23,456.78",
    "SBI alert: Rs.750 transferred to Raghav (UPI ID raghav@okicici) from a/c XX1234 on 04/04/2025. YONO Ref #98765432.",
    "Transaction alert from Axis Bank: Your Debit Card XX5678 was used for Rs.1,200 at PVR Cinemas on 04-Apr-25."
]

# Combine both test sets or choose one
# test_messages = simple_test_messages
# test_messages = complex_test_messages
# test_messages = bank_test_messages
test_messages = complex_test_messages + bank_test_messages

for sms in test_messages:
    print("—" * 120)
    print(f"📩 SMS: {sms}")
    
    if is_financial_transaction(sms):
        result = extract_transaction_details(sms)

        print("✅ Detected financial message.")
        print("📊 Extracted details:")

        def print_field(label: str, field_data: dict):
            # Check if the field is a dictionary (structured output)
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

        print_field("Bank", result.get("bank"))
        print_field("Amount", result.get("amount"))
        print_field("Date", result.get("date"))
        print_field("Payee", result.get("payee"))
        print_field("Transaction type", result.get("transaction_type"))
        print_field("Account from", result.get("account_from"))
        print_field("Account to", result.get("account_to"))

    else:
        print("❌ Not a financial transaction.")