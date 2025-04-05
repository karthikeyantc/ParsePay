import re
from datetime import datetime, timedelta

def match_bank_patterns(sms: str, known_banks: list, bank_patterns: list) -> tuple:
    """Helper function to match bank patterns in SMS."""
    for pattern in bank_patterns:
        match = re.search(pattern, sms, re.IGNORECASE)
        if match:
            potential_bank = match.group(1).strip().strip('.:,')
            potential_bank = re.sub(r"^(?:from|alert|to|in|your)\s+", "", potential_bank, flags=re.IGNORECASE)
            for known_bank in known_banks:
                if known_bank in potential_bank.upper():
                    return potential_bank, 0.9
    return None, 0.0

def match_upi_or_account(sms: str, known_banks: list, account_prefix_to_bank: dict) -> dict:
    """Helper function to match UPI or account prefix for bank inference."""
    upi_match = re.search(r'@([a-z]+)', sms, re.IGNORECASE)
    if upi_match:
        upi_suffix = upi_match.group(1).upper()
        if upi_suffix in [bank.upper() for bank in known_banks]:
            return {"value": upi_suffix, "confidence": 0.65, "error": None}
        elif "OKICICI" in upi_suffix:
            return {"value": "ICICI", "confidence": 0.65, "error": None}
        elif "OKAXIS" in upi_suffix:
            return {"value": "AXIS", "confidence": 0.65, "error": None}
        elif "YBL" in upi_suffix:
            return {"value": "YES", "confidence": 0.65, "error": None}
    account_match = re.search(r'(?:xx|x|XX)(\d{2})\d+', sms)
    if account_match:
        prefix = account_match.group(1)
        if prefix in account_prefix_to_bank:
            return {"value": account_prefix_to_bank[prefix], "confidence": 0.5, "error": None}
    return {"value": None, "confidence": 0.0, "error": "Bank name not found"}

def extract_accounts(text):
    """
    Extract account information from transaction SMS.
    
    Identifies both source (from) and destination (to) accounts.
    Returns a tuple of (from_account, from_confidence, to_account, to_confidence)
    """
    # Account From patterns
    from_patterns = [
        # Account number patterns
        r'(?:from|debited from|withdrawn from|fr)[^a-zA-Z0-9]*(?:a\/c|ac|acct|account)[^a-zA-Z0-9]*([A-Z]{2}\d+|\d+|[xX]+\d+)',
        r'(?:from|debited from|withdrawn from|fr)[^a-zA-Z0-9]*((?:[xX]{2,}|\*{2,})\d{4,})',
        r'(?:from|debited from|withdrawn from)[^a-zA-Z0-9]*((?:\d{2,}[xX]{2,}|\d{2,}\*{2,}))',
        r'(?:a\/c|ac|acct|account)[^a-zA-Z0-9]*([xX]{2,}\d{4,}|\d{2,}[xX]{2,}|\*{2,}\d{4,}|\d{2,}\*{2,})[^a-zA-Z0-9]*(?:debited|txn|transaction)',
        
        # UPI handles
        r'(?:from|debited from|withdrawn from)[^a-zA-Z0-9]*(\w+@\w+)',
        
        # Card references
        r'(?:card)[^a-zA-Z0-9]*([xX]{2,}\d{4,}|\d{2,}[xX]{2,})',
        r'(?:using|via)[^a-zA-Z0-9]*card[^a-zA-Z0-9]*(\d+[xX]+\d+|\d+)',
    ]
    
    # Account To patterns
    to_patterns = [
        # Account number patterns
        r'(?:to|credited to|deposited to|deposit to|transferred to|transfer to)[^a-zA-Z0-9]*(?:a\/c|ac|acct|account)[^a-zA-Z0-9]*([A-Z]{2}\d+|\d+|[xX]+\d+)',
        r'(?:to|credited to|deposited to|deposit to|transferred to|transfer to)[^a-zA-Z0-9]*((?:[xX]{2,}|\*{2,})\d{4,})',
        r'(?:to|credited to|deposited to|deposit to|transferred to|transfer to)[^a-zA-Z0-9]*((?:\d{2,}[xX]{2,}|\d{2,}\*{2,}))',
        
        # UPI handles and beneficiaries
        r'(?:to|credited to|deposited to|paid to)[^a-zA-Z0-9]*([a-zA-Z0-9_.]+@[a-zA-Z0-9]+)',
        r'(?:to|credited to|deposited to|paid to|transfer to)[^a-zA-Z0-9]*([A-Za-z\s.]+)[^a-zA-Z0-9]*(?:via|using|on|through)',
        r'(?:beneficiary|benef|payee)[^a-zA-Z0-9]*([A-Za-z\s.]+)[^a-zA-Z0-9]*(?:is|with)',
        
        # Merchant references
        r'(?:merchant)[^a-zA-Z0-9]*([A-Za-z0-9\s.]+)',
    ]
    
    # Account From extraction
    from_account = None
    from_confidence = 0.0
    
    for pattern in from_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            from_account = match.group(1).strip()
            from_confidence = 0.7  # Base confidence
            
            # Boost confidence for clearer patterns
            if 'a/c' in pattern or 'account' in pattern:
                from_confidence = 0.8
                
            # Extra boost for account with masked digits
            if re.search(r'[xX*]{2,}\d+', from_account) or re.search(r'\d+[xX*]{2,}', from_account):
                from_confidence = 0.85
                
            break
    
    # Account To extraction
    to_account = None
    to_confidence = 0.0
    
    for pattern in to_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            to_account = match.group(1).strip()
            to_confidence = 0.7  # Base confidence
            
            # Boost confidence for clearer patterns
            if 'a/c' in pattern or 'account' in pattern:
                to_confidence = 0.8
                
            # Boost for email-like UPI handles
            if '@' in to_account:
                to_confidence = 0.85
                
            break
    
    return from_account, from_confidence, to_account, to_confidence