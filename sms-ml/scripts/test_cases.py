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