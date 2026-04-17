# Helper functions
import os

def get_env(key, default=None):
    """Get environment variable from Streamlit secrets or os.getenv()
    
    Tries Streamlit secrets first (for Cloud deployment),
    then falls back to os.getenv() (for local development).
    """
    try:
        import streamlit as st
        value = st.secrets.get(key)
        if value:
            return value
    except (ImportError, AttributeError):
        pass
    
    return os.getenv(key, default)

def format_currency(amount):
    """Format amount as currency."""
    return f"${amount:,.2f}"

def calculate_percentage(part, total):
    """Calculate percentage safely."""
    if total == 0:
        return 0
    return (part / total) * 100

def get_month_name(month_num):
    """Get month name from number."""
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]
    return months[month_num - 1] if 1 <= month_num <= 12 else "Unknown"