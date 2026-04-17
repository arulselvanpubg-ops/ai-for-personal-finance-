# Validation helpers
def validate_amount(amount):
    """Validate transaction amount."""
    try:
        amt = float(amount)
        return amt != 0
    except:
        return False

def validate_date(date_str):
    """Validate date string."""
    from datetime import datetime
    try:
        datetime.fromisoformat(date_str)
        return True
    except:
        return False

def sanitize_input(text):
    """Sanitize user input."""
    if not text:
        return ""
    return str(text).strip()[:500]  # Limit length