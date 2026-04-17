import re


def validate_amount(amount):
    """Validate transaction amount."""
    try:
        amt = float(amount)
        return amt != 0
    except (TypeError, ValueError):
        return False


def validate_date(date_str):
    """Validate date string."""
    from datetime import datetime

    try:
        datetime.fromisoformat(str(date_str))
        return True
    except (TypeError, ValueError):
        return False


def sanitize_input(text, max_length=500):
    """Sanitize user input."""
    if text is None:
        return ""
    return str(text).strip()[:max_length]


def validate_email(email):
    """Validate email format with a lightweight check."""
    if not email:
        return False
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(email).strip()))


def normalize_email(email):
    return sanitize_input(email, max_length=255).lower()


def validate_password(password, min_length=8):
    return bool(password) and len(password) >= min_length


def validate_name(name, min_length=2):
    cleaned = sanitize_input(name, max_length=80)
    return len(cleaned) >= min_length
