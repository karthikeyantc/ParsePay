import re

def match_amount_pattern(sms: str) -> tuple:
    """Helper function to match amount pattern in SMS."""
    amount_match = re.search(r"(?i)(?:rs\.?|inr)\s?([0-9,]+(?:\.[0-9]{1,2})?)(?:\s*\/\-)?", sms)
    if amount_match:
        amount_value = amount_match.group(1).replace(",", "")
        return amount_value, 1.0
    return None, 0.0