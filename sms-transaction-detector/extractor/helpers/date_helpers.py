import re
from datetime import datetime, timedelta

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