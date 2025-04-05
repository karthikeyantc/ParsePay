import unittest
import sys
import os
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add the 'sms-transaction-detector' directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../sms-transaction-detector')))
# Add the workspace root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from sms_transaction_detector.ml_model.train_ner_model import extract_transaction_details

class TestPayeeExtractionAI(unittest.TestCase):
    
    def test_merchant_name_extraction(self):
        # Test merchant name extraction from various SMS formats
        sms_messages = [
            "Your HDFC Bank Card XX1234 has been used for Rs.2,500.00 at AMAZON RETAIL on 05-04-2025.",
            "HDFC Bank: Rs.1,200.00 debited from a/c XX5678 for purchase at FLIPKART on 05-APR-2025.",
            "ALERT: Transaction of INR 750.00 done at SWIGGY using your SBI Card ending 4321.",
            "Payment of Rs.350.50 made to UBER via UPI app from your ICICI account.",
            "Transaction Alert: INR 5,430.25 paid to RELIANCE RETAIL at 10:15 AM today from XX7890."
        ]
        
        expected_merchants = ["AMAZON RETAIL", "FLIPKART", "SWIGGY", "UBER", "RELIANCE RETAIL"]
        
        for i, sms in enumerate(sms_messages):
            result = extract_transaction_details(sms)
            self.assertEqual(result["payee"]["value"], expected_merchants[i])
            self.assertGreaterEqual(result["payee"]["confidence"], 0.8)

    # Additional test cases for UPI ID, person name, service payment, edge cases, and missing payee
    # can be replicated here, similar to the original test suite, but using the AI model.

if __name__ == "__main__":
    unittest.main()