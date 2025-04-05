import unittest
import sys
import os
from datetime import datetime

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extractor.transaction_extractor import extract_transaction_details

class TestPayeeExtraction(unittest.TestCase):
    
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
    
    def test_upi_id_extraction(self):
        # Test UPI ID extraction
        sms_messages = [
            "UPI transaction successful! Rs.500.00 sent to john.doe@okicici from XX5678 on 05-04-2025.",
            "Payment of Rs.1,200 to sam.smith@ybl completed via UPI ID Reference: UPI/123456789.",
            "SBI Alert: Rs.245.00 debited from account XX1234 to merchant.payment@okaxis via UPI.",
            "ALERT: Transaction of INR 350.00 to coffee.shop@paytm is successful. UPI Ref: 20250405112233.",
            "HDFC Bank: INR 1,050.00 transferred to furniture.store@hdfc from your a/c XX9876."
        ]
        
        expected_payees = ["john.doe@okicici", "sam.smith@ybl", "merchant.payment@okaxis", 
                           "coffee.shop@paytm", "furniture.store@hdfc"]
        
        for i, sms in enumerate(sms_messages):
            result = extract_transaction_details(sms)
            self.assertEqual(result["payee"]["value"], expected_payees[i])
            self.assertGreaterEqual(result["payee"]["confidence"], 0.85)
    
    def test_person_name_extraction(self):
        # Test person name extraction
        sms_messages = [
            "Rs.1,500.00 transferred to Rajesh Kumar's A/c XX2468 via IMPS. Ref: IMPS/123456789.",
            "ICICI Bank: INR 3,000.00 sent to PRIYA SHARMA a/c XX1379 through NEFT.",
            "SBI Alert: Rs.2,750.00 debited for fund transfer to AMIT SINGH (A/c: XX7531).",
            "Payment of Rs.1,000.00 to MEENA PATEL successful. IMPS Ref: P2P12345678.",
            "HDFC Bank: Rs.5,000.00 transferred to VIJAY MEHTA a/c XX9753 as per your request."
        ]
        
        expected_names = ["Rajesh Kumar", "PRIYA SHARMA", "AMIT SINGH", "MEENA PATEL", "VIJAY MEHTA"]
        
        for i, sms in enumerate(sms_messages):
            result = extract_transaction_details(sms)
            self.assertEqual(result["payee"]["value"], expected_names[i])
            self.assertGreaterEqual(result["payee"]["confidence"], 0.8)
    
    def test_service_payment_extraction(self):
        # Test service payment extraction
        sms_messages = [
            "Thank you for paying Rs.1,250.00 towards your Electricity Bill from your ICICI Bank a/c XX5432.",
            "HDFC Bank: INR 899.00 debited for Mobile Bill Payment to Airtel from XX7654.",
            "SBI Alert: Rs.450.00 paid for DTH Recharge - Tata Sky from your account XX3456.",
            "ALERT: Your Credit Card Bill payment of Rs.5,500.00 from a/c XX8765 is successful.",
            "Payment of Rs.2,199.00 towards Broadband Bill - Jio Fiber is complete. Ref: BILL12345."
        ]
        
        expected_services = ["Electricity Bill", "Mobile Bill Payment - Airtel", "DTH Recharge - Tata Sky",
                            "Credit Card Bill", "Broadband Bill - Jio Fiber"]
        
        for i, sms in enumerate(sms_messages):
            result = extract_transaction_details(sms)
            self.assertEqual(result["payee"]["value"], expected_services[i])
            self.assertGreaterEqual(result["payee"]["confidence"], 0.75)
    
    def test_edge_cases(self):
        # Test edge cases and mixed formats
        sms_messages = [
            "ALERT: Rs.500.00 sent via UPI app to Ram's vegetable stall (UPI ID: ram.veg@okicici).",
            "Payment of Rs.1,500.00 to Dr. John for Medical Consultation completed.",
            "Transaction of INR 299.00 at NETFLIX subscription successful.",
            "HDFC Bank: Rs.2,500.00 transferred to XYZ Corp. for Invoice #12345 via RTGS.",
            "SBI Alert: NEFT transfer of Rs.10,000.00 to Scholarship Fund - ABC University completed."
        ]
        
        expected_payees = ["Ram's vegetable stall (ram.veg@okicici)", "Dr. John - Medical Consultation", 
                           "NETFLIX subscription", "XYZ Corp. - Invoice #12345", "Scholarship Fund - ABC University"]
        
        for i, sms in enumerate(sms_messages):
            result = extract_transaction_details(sms)
            self.assertEqual(result["payee"]["value"], expected_payees[i])
            self.assertGreaterEqual(result["payee"]["confidence"], 0.7)
    
    def test_missing_payee(self):
        # Test SMS messages with no clear payee information
        sms_messages = [
            "Your account XX1234 has been debited with Rs.500.00 on 05-04-2025.",
            "HDFC Bank: INR 1,000.00 withdrawn from ATM on 04-APR-2025.",
            "SBI Alert: Balance in a/c XX5678 as of 05-04-2025 is Rs.25,350.75",
            "Transaction of Rs.2,500.00 completed successfully. Reference: TXN123456789."
        ]
        
        for sms in sms_messages:
            result = extract_transaction_details(sms)
            self.assertIsNone(result["payee"]["value"])
            self.assertEqual(result["payee"]["confidence"], 0.0)
            self.assertIsNotNone(result["payee"]["error"])
            

if __name__ == "__main__":
    unittest.main()