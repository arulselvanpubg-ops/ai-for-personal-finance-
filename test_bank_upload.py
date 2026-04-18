#!/usr/bin/env python3
"""
Test script to verify bank statement upload functionality
"""

import pandas as pd
from datetime import datetime, timedelta
from core.db import Transaction
from core.parser import import_transactions
from ai.categorizer import categorize_transactions_for_import

def create_sample_csv():
    """Create a sample CSV bank statement for testing"""
    # Sample transactions
    transactions = [
        {"Date": "2026-04-01", "Description": "Salary Credit", "Amount": 85000.00},
        {"Date": "2026-04-02", "Description": "Grocery Shopping", "Amount": -2500.00},
        {"Date": "2026-04-03", "Description": "Electricity Bill", "Amount": -1200.00},
        {"Date": "2026-04-04", "Description": "Restaurant", "Amount": -800.00},
        {"Date": "2026-04-05", "Description": "Fuel Station", "Amount": -2000.00},
        {"Date": "2026-04-06", "Description": "Online Shopping", "Amount": -3500.00},
        {"Date": "2026-04-07", "Description": "Medical Store", "Amount": -500.00},
        {"Date": "2026-04-08", "Description": "Movie Tickets", "Amount": -600.00},
        {"Date": "2026-04-09", "Description": "Mobile Recharge", "Amount": -299.00},
        {"Date": "2026-04-10", "Description": "Cash Withdrawal", "Amount": -5000.00},
    ]
    
    df = pd.DataFrame(transactions)
    df.to_csv("sample_bank_statement.csv", index=False)
    print("Sample CSV created: sample_bank_statement.csv")
    return "sample_bank_statement.csv"

def test_bank_upload():
    """Test the complete bank statement upload process"""
    print("=== Testing Bank Statement Upload ===")
    
    # Clear existing data
    Transaction._collection().delete_many({})
    print("Cleared existing transactions")
    
    # Create sample CSV
    csv_file = create_sample_csv()
    
    # Import transactions
    try:
        transactions = import_transactions(csv_file)
        print(f"Parsed {len(transactions)} transactions from CSV")
        
        if not transactions:
            print("ERROR: No transactions parsed")
            return False
            
        # Categorize transactions
        descriptions = [tx.get("description", "") for tx in transactions]
        categories = categorize_transactions_for_import(descriptions)
        
        # Save to database
        for tx, cat in zip(transactions, categories):
            Transaction.create(
                date=tx["date"],
                amount=tx["amount"],
                description=tx["description"],
                category=cat,
            )
        
        print(f"Successfully saved {len(transactions)} transactions to database")
        
        # Verify data
        all_transactions = Transaction.find_all()
        print(f"Total transactions in database: {len(all_transactions)}")
        
        if all_transactions:
            print("Sample transactions:")
            for i, tx in enumerate(all_transactions[:3]):
                print(f"  {i+1}. {tx['date'].strftime('%Y-%m-%d')} - {tx['description']} - {tx['amount']} - {tx['category']}")
        
        return True
        
    except Exception as e:
        print(f"ERROR during upload: {e}")
        return False

def test_dashboard_data():
    """Test that dashboard would show real data"""
    print("\n=== Testing Dashboard Data ===")
    
    all_transactions = Transaction.find_all()
    has_data = bool(all_transactions)
    
    print(f"Has real data: {has_data}")
    print(f"Number of transactions: {len(all_transactions)}")
    
    if has_data:
        # Calculate summary like dashboard would
        from core.finance import get_monthly_summary, calculate_financial_health_score
        
        now = datetime.now()
        summary = get_monthly_summary(now.year, now.month)
        score = calculate_financial_health_score(now.year, now.month)
        
        print(f"Monthly Summary: {summary}")
        print(f"Financial Health Score: {score}")
    
    return has_data

if __name__ == "__main__":
    # Test upload
    upload_success = test_bank_upload()
    
    # Test dashboard data
    dashboard_has_data = test_dashboard_data()
    
    print(f"\n=== Results ===")
    print(f"Upload Success: {upload_success}")
    print(f"Dashboard Has Data: {dashboard_has_data}")
    
    if upload_success and dashboard_has_data:
        print("SUCCESS: Bank statement upload is working correctly!")
        print("The dashboard should now show real data from your uploaded statement.")
    else:
        print("ISSUE: Bank statement upload needs attention.")
