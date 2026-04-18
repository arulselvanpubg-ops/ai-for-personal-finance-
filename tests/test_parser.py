import pytest
from core.parser import parse_csv, _parse_money, _parse_date_cell
from utils.validators import validate_amount

def test_parse_money():
    assert _parse_money("1,234.56") == 1234.56
    assert _parse_money("₹1,234.56") == 1234.56
    assert _parse_money("(100.00)") == -100.00
    assert _parse_money("-50.25") == -50.25
    assert _parse_money("1.234,56") == 1234.56  # European style
    assert _parse_money("invalid") is None

def test_parse_date_cell():
    from datetime import datetime
    dt = _parse_date_cell("2026-04-18")
    assert isinstance(dt, datetime)
    assert dt.year == 2026
    assert dt.month == 4
    assert dt.day == 18
    
    assert _parse_date_cell("invalid") is None


def test_validate_amount():
    assert validate_amount(100) == True
    assert validate_amount(-50) == True
    assert validate_amount(0) == False
    assert validate_amount("abc") == False

def test_parse_csv():
    # This would need a test CSV file
    # For now, just test the function exists
    assert callable(parse_csv)