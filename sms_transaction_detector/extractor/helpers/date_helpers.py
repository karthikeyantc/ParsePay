import re
import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
import pytz
import calendar

def match_date_patterns(sms: str, date_patterns: list, today: datetime.datetime) -> tuple:
    """Helper function to match date patterns in SMS."""
    for pattern, fmt in date_patterns:
        match = re.search(pattern, sms, re.IGNORECASE)
        if match:
            try:
                if "-%b-" in fmt:
                    day, month_abbr, year = match.groups()
                    month_dict = {
                        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
                    }
                    month = month_dict.get(month_abbr.lower(), '01')
                    dt_str = f"{day}-{month}-{year}"
                    if len(year) == 2:
                        year_prefix = "20" if int(year) < 50 else "19"
                        dt = datetime.datetime.strptime(f"{day}-{month}-{year_prefix}{year}", "%d-%m-%Y")
                    else:
                        dt = datetime.datetime.strptime(dt_str, "%d-%m-%Y")
                elif "%B" in fmt:
                    groups = match.groups()
                    if "%d %B %Y" == fmt:
                        day, month_name, year = groups
                    else:
                        month_name, day, year = groups
                    day = re.sub(r'(?:st|nd|rd|th)', '', day)
                    dt_str = f"{day} {month_name} {year}"
                    dt = datetime.datetime.strptime(dt_str, "%d %B %Y")
                else:
                    dt_str = "-".join(match.groups())
                    dt = datetime.datetime.strptime(dt_str, fmt)
                if dt.year < 2000:
                    dt = dt.replace(year=dt.year + 2000)
                return dt.strftime("%Y-%m-%d"), 0.95
            except (ValueError, KeyError):
                continue
    return None, 0.0

def match_relative_dates(sms: str, today: datetime.datetime) -> tuple:
    """Helper function to match relative dates in SMS."""
    if re.search(r'\btoday\b', sms, re.IGNORECASE):
        return today.strftime("%Y-%m-%d"), 0.85
    elif re.search(r'\byesterday\b', sms, re.IGNORECASE):
        yesterday = today - datetime.timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d"), 0.85
    elif re.search(r'\btomorrow\b', sms, re.IGNORECASE):
        tomorrow = today + datetime.timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d"), 0.85
    return None, 0.0

def extract_transaction_context(sms: str) -> dict:
    """Extract context from SMS to help with date inference."""
    context = {
        'is_service_payment': False,
        'contains_reference': False,
        'contains_bill': False,
        'contains_subscription': False
    }
    
    service_terms = ['bill', 'recharge', 'payment', 'subscription', 'utility', 'electricity', 
                     'broadband', 'mobile', 'dth', 'gas', 'water', 'landline', 'insurance']
    
    for term in service_terms:
        if re.search(r'\b' + re.escape(term) + r'\b', sms, re.IGNORECASE):
            context['is_service_payment'] = True
            break
    
    if re.search(r'\b(?:ref|reference)\b[^a-zA-Z0-9]*[a-zA-Z0-9]+', sms, re.IGNORECASE):
        context['contains_reference'] = True
    
    if re.search(r'\bbill\b', sms, re.IGNORECASE):
        context['contains_bill'] = True
    
    if re.search(r'\bsubscription\b', sms, re.IGNORECASE):
        context['contains_subscription'] = True
    
    return context

def infer_date_from_context(sms: str, context: dict, now: datetime.datetime) -> tuple:
    """Infer the date from context when explicit date is missing."""
    # For service payments without dates, assume it's recent (today or yesterday)
    if context['is_service_payment']:
        # Check if it contains a bill period
        bill_period_match = re.search(r'(?:bill|payment)\s+(?:for|of)\s+(?:month|period)?\s*(?:of)?\s*([a-zA-z]{3,9})(?:[,-]?\s*(\d{2,4}))?', 
                                      sms, re.IGNORECASE)
        if bill_period_match:
            try:
                month_name = bill_period_match.group(1)
                year = bill_period_match.group(2) if bill_period_match.groups()[1] else str(now.year)
                if len(year) == 2:
                    year = "20" + year
                
                # Map month name to number
                month_number = None
                for i, month in enumerate(calendar.month_name[1:], 1):
                    if month_name.lower() in month.lower():
                        month_number = i
                        break
                
                if month_number:
                    # Assume bill payment is for last month
                    inferred_date = datetime.date(int(year), month_number, 1)
                    # Bills are typically paid at start of next month
                    if now.month == month_number:
                        inferred_date = now.date()
                    else:
                        inferred_date = datetime.date(now.year, now.month, now.day)
                    return inferred_date.strftime("%Y-%m-%d"), 0.65
            except:
                pass
        
        # For subscription or recurring payments, assume it's today
        if context['contains_subscription']:
            return now.strftime("%Y-%m-%d"), 0.6
        
        # Otherwise, for service payments with references, assume today or yesterday
        if context['contains_reference']:
            # Bias towards today
            return now.strftime("%Y-%m-%d"), 0.55
    
    # Default case - no context clues, return None
    return None, 0.0

def parse_date_with_custom_formats(date_text: str, now: datetime.datetime) -> tuple:
    """Try to parse dates with custom formats not handled well by dateutil."""
    
    # Define custom patterns with their format
    custom_patterns = [
        # DD-MM-YY with various separators
        (r'(\d{1,2})[-./](\d{1,2})[-./](\d{2})\b', "%d-%m-%y"),
        
        # DD-MM-YYYY with various separators
        (r'(\d{1,2})[-./](\d{1,2})[-./](20\d{2})\b', "%d-%m-%Y"),
        
        # YYYY-MM-DD format (ISO)
        (r'(20\d{2})[-./](\d{1,2})[-./](\d{1,2})\b', "%Y-%m-%d"),
        
        # DD-MMM-YY with abbreviated month
        (r'(\d{1,2})[-./\s]([A-Za-z]{3})[-./\s](\d{2})\b', "%d-%b-%y"),
        
        # DD-MMM-YYYY with abbreviated month
        (r'(\d{1,2})[-./\s]([A-Za-z]{3})[-./\s](20\d{2})\b', "%d-%b-%Y"),
        
        # Month DD, YYYY format
        (r'([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(20\d{2})', "%B %d %Y"),
        
        # DD Month, YYYY format
        (r'(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9}),?\s*(20\d{2})', "%d %B %Y"),
        
        # DD Month format (without year)
        (r'(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\b(?!\s*\d)', "%d %B"),
        
        # DD-MM format (without year)
        (r'(\d{1,2})[-./](\d{1,2})\b(?!\s*\d)', "%d-%m"),
        
        # Month DD format (without year)
        (r'([A-Za-z]{3,9})\s+(\d{1,2})(?:st|nd|rd|th)?\b(?!\s*\d)', "%B %d"),
    ]
    
    for pattern, fmt in custom_patterns:
        match = re.search(pattern, date_text, re.IGNORECASE)
        if match:
            try:
                groups = match.groups()
                
                # Handle abbreviated month names
                if "%b" in fmt:
                    month_abbr = groups[1].lower()
                    month_dict = {
                        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
                        'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
                        'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
                    }
                    if month_abbr not in month_dict:
                        # Try to match partial month names
                        for full_month, month_num in month_dict.items():
                            if month_abbr in full_month:
                                month_abbr = full_month
                                break
                    
                    month = month_dict.get(month_abbr, '01')
                    day = groups[0]
                    
                    # Normalize day
                    if len(day) == 1:
                        day = '0' + day
                    
                    # Handle year (with or without century)
                    if len(groups) > 2 and groups[2]:
                        year = groups[2]
                        if len(year) == 2:
                            year_prefix = "20" if int(year) < 50 else "19"
                            year = year_prefix + year
                    else:
                        # If no year in pattern, use current year
                        year = str(now.year)
                    
                    date_str = f"{year}-{month}-{day}"
                    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # Handle dates that might be in the future
                    if date_obj.date() > now.date() + datetime.timedelta(days=7):
                        # If more than a week in the future, assume it's for last year
                        date_obj = date_obj.replace(year=date_obj.year - 1)
                    
                    return date_obj.strftime("%Y-%m-%d"), 0.85
                
                # Handle full month names
                elif "%B" in fmt:
                    if len(groups) == 3:  # Full date with year
                        # Format depends on pattern
                        if fmt == "%B %d %Y":  # Month DD, YYYY
                            month_name, day, year = groups
                        else:  # DD Month, YYYY
                            day, month_name, year = groups
                    else:  # Date without year
                        if fmt == "%B %d":  # Month DD
                            month_name, day = groups
                        else:  # DD Month
                            day, month_name = groups
                        year = str(now.year)
                    
                    # Remove ordinal indicators
                    day = re.sub(r'(?:st|nd|rd|th)', '', day)
                    
                    # Try to match month name to calendar months
                    month_number = None
                    for i, month in enumerate(calendar.month_name[1:], 1):
                        if month_name.lower() in month.lower():
                            month_number = i
                            break
                    
                    if not month_number:
                        # Try abbreviated month names as fallback
                        for i, month in enumerate(calendar.month_abbr[1:], 1):
                            if month_name.lower() in month.lower():
                                month_number = i
                                break
                    
                    if month_number:
                        # Normalize day
                        if len(day) == 1:
                            day = '0' + day
                            
                        # Normalize month
                        month = str(month_number).zfill(2)
                        
                        # Create date object
                        date_str = f"{year}-{month}-{day}"
                        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                        
                        # Handle dates that might be in the future
                        if date_obj.date() > now.date() + datetime.timedelta(days=7):
                            # If more than a week in the future, assume it's for last year
                            date_obj = date_obj.replace(year=date_obj.year - 1)
                        
                        return date_obj.strftime("%Y-%m-%d"), 0.85
                
                # Handle numeric format cases
                else:
                    # Extract parts based on format
                    if fmt == "%d-%m-%y" or fmt == "%d-%m-%Y":  # DD-MM-YY(YY) format
                        day, month, year = groups
                        if len(year) == 2:
                            year_prefix = "20" if int(year) < 50 else "19"
                            year = year_prefix + year
                    elif fmt == "%Y-%m-%d":  # YYYY-MM-DD format
                        year, month, day = groups
                    elif fmt == "%d-%m":  # DD-MM format (no year)
                        day, month = groups
                        year = str(now.year)
                    
                    # Normalize day and month
                    day = day.zfill(2)
                    month = month.zfill(2)
                    
                    # Create date object
                    date_str = f"{year}-{month}-{day}"
                    date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    
                    # Handle dates that might be in the future
                    if date_obj.date() > now.date() + datetime.timedelta(days=7):
                        # If more than a week in the future, assume it's for last year
                        date_obj = date_obj.replace(year=date_obj.year - 1)
                    
                    return date_obj.strftime("%Y-%m-%d"), 0.85
            except Exception as e:
                continue
    
    return None, 0.0

def extract_date(text):
    """
    Extract transaction date from SMS
    Returns a tuple of (date_str, confidence_score)
    
    Enhanced version with improved pattern matching, relative date handling,
    and context-based inference for service payments
    """
    # Get current date for reference
    now = datetime.datetime.now()
    ist_timezone = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.datetime.now(ist_timezone)
    
    # Common date patterns in SMS with explicit date indicators
    explicit_patterns = [
        # Common date patterns with "on", "dated", "date", etc.
        r'(?:on|dated|date|as\s+of)[^a-zA-Z0-9]*(\d{1,2}[/-\.]\d{1,2}[/-\.]\d{2,4})',
        r'(?:on|dated|date|as\s+of)[^a-zA-Z0-9]*(\d{1,2}(?:st|nd|rd|th)?[/-\.\s]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[/-\.\s]+\d{2,4})',
        r'(?:on|dated|date|as\s+of)[^a-zA-Z0-9]*(\d{1,2}(?:st|nd|rd|th)?[/-\.\s]+(?:January|February|March|April|May|June|July|August|September|October|November|December)[/-\.\s]+\d{2,4})',
        r'(?:on|dated|date|as\s+of)[^a-zA-Z0-9]*(\d{4}[/-\.]\d{1,2}[/-\.]\d{1,2})',
        r'(?:on|dated|date|as\s+of)[^a-zA-Z0-9]*(\d{1,2}(?:st|nd|rd|th)?[/-\.\s]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)',
        r'(?:on|dated|date|as\s+of)[^a-zA-Z0-9]*(\d{1,2}(?:st|nd|rd|th)?[/-\.\s]+(?:January|February|March|April|May|June|July|August|September|October|November|December))',
        
        # Relative dates
        r'(?:on|dated|date|as\s+of)[^a-zA-Z0-9]*(today)',
        r'(?:on|dated|date|as\s+of)[^a-zA-Z0-9]*(yesterday)',
    ]
    
    # Date patterns without explicit date indicators
    implicit_patterns = [
        # DD-MM-YYYY or DD/MM/YYYY formats without indicators
        r'(\d{1,2}[/-\.]\d{1,2}[/-\.]\d{4})',
        r'(\d{1,2}[/-\.]\d{1,2}[/-\.]2\d{1})', # 2-digit year with 2 prefix (like 21)
        
        # YYYY-MM-DD formats (ISO)
        r'(20\d{2}[/-\.]\d{1,2}[/-\.]\d{1,2})',
        
        # DD-MMM-YYYY formats
        r'(\d{1,2}(?:st|nd|rd|th)?[/-\.\s]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[/-\.\s]+\d{4})',
        r'(\d{1,2}(?:st|nd|rd|th)?[/-\.\s]+(?:January|February|March|April|May|June|July|August|September|October|November|December)[/-\.\s]+\d{4})',
        
        # Month DD, YYYY formats
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[/-\.\s]+\d{1,2}(?:st|nd|rd|th)?[/-\.\s,]+\d{4})',
        r'((?:January|February|March|April|May|June|July|August|September|October|November|December)[/-\.\s]+\d{1,2}(?:st|nd|rd|th)?[/-\.\s,]+\d{4})',
        
        # Month DD formats (without year)
        r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[/-\.\s]+\d{1,2}(?:st|nd|rd|th)?)',
        r'((?:January|February|March|April|May|June|July|August|September|October|November|December)[/-\.\s]+\d{1,2}(?:st|nd|rd|th)?)',
        
        # DD Month formats (without year)
        r'(\d{1,2}(?:st|nd|rd|th)?[/-\.\s]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*)',
        r'(\d{1,2}(?:st|nd|rd|th)?[/-\.\s]+(?:January|February|March|April|May|June|July|August|September|October|November|December))',
        
        # Abbreviated formats
        r'(\d{1,2}[/-]\d{1,2})',  # DD-MM or MM-DD (common in SMS)
    ]
    
    # Combined patterns for timestamp date-time formats
    timestamp_patterns = [
        # Date + Time patterns
        r'(\d{1,2}[/-\.]\d{1,2}[/-\.]\d{2,4})[^a-zA-Z0-9]*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[aApP][mM])?)',
        r'(\d{4}[/-\.]\d{1,2}[/-\.]\d{1,2})[^a-zA-Z0-9]*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[aApP][mM])?)',
        r'(\d{1,2}(?:st|nd|rd|th)?[/-\.\s]+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[/-\.\s]+\d{2,4})[^a-zA-Z0-9]*(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[aApP][mM])?)',
    ]
    
    # Check context of the SMS for better date inference
    context = extract_transaction_context(text)
    
    # 1. First, try to find explicit date indicators with high confidence
    for pattern in explicit_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_text = match.group(1).strip()
            
            # Handle relative dates
            if date_text.lower() == 'today':
                return now_ist.strftime('%Y-%m-%d'), 0.9
            elif date_text.lower() == 'yesterday':
                yesterday = now_ist - datetime.timedelta(days=1)
                return yesterday.strftime('%Y-%m-%d'), 0.9
                
            # Try custom format parsing for better accuracy
            date_str, confidence = parse_date_with_custom_formats(date_text, now_ist)
            if date_str:
                return date_str, confidence
                
            # Fallback to dateutil parser for flexibility
            try:
                parsed_date = parser.parse(date_text, fuzzy=True)
                
                # Fix years that might be parsed incorrectly
                if parsed_date.year < 2000:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                
                # Handle future dates (likely parsing errors)
                if parsed_date.date() > now.date() + datetime.timedelta(days=30):
                    # If more than a month in the future, assume it's this or last year
                    parsed_date = parsed_date.replace(year=now.year)
                    if parsed_date.date() > now.date() + datetime.timedelta(days=30):
                        parsed_date = parsed_date.replace(year=now.year - 1)
                
                return parsed_date.strftime('%Y-%m-%d'), 0.85
            except:
                pass
    
    # 2. Check for timestamp patterns which often contain both date and time
    for pattern in timestamp_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_text = match.group(1).strip()
            
            # Try custom format parsing for better accuracy
            date_str, confidence = parse_date_with_custom_formats(date_text, now_ist)
            if date_str:
                return date_str, confidence + 0.05  # Slightly higher confidence for timestamps
                
            # Fallback to dateutil parser
            try:
                parsed_date = parser.parse(date_text, fuzzy=True)
                
                # Fix years that might be parsed incorrectly
                if parsed_date.year < 2000:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                
                # Handle future dates (likely parsing errors)
                if parsed_date.date() > now.date() + datetime.timedelta(days=30):
                    # If more than a month in the future, assume it's this or last year
                    parsed_date = parsed_date.replace(year=now.year)
                    if parsed_date.date() > now.date() + datetime.timedelta(days=30):
                        parsed_date = parsed_date.replace(year=now.year - 1)
                
                return parsed_date.strftime('%Y-%m-%d'), 0.85
            except:
                pass
    
    # 3. Try implicit date patterns (without explicit indicators)
    for pattern in implicit_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_text = match.group(1).strip()
            
            # Try custom format parsing for better accuracy
            date_str, confidence = parse_date_with_custom_formats(date_text, now_ist)
            if date_str:
                return date_str, confidence - 0.05  # Slightly lower confidence for implicit dates
                
            # Fallback to dateutil parser
            try:
                parsed_date = parser.parse(date_text, fuzzy=True)
                
                # Fix years that might be parsed incorrectly
                if parsed_date.year < 2000:
                    parsed_date = parsed_date.replace(year=parsed_date.year + 2000)
                
                # For two-digit year formats, handle future dates
                if len(date_text) <= 10 and parsed_date.date() > now.date() + datetime.timedelta(days=30):
                    parsed_date = parsed_date.replace(year=now.year)
                    if parsed_date.date() > now.date() + datetime.timedelta(days=30):
                        parsed_date = parsed_date.replace(year=now.year - 1)
                
                return parsed_date.strftime('%Y-%m-%d'), 0.75
            except:
                pass
    
    # 4. If still no date, try to infer from context
    if context['is_service_payment']:
        date_str, confidence = infer_date_from_context(text, context, now_ist)
        if date_str:
            return date_str, confidence
    
    # 5. Last resort: Look for time references that might indicate today/yesterday
    time_match = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?(?:\s*[aApP][mM])?)', text, re.IGNORECASE)
    if time_match:
        # If we find a time but no date, assume it's today
        try:
            time_str = time_match.group(1)
            parsed_time = parser.parse(time_str).time()
            
            # If the time is in the future today, it might be from yesterday or today
            current_time = now.time()
            if parsed_time > current_time and (parsed_time.hour - current_time.hour) > 3:
                # If it's more than 3 hours in the future, likely yesterday
                date_str = (now - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            else:
                date_str = now.strftime('%Y-%m-%d')
            
            return date_str, 0.5  # Low confidence for inferred dates from time
        except:
            pass
    
    # If all else fails, return None
    return None, 0.0

def normalize_date(date_str):
    """Normalize date to YYYY-MM-DD format."""
    if not date_str:
        return None
        
    # Clean up 'on ' prefix if present
    if date_str.startswith('on '):
        date_str = date_str[3:]
    
    # Try to parse the date with dateutil
    try:
        parsed_date = parser.parse(date_str, fuzzy=True)
        return parsed_date.strftime('%Y-%m-%d')
    except:
        pass
    
    # If parsing fails, return original
    return date_str