import re
import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
import pytz

def match_date_patterns(sms: str, date_patterns: list, today: datetime) -> tuple:
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
                        dt = datetime.strptime(f"{day}-{month}-{year_prefix}{year}", "%d-%m-%Y")
                    else:
                        dt = datetime.strptime(dt_str, "%d-%m-%Y")
                elif "%B" in fmt:
                    groups = match.groups()
                    if "%d %B %Y" == fmt:
                        day, month_name, year = groups
                    else:
                        month_name, day, year = groups
                    day = re.sub(r'(?:st|nd|rd|th)', '', day)
                    dt_str = f"{day} {month_name} {year}"
                    dt = datetime.strptime(dt_str, "%d %B %Y")
                else:
                    dt_str = "-".join(match.groups())
                    dt = datetime.strptime(dt_str, fmt)
                if dt.year < 2000:
                    dt = dt.replace(year=dt.year + 2000)
                return dt.strftime("%Y-%m-%d"), 0.95
            except (ValueError, KeyError):
                continue
    return None, 0.0

def match_relative_dates(sms: str, today: datetime) -> tuple:
    """Helper function to match relative dates in SMS."""
    if re.search(r'\btoday\b', sms, re.IGNORECASE):
        return today.strftime("%Y-%m-%d"), 0.85
    elif re.search(r'\byesterday\b', sms, re.IGNORECASE):
        yesterday = today - timedelta(days=1)
        return yesterday.strftime("%Y-%m-%d"), 0.85
    elif re.search(r'\btomorrow\b', sms, re.IGNORECASE):
        tomorrow = today + timedelta(days=1)
        return tomorrow.strftime("%Y-%m-%d"), 0.85
    return None, 0.0

def extract_date(text):
    """
    Extract transaction date from SMS
    Returns a tuple of (date_str, confidence_score)
    
    Enhanced version with improved pattern matching and relative date handling
    """
    # Get current date for reference
    now = datetime.datetime.now()
    ist_timezone = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.datetime.now(ist_timezone)
    
    # Common date patterns in SMS
    patterns = [
        # DD-MM-YYYY or DD/MM/YYYY formats
        r'(?:on|dated|date)[^a-zA-Z0-9]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
        
        # DD-MMM-YYYY formats
        r'(\d{1,2}[/-][A-Za-z]{3,}[/-]\d{2,4})',
        r'(\d{1,2}\s+[A-Za-z]{3,}\s+\d{2,4})',
        
        # Today, yesterday references
        r'(?:on|dated|date)[^a-zA-Z0-9]*(today)',
        r'(?:on|dated|date)[^a-zA-Z0-9]*(yesterday)',
        
        # Time references that can help determine date
        r'(\d{1,2}:\d{2}(?:\s*[ap]m)?)[^a-zA-Z0-9]*(?:today|yesterday|on\s+\d{1,2}[/-]\d{1,2})',
        
        # Timestamps in common formats
        r'(?:on|at)[^a-zA-Z0-9]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s+\d{1,2}:\d{2}(?:\s*[ap]m)?)',
    ]
    
    date_str = None
    confidence = 0.0
    
    # Try the patterns
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            date_str = match.group(1).strip()
            confidence = 0.7  # Base confidence
            
            # Handle relative dates
            if date_str.lower() == 'today':
                date_str = now_ist.strftime('%d-%m-%Y')
                confidence = 0.9
            elif date_str.lower() == 'yesterday':
                yesterday = now_ist - datetime.timedelta(days=1)
                date_str = yesterday.strftime('%d-%m-%Y')
                confidence = 0.9
            
            # Boost confidence for clear date patterns
            if re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', date_str):
                confidence = 0.85
            
            break
    
    # If no date found with patterns, try to extract using dateutil parser
    if not date_str:
        try:
            # Look for time patterns that might indicate a transaction
            time_match = re.search(r'(\d{1,2}:\d{2}(?:\s*[ap]m)?)', text, re.IGNORECASE)
            if time_match:
                # If we find a time but no date, assume it's today or recent
                time_str = time_match.group(1)
                try:
                    # Parse the time
                    parsed_time = parser.parse(time_str)
                    
                    # If the time is in the future today, it's likely from yesterday
                    if parsed_time.time() > now.time():
                        date_str = (now - datetime.timedelta(days=1)).strftime('%d-%m-%Y')
                    else:
                        date_str = now.strftime('%d-%m-%Y')
                    
                    confidence = 0.6  # Lower confidence for inferred dates
                except:
                    pass
        except Exception as e:
            # If dateutil parser fails, we'll return None
            pass
    
    # If we found a date string but it's not in a standard format, try to normalize it
    if date_str and not re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', date_str):
        try:
            parsed_date = parser.parse(date_str, fuzzy=True)
            
            # If the year is far in the future, it's likely a misinterpretation 
            # (common with 2-digit years), adjust to recent past
            if parsed_date.year > now.year + 1:
                parsed_date = parsed_date.replace(year=parsed_date.year - 100)
            
            # Format consistently as DD-MM-YYYY
            date_str = parsed_date.strftime('%d-%m-%Y')
            
            # Slightly reduce confidence due to normalization
            confidence = max(0.5, confidence - 0.1)
        except:
            # If normalization fails, keep the original string
            pass
    
    return date_str, confidence

def normalize_date(date_str):
    """Normalize date to DD-MM-YY format."""
    if not date_str:
        return None
        
    # Clean up 'on ' prefix if present
    if date_str.startswith('on '):
        date_str = date_str[3:]
    
    # Handle different delimiters and formats...
    # This is a simplified version - full implementation would handle all formats
    
    return date_str