import sys
import os

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model.transaction_classifier import is_financial_transaction
from extractor.transaction_extractor import extract_transaction_details

test_messages = [
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

        print_field("Amount", result.get("amount"))
        print_field("Date", result.get("date"))
        print_field("Payee", result.get("payee"))
        print_field("Transaction type", result.get("transaction_type"))
        print_field("Account from", result.get("account_from"))
        print_field("Account to", result.get("account_to"))

    else:
        print("❌ Not a financial transaction.")
