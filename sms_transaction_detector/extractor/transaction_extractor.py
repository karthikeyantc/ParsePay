import re
from datetime import datetime, timedelta
from .helpers.bank_helpers import match_bank_patterns, match_upi_or_account
from .helpers.amount_helpers import match_amount_pattern
from .helpers.date_helpers import match_date_patterns, match_relative_dates

def extract_bank(sms: str) -> dict:
    """Extract bank name from SMS message."""
    result = {"value": None, "confidence": 0.0, "error": None}
    
    # List of known banks for validation
    known_banks = [
        "HDFC", "SBI", "ICICI", "AXIS", "IDFC FIRST", "YES", "KOTAK", "PNB", 
        "BOB", "BOI", "CANARA", "UNION", "DEUTSCHE", "INDUSIND", "FEDERAL",
        "RBL", "CITI", "HSBC", "IDBI", "UCO", "BANDHAN", "KARNATAKA", "INDIAN"
    ]
    
    # Mapping of account prefixes to likely banks
    account_prefix_to_bank = {
        "45": "HDFC",
        "21": "SBI",
        "33": "ICICI",
        "91": "AXIS",
        "59": "KOTAK",
        "36": "CITI",
        "40": "YES"
        # Add more mappings based on real-world observations
    }
    
    # Extract bank name - enhanced with more patterns and bank-account prefix mapping
    bank_patterns = [
        r"(?:^|\s)([A-Z]{2,}(?:\s+[A-Z]+)?\s+Bank)",  # "HDFC Bank", "SBI Bank"
        r"(?:^|\s)([A-Z]{2,}(?:\s+[A-Z]+)?):?(?:\s|$)",  # "HDFC:", "SBI:", "ICICI"
        r"(?:from|on|to|in|your)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?\s+[Bb]ank)",  # "your Axis Bank", "from HDFC Bank"
        r"(?:from|on|to|in|your)\s+([A-Z]{2,}\s+FIRST)"  # "IDFC FIRST"
    ]
    
    bank_name, bank_confidence = match_bank_patterns(sms, known_banks, bank_patterns)
    if bank_name:
        result = {"value": bank_name, "confidence": bank_confidence, "error": None}
    else:
        result = match_upi_or_account(sms, known_banks, account_prefix_to_bank)
    
    return result

def extract_amount(sms: str) -> dict:
    """Extract transaction amount from SMS message."""
    result = {"value": None, "confidence": 0.0, "error": None}
    
    amount_value, confidence = match_amount_pattern(sms)
    if amount_value:
        result = {"value": amount_value, "confidence": confidence, "error": None}
    else:
        result["error"] = "Amount not found"
    
    return result

def extract_date(sms: str) -> dict:
    """Extract transaction date from SMS message."""
    result = {"value": None, "confidence": 0.0, "error": None}
    
    today = datetime.now()
    current_year = today.year
    
    # First, try to extract full date patterns with year
    date_patterns = [
        # Explicit full dates with different separators and formats
        (r"\b(\d{2})[/-](\d{2})[/-](\d{2,4})\b", "%d-%m-%y"),          # 03-04-25 or 03/04/25
        (r"\b(\d{4})-(\d{2})-(\d{2})\b", "%Y-%m-%d"),                  # 2025-03-25
        (r"\b(\d{2})\.(\d{2})\.(\d{4})\b", "%d.%m.%Y"),                # 05.04.2025
        (r"\b(\d{2})/(\d{2})/(\d{4})\b", "%d/%m/%Y"),                  # 05/04/2025
        (r"\b(\d{2})-([A-Za-z]{3})-(\d{2,4})\b", "%d-%b-%y"),          # 01-Apr-25
        (r"\bon\s+(\d{2})[/-](\d{2})[/-](\d{2,4})\b", "%d-%m-%y"),     # on 03-04-25
        (r"\bon\s+(\d{2})\.(\d{2})\.(\d{4})\b", "%d.%m.%Y"),           # on 05.04.2025
        (r"\bon\s+(\d{1,2})\s+([A-Za-z]{3,9})[,]?\s+(\d{4})\b", "%d %B %Y"),  # on 5 April 2025
        (r"\bon\s+(\d{2})-([A-Za-z]{3})-(\d{2,4})\b", "%d-%b-%y"),     # on 01-Apr-25
        (r"\b([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b", "%B %d %Y"),  # April 5th, 2025
        (r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\s+(\d{4})\b", "%d %B %Y"),    # 5th April 2025
    ]
    
    date_value, confidence = match_date_patterns(sms, date_patterns, today)
    if not date_value:
        date_value, confidence = match_relative_dates(sms, today)
    
    if date_value:
        result = {"value": date_value, "confidence": confidence, "error": None}
    else:
        result["error"] = "Date not found"
    
    return result

def extract_transaction_type(sms: str) -> dict:
    """Extract transaction type from SMS message."""
    result = {"value": None, "confidence": 0.0, "error": None}
    
    # Enhanced transaction type detection
    if re.search(r"(?i)\b(debited|spent|paid|sent|withdrawn|withdrawal|purchase|payment)\b", sms):
        txn_type = "debit"
        result = {"value": txn_type, "confidence": 0.95, "error": None}
    elif re.search(r"(?i)\b(credited|received|deposit|salary|credit|cash\s+in)\b", sms):
        txn_type = "credit"
        result = {"value": txn_type, "confidence": 0.95, "error": None}
    elif re.search(r"(?i)\b(transferred|transfer|sent|paid|payment)\b", sms):
        txn_type = "debit"  # Most transfers are debits unless explicitly stated otherwise
        result = {"value": txn_type, "confidence": 0.95, "error": None}
    elif re.search(r"(?i)\b(card|debit card).+used\b", sms):  # Card usage is typically a debit
        txn_type = "debit"
        result = {"value": txn_type, "confidence": 0.95, "error": None}
    else:
        result["error"] = "Transaction type not found"
    
    return result

def extract_payee(sms: str) -> dict:
    """Extract payee information from SMS message."""
    result = {"value": None, "confidence": 0.0, "error": None}
    
    # 1. Merchant name extraction (for card transactions, POS, etc.)
    merchant_patterns = [
        r"(?i)(?:at|@)\s+([A-Z0-9\s]+)(?:\s+on|\.|$)",  # at AMAZON.IN
        r"(?i)(?:at|to|@)\s+([A-Z][A-Z0-9\s]+)(?:\s+using|\s+via|\s+on|\.|$)",  # at AMAZON using
        r"(?i)(?:POS|purchase)\s+(?:at|@)\s+([A-Z0-9\s]+)(?:\s+on|\.|$)",  # POS at WALMART
        r"(?i)(?:for purchase at|spent at|paid to|payment to)\s+([A-Z0-9\s]+)(?:\s+on|\.|$)",  # for purchase at FLIPKART
        r"(?i)(?:card|debit card|credit card).+(?:used|transaction|purchase).+(?:at|@)\s+([A-Z0-9\s]+)(?:\s+on|\.|$)" # card used at STORE
    ]
    
    for pattern in merchant_patterns:
        match = re.search(pattern, sms)
        if match:
            merchant = match.group(1).strip()
            # Filter out non-merchant text that might be mistakenly captured
            if merchant and not re.match(r'(?i)(on|using|via|the|your|our)', merchant):
                result = {"value": merchant, "confidence": 0.9, "error": None}
                break

    # 2. UPI ID extraction
    if not result["value"]:
        upi_patterns = [
            r"(?i)(?:to|2|sent to|paid to|payment to)\s+([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+)",  # to user@bank
            r"(?i)(?:UPI:?\s+|VPA:?\s+)([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+)",  # UPI: user@bank
            r"(?i)(?:UPI ID|VPA ID):?\s+([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+)",  # UPI ID: user@bank
            r"(?i)(?:UPI|VPA|UPI Ref):?\s+(?:.*?)\s+(?:to|2|ID:?)\s+([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+)" # UPI payment to user@bank
        ]
        
        for pattern in upi_patterns:
            match = re.search(pattern, sms)
            if match:
                upi_id = match.group(1).strip()
                result = {"value": upi_id, "confidence": 0.85, "error": None}
                break

    # 3. Person name extraction (for fund transfers, IMPS, NEFT, etc.)
    if not result["value"]:
        person_patterns = [
            r"(?i)(?:transferred|sent|payment|paid)(?:\s+to)?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})(?:'s)?\s+(?:A\/C|A\/c|Acct|account|a/c)",  # transferred to Rajesh Kumar's A/c
            r"(?i)(?:transferred|sent|payment|paid)(?:\s+to)?\s+([A-Z]{2,}(?:\s+[A-Z]{2,}){1,2})(?:'s)?\s+(?:A\/C|A\/c|Acct|account|a/c)",  # transferred to PRIYA SHARMA a/c
            r"(?i)(?:to|2)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})(?:\s+via|\s+through|\s+using|\s+by)?",  # to Rajesh Kumar via
            r"(?i)(?:to|2)\s+([A-Z]{2,}(?:\s+[A-Z]{2,}){1,2})(?:\s+via|\s+through|\s+using|\s+by)?",  # to PRIYA SHARMA via
            r"(?i)(?:beneficiary|benef|recipient):?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})",  # beneficiary: Rajesh Kumar
            r"(?i)(?:beneficiary|benef|recipient):?\s+([A-Z]{2,}(?:\s+[A-Z]{2,}){1,2})",  # beneficiary: PRIYA SHARMA
            r"(?i)(?:to|2)\s+(?:the\s+account\s+of\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})",  # to the account of Rajesh Kumar
            r"(?i)(?:to|2)\s+(?:the\s+account\s+of\s+)([A-Z]{2,}(?:\s+[A-Z]{2,}){1,2})",  # to the account of PRIYA SHARMA
            r"(?i)(?:transfer|payment|sent|paid)\s+to\s+(?:[^.]*?)(?:\()([^)]+)(?:\))",  # transfer to account (PRIYA SHARMA)
            r"(?i)(?:fund\s+transfer|transfer|payment|sent|paid)\s+to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,2})",  # fund transfer to Rajesh Kumar
            r"(?i)(?:fund\s+transfer|transfer|payment|sent|paid)\s+to\s+([A-Z]{2,}(?:\s+[A-Z]{2,}){1,2})",  # fund transfer to PRIYA SHARMA
            # Special case for Dr./Mr./Mrs. titles
            r"(?i)(?:to|2|sent to|paid to|payment to)\s+((?:Dr|Mr|Mrs|Ms|Prof)\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)"  # to Dr. John Smith
        ]

        for pattern in person_patterns:
            match = re.search(pattern, sms)
            if match:
                person_name = match.group(1).strip()
                # Check if it's likely a person name (not containing common non-name words)
                if person_name and not re.search(r'(?i)\b(bank|card|account|billing|payment|purchase|transaction|reference|paid|using|info)\b', person_name):
                    result = {"value": person_name, "confidence": 0.85, "error": None}
                    break

    # 4. Service payment extraction (bills, subscriptions, etc.)
    if not result["value"]:
        service_patterns = [
            r"(?i)(?:towards|for)\s+([A-Za-z\s]+\b(?:Bill|Payment|Recharge|Subscription))(?:\s+-\s+([A-Za-z\s]+))?",  # towards Electricity Bill - Provider
            r"(?i)(?:towards|for)\s+([A-Za-z\s]+(?:Bill|Payment|Recharge|Subscription))(?:\s+to|\s+for|\s+of)?\s+([A-Za-z\s]+)",  # for Mobile Bill Payment to Airtel
            r"(?i)(?:[A-Za-z\s]+(?:Bill|Payment|Recharge|Subscription))\s+-\s+([A-Za-z\s]+)",  # DTH Recharge - Tata Sky
            r"(?i)(?:payment|paid|transferred|sent)(?:\s+for)?\s+([A-Za-z\s]+(?:Bill|Invoice|Receipt|Statement|Dues|Fee|Fees))",  # payment for Electricity Bill
            r"(?i)(?:payment|paid|transferred|sent)(?:\s+for)?\s+([A-Za-z\s]+)\s+(?:Bill|Invoice|Receipt|Dues|Fee|Fees)"  # payment for College Fees
        ]
        
        for pattern in service_patterns:
            match = re.search(pattern, sms)
            if match:
                service = match.group(1).strip()
                # Check if there's a provider/company specified
                if match.lastindex > 1 and match.group(2):
                    provider = match.group(2).strip()
                    service = f"{service} - {provider}"
                
                result = {"value": service, "confidence": 0.8, "error": None}
                break

    # 5. Edge cases and mixed formats - combining merchant/person with UPI
    if not result["value"]:
        edge_patterns = [
            r"(?i)(?:to|2|sent to|paid to|payment to)\s+([^()]+)(?:\s*\(UPI ID:?\s*([a-zA-Z0-9._-]+@[a-zA-Z0-9._-]+)\))",  # to Name (UPI ID: user@bank)
            r"(?i)(?:to|2|sent to|paid to|payment to)\s+([^()]+)(?:\s+via|through|using)\s+UPI",  # to Name via UPI
            r"(?i)(?:to|2|sent to|paid to|payment to|for)\s+([A-Za-z\s]+(?:service|consultation|fee|invoice|subscription))",  # for Medical Consultation
            r"(?i)(?:to|2|sent to|paid to|payment to)\s+([^()]+)(?:\s+-\s+([A-Za-z\s]+))",  # to XYZ Corp - Invoice #12345
            r"(?i)(?:at|@)\s+([A-Za-z0-9\s]+)\s+(?:subscription|membership|recurring)"  # at NETFLIX subscription
        ]
        
        for pattern in edge_patterns:
            match = re.search(pattern, sms)
            if match:
                payee = match.group(1).strip()
                
                # Check if there's additional info to include
                if match.lastindex > 1 and match.group(2):
                    additional_info = match.group(2).strip()
                    # For UPI ID in parentheses
                    if '@' in additional_info:
                        payee = f"{payee} ({additional_info})"
                    else:
                        payee = f"{payee} - {additional_info}"
                
                result = {"value": payee, "confidence": 0.75, "error": None}
                break

    # 6. Bank and credit card related payments
    if not result["value"]:
        bank_payment_patterns = [
            r"(?i)(?:payment|paid)(?:\s+towards|\s+for)?\s+(?:your)?\s+([A-Za-z\s]+(?:Card|credit\s+card|loan|mortgage)(?:\s+Bill)?)",  # payment towards your Credit Card Bill
            r"(?i)(?:payment|paid)(?:\s+towards|\s+for)?\s+(?:your)?\s+([A-Za-z\s]+(?:EMI|Loan\s+EMI|Dues|Statement))",  # payment towards your Home Loan EMI
            r"(?i)(?:payment|paid)(?:\s+to)?\s+(?:your)?\s+([A-Za-z\s]+(?:Bank|Financial|Finance|Insurance)(?:\s+[A-Za-z\s]+)?)"  # payment to ICICI Home Finance
        ]
        
        for pattern in bank_payment_patterns:
            match = re.search(pattern, sms)
            if match:
                bank_payment = match.group(1).strip()
                result = {"value": bank_payment, "confidence": 0.8, "error": None}
                break

    # If payee is still not found, set the error
    if not result["value"]:
        result["error"] = "Payee not found"
    
    return result

def extract_account_details(sms: str) -> tuple:
    """Extract account details (from and to) from SMS message."""
    account_from = {"value": None, "confidence": 0.0, "error": None}
    account_to = {"value": None, "confidence": 0.0, "error": None}

    # Enhanced account extraction patterns
    account_patterns = [
        r"(?:A\/C|A\/c|Acct|Card|account)?\s*(?:xx|x|XX|ending|[Ee]nding in)?\s*([xX\d]{4,})",
        r"[Aa](?:\/)?[Cc](?:count)?\s*(?:\w+\s*)?(?:no\.?)?\s*(?:xx|x|XX)?\s*([xX\d]{4,})",
        r"(?:acct|account|a\/c)[.\s]*(?:no\.?)?[.\s]*(?:xx|x|XX)?[.\s]*([xX\d]{4,})",
        r"(?:xx|XX)(\d{4,})"
    ]

    # First look for accounts with explicit role indicators
    from_account_match = re.search(r"(?i)from\s+(?:A\/C|A\/c|Acct|account)?\s*(?:xx|x|XX|ending)?\s*([xX\d]{4,})", sms)
    if from_account_match:
        account_from = {"value": from_account_match.group(1), "confidence": 0.95, "error": None}

    # Enhanced patterns for "account to" detection
    to_account_patterns = [
        r"(?i)to\s+(?:.*?)\s*\((?:A\/C|A\/c|Acct|account)?\s*(?:no\.?)?\s*(?:xx|x|XX|ending)?\s*([xX\d]{4,})\)",  # to Name (A/c XX1234)
        r"(?i)to\s+(?:A\/C|A\/c|Acct|account)?\s*(?:xx|x|XX|ending)?\s*([xX\d]{4,})",  # to A/c XX1234
        r"(?i)credited\s+to\s+(?:A\/C|A\/c|Acct|account)?\s*(?:no\.?)?\s*(?:xx|x|XX|ending)?\s*([xX\d]{4,})",  # credited to A/c XX1234
        r"(?i)transferred\s+to\s+(?:.*?)\s+(?:\()?(?:A\/C|A\/c|Acct|account)?\s*(?:no\.?)?\s*(?:xx|x|XX|ending)?\s*([xX\d]{4,})(?:\))?",  # transferred to Name A/c XX1234
        r"(?i)deposited\s+to\s+(?:your)?\s+(?:A\/C|A\/c|Acct|account)?\s*(?:no\.?)?\s*(?:xx|x|XX)?\s*([xX\d]{4,})",  # deposited to your A/c XX1234
        r"(?i)beneficiary\s+(?:A\/C|A\/c|Acct|account)?\s*(?:no\.?)?\s*(?:xx|x|XX)?\s*([xX\d]{4,})",  # beneficiary A/c XX1234
        r"(?i)to\s+(?:.*?)@(?:\w+)/([\d]{4,})",  # to name@bank/1234567890 (UPI format with embedded account)
        r"(?i)UPI[- ]P2A[- ](?:.*?)(?:to|a/c|account)[- ](\d{4,})",  # UPI P2A transfer to 1234567890
        r"(?i)UPI/([\d]{4,})/",  # UPI/1234567890/reference
        r"(?i)to\s+(?:.*?)\s+via\s+IMPS\s+Ref:\s+(\d{4,})",  # to Name via IMPS Ref: 123456
        r"(?i)to\s+(?:.*?)\s+using\s+NEFT\s+Ref:\s+(\d{4,})",  # to Name using NEFT Ref: 123456
        r"(?i)to\s+(?:.*?)\s+via\s+RTGS\s+Ref:\s+(\d{4,})"  # to Name via RTGS Ref: 123456
    ]

    # Try each "to account" pattern
    for pattern in to_account_patterns:
        to_account_match = re.search(pattern, sms)
        if to_account_match:
            account_to = {"value": to_account_match.group(1), "confidence": 0.95, "error": None}
            break

    # If from_account not found yet, try to find a general account number based on transaction type
    if not account_from["value"]:
        for pattern in account_patterns:
            account_match = re.search(pattern, sms)
            if account_match:
                account_number = account_match.group(1)
                if re.search(r"(?i)\b(debited|spent|paid|sent|withdrawn|withdrawal|purchase|payment)\b", sms):
                    account_from = {"value": account_number, "confidence": 0.8, "error": None}
                break

    # If to_account not found yet, try to find a general account number based on transaction type
    if not account_to["value"]:
        for pattern in account_patterns:
            account_match = re.search(pattern, sms)
            if account_match:
                account_number = account_match.group(1)
                if re.search(r"(?i)\b(credited|received|deposit|salary|credit|cash\s+in)\b", sms):
                    account_to = {"value": account_number, "confidence": 0.8, "error": None}
                break

    # Set errors if not found
    if not account_from["value"]:
        account_from["error"] = "Source account not found"

    if not account_to["value"]:
        account_to["error"] = "Destination account not found"

    return account_from, account_to

def extract_transaction_details(sms: str) -> dict:
    """Extract transaction details from an SMS message.
    
    Args:
        sms: The SMS message text to extract transaction details from.
        
    Returns:
        dict: A dictionary containing the extracted transaction details with their confidence scores.
    """
    result = {
        "amount": {"value": None, "confidence": 0.0, "error": None},
        "date": {"value": None, "confidence": 0.0, "error": None},
        "payee": {"value": None, "confidence": 0.0, "error": None},
        "transaction_type": {"value": None, "confidence": 0.0, "error": None},
        "account_from": {"value": None, "confidence": 0.0, "error": None},
        "account_to": {"value": None, "confidence": 0.0, "error": None},
        "bank": {"value": None, "confidence": 0.0, "error": None}
    }
    
    # Extract each component using the helper functions
    result["bank"] = extract_bank(sms)
    result["amount"] = extract_amount(sms)
    result["date"] = extract_date(sms)
    result["transaction_type"] = extract_transaction_type(sms)
    result["payee"] = extract_payee(sms)
    
    # Extract account details (returns a tuple of from and to)
    account_from, account_to = extract_account_details(sms)
    result["account_from"] = account_from
    result["account_to"] = account_to
    
    return result
