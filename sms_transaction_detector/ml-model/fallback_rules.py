import re

def apply_fallback_rules(sms_text, result):
    """
    Apply fallback rules to extract entities when the ML model fails to detect them.
    This function is separated from the training script to allow independent use.
    
    Args:
        sms_text (str): The SMS text to analyze
        result (dict): Dictionary containing entity extraction results to update
    """
    # Amount extraction - if not found by ML model
    if not result["amount"]["value"]:
        amount_patterns = [
            r'Rs\.?\s*([0-9,]+\.?[0-9]*)', 
            r'INR\s*([0-9,]+\.?[0-9]*)',
            r'Rs\s*([0-9,]+\.?[0-9]*)',
            r'debited with\s*Rs\.?\s*([0-9,]+\.?[0-9]*)',
            r'([0-9,]+\.?[0-9]*)\s*(?:Rs\.?|INR)',
            r'of\s*Rs\.?\s*([0-9,]+\.?[0-9]*)',
            r'for\s*Rs\.?\s*([0-9,]+\.?[0-9]*)'
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, sms_text, re.IGNORECASE)
            if match:
                result["amount"]["value"] = match.group(0).strip()
                result["amount"]["confidence"] = 0.7
                break
    
    # Date extraction - if not found by ML model
    if not result["date"]["value"]:
        date_patterns = [
            r'(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})',  # DD-MM-YYYY, MM/DD/YYYY
            r'(\d{4}[-/\.]\d{1,2}[-/\.]\d{1,2})',    # YYYY-MM-DD
            r'(\d{1,2}[-/\.][A-Za-z]{3,4}[-/\.]\d{2,4})',  # DD-MMM-YYYY
            r'on\s+(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})',
            r'on\s+(\d{1,2}[-/\.][A-Za-z]{3,4}[-/\.]\d{2,4})'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, sms_text, re.IGNORECASE)
            if match:
                if match.group(0).startswith('on '):
                    result["date"]["value"] = match.group(1).strip()
                else:
                    result["date"]["value"] = match.group(0).strip()
                result["date"]["confidence"] = 0.65
                break
    
    # Bank extraction - if not found by ML model
    if not result["bank"]["value"]:
        banks = {
            "HDFC": ["HDFC", "HDFC Bank"],
            "SBI": ["SBI", "State Bank", "State Bank of India"],
            "ICICI": ["ICICI", "ICICI Bank"],
            "Axis": ["Axis", "Axis Bank"],
            "IDFC FIRST": ["IDFC", "IDFC FIRST", "IDFC Bank"],
            "Yes Bank": ["Yes Bank"],
            "Kotak": ["Kotak", "Kotak Bank", "Kotak Mahindra"],
            "PNB": ["PNB", "Punjab National Bank"],
            "Bank of Baroda": ["BOB", "Bank of Baroda"]
        }
        
        for bank, keywords in banks.items():
            for keyword in keywords:
                if keyword in sms_text:
                    result["bank"]["value"] = bank
                    result["bank"]["confidence"] = 0.75
                    break
            if result["bank"]["value"]:
                break
    
    # Transaction type detection - if not found by ML model
    if not result["transaction_type"]["value"]:
        transaction_patterns = {
            "CREDIT": [r'credited', r'received', r'credit', r'salary', r'deposited', r'added'],
            "DEBIT": [r'debited', r'spent', r'paid', r'payment', r'purchase', r'debit', r'withdrawn'],
            "TRANSFER": [r'transferred', r'transfer', r'sent', r'IMPS', r'NEFT', r'RTGS', r'UPI']
        }
        
        for txn_type, patterns in transaction_patterns.items():
            for pattern in patterns:
                if re.search(pattern, sms_text, re.IGNORECASE):
                    result["transaction_type"]["value"] = txn_type
                    result["transaction_type"]["confidence"] = 0.7
                    break
            if result["transaction_type"]["value"]:
                break
    
    # Payee extraction - if not found by ML model
    if not result["payee"]["value"]:
        payee_patterns = [
            r'to\s+([A-Za-z0-9\s\.\-\']+?)\s+(?:on|via|ref|from|a\/c)',
            r'at\s+([A-Z0-9\s\*\/\.\-]+?)(?:\s+on|\.|$)',
            r'for\s+([A-Za-z0-9\s\.\-\']+?)(?:\s+on|\.|$)',
            r'paid\s+to\s+([A-Za-z0-9\s\.\-\']+?)(?:\s+|\.|\(|$)',
            r'transferred\s+to\s+([A-Za-z0-9\s\.\-\']+?)(?:\s+|\.|\(|$)',
            r'credited\s+from\s+([A-Za-z0-9\s\.\-\']+?)(?:\s+|\.|\(|$)'
        ]
        
        for pattern in payee_patterns:
            match = re.search(pattern, sms_text, re.IGNORECASE)
            if match:
                result["payee"]["value"] = match.group(1).strip()
                result["payee"]["confidence"] = 0.6
                break
        
        # UPI ID pattern
        if not result["payee"]["value"] and "@" in sms_text:
            upi_pattern = r'([a-zA-Z0-9\.\-\_]+@[a-z]+)'
            match = re.search(upi_pattern, sms_text)
            if match:
                result["payee"]["value"] = match.group(1).strip()
                result["payee"]["confidence"] = 0.55
    
    # Account extraction - if not found by ML model
    account_patterns = [
        # From account patterns
        (r'from\s+(?:a\/c|account|acc\.?|ac)(?:\s+no\.?)?\s*[:\.#]?\s*([\dXx\*]{4,})', "account_from"),
        (r'from\s+(?:a\/c|account|acc\.?|ac)(?:\s+no\.?)?\s*[:\.#]?\s*([Xx\*]+\d{1,4})', "account_from"),
        (r'your\s+(?:a\/c|account|acc\.?|ac)(?:\s+no\.?)?\s*[:\.#]?\s*([\dXx\*]{4,})', "account_from"),
        (r'card\s+[\w\s\.\-\']+?\s*(X+\d+|x+\d+|\*+\d+)', "account_from"),
        
        # To account patterns
        (r'to\s+(?:a\/c|account|acc\.?|ac)(?:\s+no\.?)?\s*[:\.#]?\s*([\dXx\*]{4,})', "account_to"),
        (r'to\s+(?:a\/c|account|acc\.?|ac)(?:\s+no\.?)?\s*[:\.#]?\s*([Xx\*]+\d{1,4})', "account_to"),
        (r'credited\s+to\s+.{1,30}?\s*(?:a\/c|account|acc\.?|ac)(?:\s+no\.?)?\s*[:\.#]?\s*([\dXx\*]{4,})', "account_to")
    ]
    
    for pattern, field in account_patterns:
        if not result[field]["value"]:
            match = re.search(pattern, sms_text, re.IGNORECASE)
            if match:
                result[field]["value"] = match.group(1).strip()
                result[field]["confidence"] = 0.65