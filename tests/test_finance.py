import pytest
from unittest.mock import MagicMock, patch
from core.finance import calculate_financial_health_score, get_monthly_summary
from datetime import datetime

@pytest.fixture
def mock_transactions():
    return [
        {"amount": 5000, "category": "Salary", "date": datetime(2026, 4, 1)},
        {"amount": -1000, "category": "Rent", "date": datetime(2026, 4, 2)},
        {"amount": -500, "category": "Groceries", "date": datetime(2026, 4, 3)},
    ]

def test_calculate_financial_health_score(mock_transactions):
    with patch("core.finance.Transaction.find_by_date_range") as mock_find:
        mock_find.return_value = mock_transactions
        
        # income = 5000, expenses = 1500. ratio = 1500/5000 = 0.3
        # ratio <= 0.5 -> score = 100.0
        score = calculate_financial_health_score(2026, 4)
        assert score == 100.0

def test_calculate_financial_health_score_no_data():
    with patch("core.finance.Transaction.find_by_date_range") as mock_find:
        mock_find.return_value = []
        score = calculate_financial_health_score(2026, 4)
        assert score == 50.0

def test_get_monthly_summary(mock_transactions):
    with patch("core.finance.Transaction.find_by_date_range") as mock_find:
        mock_find.return_value = mock_transactions
        summary = get_monthly_summary(2026, 4)
        
        assert summary["income"] == 5000
        assert summary["expenses"] == 1500
        assert summary["net"] == 3500
        assert summary["categories"]["Salary"] == 5000
        assert summary["categories"]["Rent"] == 1000
        assert summary["categories"]["Groceries"] == 500