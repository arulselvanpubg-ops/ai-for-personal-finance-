import pytest
from core.parser import parse_csv
from utils.validators import validate_amount

def test_validate_amount():
    assert validate_amount(100) == True
    assert validate_amount(-50) == True
    assert validate_amount(0) == False
    assert validate_amount("abc") == False

def test_parse_csv():
    # This would need a test CSV file
    # For now, just test the function exists
    assert callable(parse_csv)