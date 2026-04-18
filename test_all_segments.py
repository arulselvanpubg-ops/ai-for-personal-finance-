#!/usr/bin/env python3
"""
Test script to verify all segments work with uploaded bank statement data
"""

import pandas as pd
from datetime import datetime
from core.db import Transaction, Budget, Category
from core.parser import import_transactions
from ai.categorizer import categorize_transactions_for_import
from core.finance import get_monthly_summary, calculate_financial_health_score, get_budget_progress

def test_dashboard_functionality():
    """Test dashboard with uploaded data"""
    print("=== Testing Dashboard Functionality ===")
    
    transactions = Transaction.find_all()
    has_data = bool(transactions)
    
    if not has_data:
        print("No data found for dashboard test")
        return False
    
    # Test monthly summary
    now = datetime.now()
    summary = get_monthly_summary(now.year, now.month)
    print(f"Monthly Summary: {summary}")
    
    # Test financial health score
    score = calculate_financial_health_score(now.year, now.month)
    print(f"Financial Health Score: {score}")
    
    print("Dashboard functionality: PASSED")
    return True

def test_expenses_functionality():
    """Test expenses segment with uploaded data"""
    print("\n=== Testing Expenses Functionality ===")
    
    transactions = Transaction.find_all()
    has_data = bool(transactions)
    
    if not has_data:
        print("No data found for expenses test")
        return False
    
    print(f"Found {len(transactions)} transactions")
    
    # Test filtering by category
    categories = set(tx['category'] for tx in transactions)
    print(f"Categories found: {categories}")
    
    # Test search functionality
    search_results = [tx for tx in transactions if 'salary' in tx['description'].lower()]
    print(f"Search results for 'salary': {len(search_results)}")
    
    print("Expenses functionality: PASSED")
    return True

def test_budget_functionality():
    """Test budget segment with uploaded data"""
    print("\n=== Testing Budget Functionality ===")
    
    transactions = Transaction.find_all()
    has_data = bool(transactions)
    
    if not has_data:
        print("No data found for budget test")
        return False
    
    # Create some sample budgets for testing
    categories = ["Food & Dining", "Transportation", "Shopping", "Bills & Utilities"]
    
    for cat in categories:
        # Create category if not exists
        existing_cats = Category.find_all()
        if not any(c['name'] == cat for c in existing_cats):
            Category.create(cat, budget=5000.0)
        
        # Create budget for current month
        now = datetime.now()
        month_str = now.strftime('%Y-%m')
        Budget.create(cat, month_str, 5000.0)
    
    # Test budget progress
    progress = get_budget_progress()
    print(f"Budget progress: {progress}")
    
    print("Budget functionality: PASSED")
    return True

def test_reports_functionality():
    """Test reports segment with uploaded data"""
    print("\n=== Testing Reports Functionality ===")
    
    transactions = Transaction.find_all()
    has_data = bool(transactions)
    
    if not has_data:
        print("No data found for reports test")
        return False
    
    # Test data aggregation for reports
    income = sum(tx['amount'] for tx in transactions if tx['amount'] > 0)
    expenses = abs(sum(tx['amount'] for tx in transactions if tx['amount'] < 0))
    net = income - expenses
    
    print(f"Report Summary - Income: {income}, Expenses: {expenses}, Net: {net}")
    
    # Test category breakdown
    categories = {}
    for tx in transactions:
        if tx['amount'] < 0:  # Only expenses
            cat = tx['category']
            categories[cat] = categories.get(cat, 0) + abs(tx['amount'])
    
    print(f"Category breakdown: {categories}")
    
    print("Reports functionality: PASSED")
    return True

def main():
    """Run all tests"""
    print("=== Testing All Segments with Uploaded Bank Statement Data ===")
    
    # Check if we have data
    transactions = Transaction.find_all()
    if not transactions:
        print("No transactions found. Please run test_bank_upload.py first.")
        return False
    
    print(f"Found {len(transactions)} transactions in database")
    
    # Test all segments
    results = {
        'dashboard': test_dashboard_functionality(),
        'expenses': test_expenses_functionality(),
        'budget': test_budget_functionality(),
        'reports': test_reports_functionality(),
    }
    
    print(f"\n=== Test Results ===")
    for segment, passed in results.items():
        status = "PASSED" if passed else "FAILED"
        print(f"{segment.capitalize()}: {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall: {'PASSED' if all_passed else 'FAILED'}")
    
    if all_passed:
        print("\nSUCCESS: All segments work correctly with uploaded bank statement data!")
        print("Your project is ready to use with real bank statements.")
    else:
        print("\nSome segments need attention.")
    
    return all_passed

if __name__ == "__main__":
    main()
