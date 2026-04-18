import pytest
from unittest.mock import MagicMock, patch
from ai.categorizer import TransactionCategorizer, categorize_transaction

@pytest.fixture
def mock_categorizer():
    with patch("ai.categorizer.InferenceClient") as mock_client:
        # Mock HF API response
        mock_instance = mock_client.return_value
        mock_instance.zero_shot_classification.return_value = [{"label": "Food & Dining"}]
        
        # Force use_api to True for testing API path
        with patch("ai.categorizer.HF_API_KEY", "fake_key"):
            cat = TransactionCategorizer()
            cat.use_api = True
            cat.client = mock_instance
            return cat

def test_categorize_keyword():
    cat = TransactionCategorizer()
    cat.use_api = False
    
    assert cat.categorize("Grocery shopping at Walmart") == "Food & Dining"
    assert cat.categorize("Uber ride to office") == "Transportation"
    assert cat.categorize("Salary deposit") == "Income"
    assert cat.categorize("Unknown stuff") == "Other"

def test_categorize_api(mock_categorizer):
    result = mock_categorizer.categorize("Some random description")
    assert result == "Food & Dining"
    mock_categorizer.client.zero_shot_classification.assert_called_once()

def test_bulk_categorize(mock_categorizer):
    descriptions = ["Burger King", "Uber", "Burger King"]
    # Mocking keyword match for Burger King to fail so it hits API
    # Actually, Burger King has 'burger' which matches Food & Dining keywords.
    # Let's use something unique.
    
    with patch.object(mock_categorizer, "_categorize_keyword", return_value="Other"):
        cats, hf_calls = mock_categorizer.bulk_categorize_for_import(descriptions)
        
        assert len(cats) == 3
        assert cats[0] == "Food & Dining"
        assert cats[2] == "Food & Dining" # Should be same as 0
        assert hf_calls == 2 # "Burger King" and "Uber" are unique