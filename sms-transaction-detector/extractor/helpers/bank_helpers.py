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