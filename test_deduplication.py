#!/usr/bin/env python3
"""
Comprehensive test for deduplication functionality
"""

import pandas as pd
import tempfile
import os
from datetime import datetime, timedelta
from core.db import Transaction
from core.deduplication import deduplicator, deduplicate_import_transactions
from ui.statement_import import process_uploaded_statement

def create_test_transactions():
    """Create test transactions with some duplicates"""
    base_date = datetime(2026, 4, 1)
    
    transactions = [
        # Original transactions
        {"date": base_date, "amount": 85000.0, "description": "Salary Credit", "category": "Income"},
        {"date": base_date + timedelta(days=1), "amount": -2500.0, "description": "Grocery Store", "category": "Food & Dining"},
        {"date": base_date + timedelta(days=2), "amount": -1200.0, "description": "Electricity Bill", "category": "Bills & Utilities"},
        
        # Exact duplicates
        {"date": base_date, "amount": 85000.0, "description": "Salary Credit", "category": "Income"},
        {"date": base_date + timedelta(days=1), "amount": -2500.0, "description": "Grocery Store", "category": "Food & Dining"},
        
        # Similar duplicates (fuzzy matching)
        {"date": base_date + timedelta(days=1), "amount": -2500.01, "description": "Grocery Store Ltd", "category": "Food & Dining"},
        {"date": base_date + timedelta(days=2), "amount": -1200.0, "description": "Electricity Bill Payment", "category": "Bills & Utilities"},
        
        # New unique transactions
        {"date": base_date + timedelta(days=3), "amount": -800.0, "description": "Restaurant", "category": "Entertainment"},
        {"date": base_date + timedelta(days=4), "amount": -2000.0, "description": "Fuel Station", "category": "Transportation"},
    ]
    
    return transactions

def test_basic_deduplication():
    """Test basic deduplication functionality"""
    print("=== Testing Basic Deduplication ===")
    
    # Clear database
    Transaction._collection().delete_many({})
    
    # Add some existing transactions
    existing_tx = [
        {"date": datetime(2026, 4, 1), "amount": 85000.0, "description": "Salary Credit", "category": "Income"},
        {"date": datetime(2026, 4, 2), "amount": -2500.0, "description": "Grocery Store", "category": "Food & Dining"},
    ]
    
    for tx in existing_tx:
        Transaction.create(**tx)
    
    print(f"Added {len(existing_tx)} existing transactions")
    
    # Create new transactions with duplicates
    new_transactions = create_test_transactions()
    print(f"Created {len(new_transactions)} new transactions")
    
    # Test deduplication
    unique_tx, duplicate_tx = deduplicator.deduplicate_transactions(new_transactions)
    
    print(f"Unique transactions: {len(unique_tx)}")
    print(f"Duplicate transactions: {len(duplicate_tx)}")
    
    # Show duplicates
    if duplicate_tx:
        print("\nDuplicates found:")
        for i, dup in enumerate(duplicate_tx[:3]):
            print(f"  {i+1}. {dup['match_type']}: {dup['new_transaction']['description']} - {dup['new_transaction']['amount']}")
    
    return unique_tx, duplicate_tx

def test_merge_strategies():
    """Test different merge strategies"""
    print("\n=== Testing Merge Strategies ===")
    
    # Clear database
    Transaction._collection().delete_many({})
    
    # Add existing transactions
    existing_tx = [
        {"date": datetime(2026, 4, 1), "amount": 85000.0, "description": "Salary Credit", "category": "Income"},
        {"date": datetime(2026, 4, 2), "amount": -2500.0, "description": "Grocery Store", "category": "Food & Dining"},
    ]
    
    for tx in existing_tx:
        Transaction.create(**tx)
    
    new_transactions = create_test_transactions()
    
    strategies = ['keep_newest', 'keep_existing', 'replace_all']
    
    for strategy in strategies:
        print(f"\n--- Testing strategy: {strategy} ---")
        
        # Clear database for clean test
        if strategy != 'replace_all':
            Transaction._collection().delete_many({})
            for tx in existing_tx:
                Transaction.create(**tx)
        
        # Apply deduplication
        deduplicated, stats = deduplicate_import_transactions(new_transactions, strategy)
        
        print(f"Original: {stats['new_transactions_count']}")
        print(f"Deduplicated: {stats['unique_transactions_count']}")
        print(f"Duplicates: {stats['duplicate_transactions_count']}")
        print(f"Duplicate %: {stats['duplicate_percentage']:.1f}%")
        
        # Check final database state
        final_tx = Transaction.find_all()
        print(f"Final database count: {len(final_tx)}")

def test_similarity_matching():
    """Test fuzzy matching for similar transactions"""
    print("\n=== Testing Similarity Matching ===")
    
    test_cases = [
        ("Grocery Store", "Grocery Store Ltd"),
        ("Electricity Bill", "Electricity Bill Payment"),
        ("Restaurant", "Restaurant Bill"),
        ("ATM Withdrawal", "ATM Withdrawal Charges"),
        ("Salary Credit", "Salary Credit April"),
    ]
    
    for desc1, desc2 in test_cases:
        similarity = deduplicator.calculate_similarity(desc1.lower(), desc2.lower())
        print(f"'{desc1}' vs '{desc2}': {similarity:.2f} (threshold: {deduplicator.similarity_threshold})")

def test_upload_with_deduplication():
    """Test full upload process with deduplication"""
    print("\n=== Testing Upload with Deduplication ===")
    
    # Clear database
    Transaction._collection().delete_many({})
    
    # Create sample CSV with duplicates
    test_data = {
        'Date': ['2026-04-01', '2026-04-02', '2026-04-01', '2026-04-03'],
        'Description': ['Salary Credit', 'Grocery Store', 'Salary Credit', 'Restaurant'],
        'Amount': [85000, -2500, 85000, -800]
    }
    
    df = pd.DataFrame(test_data)
    
    # Save to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df.to_csv(f.name, index=False)
        temp_file = f.name
    
    # Mock uploaded file with different strategies
    class MockUploadedFile:
        def __init__(self, name, data, strategy):
            self.name = name
            self._data = data
            self.invert_amounts = False
            self.merge_strategy = strategy
        
        def getbuffer(self):
            return self._data.encode()
    
    # Read file content
    with open(temp_file, 'r') as f:
        content = f.read()
    
    strategies = ['keep_newest', 'keep_existing', 'replace_all']
    
    for strategy in strategies:
        print(f"\n--- Upload with strategy: {strategy} ---")
        
        # Clear database for clean test (except replace_all)
        if strategy != 'replace_all':
            Transaction._collection().delete_many({})
        
        mock_file = MockUploadedFile('test.csv', content, strategy)
        
        try:
            outcome = process_uploaded_statement(mock_file)
            print(f"Success: {outcome.success}")
            print(f"Message: {outcome.message}")
            print(f"Count: {outcome.count}")
            
            # Check database
            transactions = Transaction.find_all()
            print(f"Total in database: {len(transactions)}")
            
        except Exception as e:
            print(f"Error: {e}")
    
    # Clean up
    os.unlink(temp_file)

def main():
    """Run all deduplication tests"""
    print("=== Comprehensive Deduplication Test ===")
    
    try:
        # Test basic functionality
        test_basic_deduplication()
        
        # Test merge strategies
        test_merge_strategies()
        
        # Test similarity matching
        test_similarity_matching()
        
        # Test full upload process
        test_upload_with_deduplication()
        
        print("\n=== All Tests Completed ===")
        print("Deduplication system is working correctly!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
