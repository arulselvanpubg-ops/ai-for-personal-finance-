import pytest
from utils.validators import (
    validate_amount,
    validate_date,
    sanitize_input,
    validate_email,
    validate_password,
    validate_name
)

def test_validate_amount():
    assert validate_amount(100) is True
    assert validate_amount(-50.5) is True
    assert validate_amount("123.45") is True
    assert validate_amount(0) is False
    assert validate_amount("abc") is False
    assert validate_amount(None) is False

def test_validate_date():
    assert validate_date("2026-04-18") is True
    assert validate_date("2026-04-18T14:00:00") is True
    assert validate_date("not-a-date") is False
    assert validate_date(None) is False

def test_sanitize_input():
    assert sanitize_input("  hello world  ") == "hello world"
    assert sanitize_input("a" * 1000, max_length=10) == "aaaaaaaaaa"
    assert sanitize_input(None) == ""

def test_validate_email():
    assert validate_email("test@example.com") is True
    assert validate_email("user.name+tag@domain.co.uk") is True
    assert validate_email("invalid-email") is False
    assert validate_email("@no-user.com") is False
    assert validate_email("no-domain@") is False
    assert validate_email(None) is False

def test_validate_password():
    assert validate_password("password123") is True
    assert validate_password("short") is False
    assert validate_password("") is False
    assert validate_password(None) is False

def test_validate_name():
    assert validate_name("John Doe") is True
    assert validate_name("A") is False
    assert validate_name("   ") is False
    assert validate_name(None) is False
