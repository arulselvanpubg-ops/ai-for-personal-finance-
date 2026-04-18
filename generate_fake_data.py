#!/usr/bin/env python3
"""
Generate comprehensive fake financial data for 2023-2026
Salary always higher than expenses for each month
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict
import pandas as pd
from core.db import Transaction
from utils.monitoring import log_event

class FakeDataGenerator:
    def __init__(self):
        self.categories = {
            'Food & Dining': ['Restaurant', 'Grocery Store', 'Food Delivery', 'Coffee Shop', 'Bakery'],
            'Transportation': ['Fuel Station', 'Metro/Auto', 'Uber/Ola', 'Bus Pass', 'Parking'],
            'Shopping': ['Amazon', 'Flipkart', 'Myntra', 'Clothing Store', 'Electronics'],
            'Entertainment': ['Movie Tickets', 'Netflix', 'Spotify', 'Gaming', 'Concert'],
            'Bills & Utilities': ['Electricity Bill', 'Water Bill', 'Internet', 'Mobile Recharge', 'Gas Bill'],
            'Healthcare': ['Pharmacy', 'Doctor Visit', 'Hospital', 'Insurance', 'Medical Store'],
            'Education': ['Online Course', 'Books', 'Tuition', 'School Fees', 'Stationery'],
            'Travel': ['Flight Booking', 'Hotel Stay', 'Train Tickets', 'Taxi', 'Tourism'],
            'Other': ['ATM Withdrawal', 'Bank Charges', 'Gifts', 'Donations', 'Miscellaneous']
        }
        
        # Salary ranges (increasing over years)
        self.salary_ranges = {
            2023: (45000, 65000),
            2024: (50000, 75000),
            2025: (55000, 85000),
            2026: (60000, 95000)
        }
        
        # Expense multipliers (to ensure salary > expenses)
        self.expense_multipliers = {
            2023: (0.4, 0.7),  # 40-70% of salary
            2024: (0.35, 0.65), # 35-65% of salary
            2025: (0.3, 0.6),   # 30-60% of salary
            2026: (0.25, 0.55)  # 25-55% of salary
        }
        
        # Transaction descriptions with variations
        self.description_variations = {
            'Salary Credit': ['Salary Credit', 'Monthly Salary', 'Salary Deposit', 'Salary Transfer'],
            'Rent': ['Monthly Rent', 'House Rent', 'Apartment Rent'],
            'Investment': ['SIP Investment', 'Mutual Fund', 'Stock Purchase', 'FD Deposit']
        }

    def generate_monthly_transactions(self, year: int, month: int) -> List[Dict]:
        """Generate transactions for a specific month ensuring salary > expenses"""
        transactions = []
        
        # Get salary range for the year
        salary_min, salary_max = self.salary_ranges[year]
        salary = random.randint(salary_min, salary_max)
        
        # Get expense multiplier range
        expense_min_mult, expense_max_mult = self.expense_multipliers[year]
        expense_multiplier = random.uniform(expense_min_mult, expense_max_mult)
        
        # Calculate target expenses (must be less than salary)
        max_expenses = salary * expense_multiplier
        
        # Generate salary transaction (usually on 1st or last working day)
        salary_day = random.choice([1, 25, 30, 31])
        # Ensure day is valid for the month
        last_day = self._get_last_day_of_month(year, month)
        salary_day = min(salary_day, last_day)
        
        salary_date = datetime(year, month, salary_day)
        salary_desc = random.choice(self.description_variations['Salary Credit'])
        
        transactions.append({
            'date': salary_date,
            'amount': float(salary),
            'description': salary_desc,
            'category': 'Income'
        })
        
        # Generate expense transactions
        current_expenses = 0
        transaction_days = self._generate_transaction_days(year, month, exclude_days=[salary_day])
        
        # Essential expenses (rent, utilities, etc.)
        essential_expenses = self._generate_essential_expenses(year, month, transaction_days[:10])
        transactions.extend(essential_expenses)
        current_expenses += sum(tx['amount'] for tx in essential_expenses if tx['amount'] < 0)
        
        # Discretionary expenses (food, entertainment, etc.)
        remaining_budget = max_expenses - abs(current_expenses)
        if remaining_budget > 0:
            discretionary_expenses = self._generate_discretionary_expenses(
                year, month, transaction_days[10:], remaining_budget
            )
            transactions.extend(discretionary_expenses)
            current_expenses += sum(tx['amount'] for tx in discretionary_expenses if tx['amount'] < 0)
        
        # Investment/savings transactions
        savings_amount = salary * random.uniform(0.1, 0.3)  # 10-30% savings
        investment_desc = random.choice(self.description_variations['Investment'])
        
        # Find a day for investment (preferably after salary, but any day works)
        investment_candidates = [d for d in transaction_days if d > salary_day]
        if not investment_candidates:
            investment_candidates = transaction_days
        
        if investment_candidates:
            investment_day = random.choice(investment_candidates)
            transactions.append({
                'date': datetime(year, month, investment_day),
                'amount': -abs(savings_amount),
                'description': investment_desc,
                'category': 'Investment'
            })
        
        # Sort transactions by date
        transactions.sort(key=lambda x: x['date'])
        
        # Verify salary > total expenses
        total_expenses = sum(abs(tx['amount']) for tx in transactions if tx['amount'] < 0)
        if total_expenses >= salary:
            # Adjust expenses if needed
            transactions = self._adjust_expenses(transactions, salary * 0.9)
        
        return transactions

    def _get_last_day_of_month(self, year: int, month: int) -> int:
        """Get the last day of a month"""
        if month == 12:
            return 31
        next_month = datetime(year, month + 1, 1) - timedelta(days=1)
        return next_month.day

    def _generate_transaction_days(self, year: int, month: int, exclude_days: List[int] = None) -> List[int]:
        """Generate random days for transactions"""
        exclude_days = exclude_days or []
        last_day = self._get_last_day_of_month(year, month)
        all_days = list(range(1, last_day + 1))
        available_days = [d for d in all_days if d not in exclude_days]
        
        # Generate 15-25 transaction days
        num_transactions = random.randint(15, 25)
        return sorted(random.sample(available_days, min(num_transactions, len(available_days))))

    def _generate_essential_expenses(self, year: int, month: int, days: List[int]) -> List[Dict]:
        """Generate essential expenses like rent, utilities"""
        expenses = []
        
        # Rent (if not first month of year)
        if month > 1:
            rent_day = days[0] if days else 1
            rent_amount = random.randint(8000, 15000)
            expenses.append({
                'date': datetime(year, month, rent_day),
                'amount': -rent_amount,
                'description': random.choice(self.description_variations['Rent']),
                'category': 'Bills & Utilities'
            })
        
        # Utilities
        utility_days = days[1:4] if len(days) > 3 else days[1:]
        utility_amounts = {
            'Electricity Bill': random.randint(800, 2500),
            'Water Bill': random.randint(300, 800),
            'Internet': random.randint(500, 1500),
            'Mobile Recharge': random.randint(200, 800),
            'Gas Bill': random.randint(400, 1200)
        }
        
        for i, (utility, amount) in enumerate(utility_amounts.items()):
            if i < len(utility_days):
                expenses.append({
                    'date': datetime(year, month, utility_days[i]),
                    'amount': -amount,
                    'description': utility,
                    'category': 'Bills & Utilities'
                })
        
        return expenses

    def _generate_discretionary_expenses(self, year: int, month: int, days: List[int], budget: float) -> List[Dict]:
        """Generate discretionary expenses within budget"""
        expenses = []
        remaining_budget = budget
        
        # Category weights
        category_weights = {
            'Food & Dining': 0.25,
            'Transportation': 0.15,
            'Shopping': 0.20,
            'Entertainment': 0.10,
            'Healthcare': 0.08,
            'Education': 0.07,
            'Travel': 0.10,
            'Other': 0.05
        }
        
        for category, weight in category_weights.items():
            category_budget = remaining_budget * weight
            if category_budget <= 0:
                continue
            
            # Generate 1-3 transactions per category
            num_transactions = random.randint(1, 3)
            category_days = random.sample(days, min(num_transactions, len(days)))
            
            for day in category_days:
                if category_budget <= 0:
                    break
                
                # Generate amount for this transaction
                max_amount = min(category_budget, self._get_max_amount_for_category(category))
                if max_amount <= 0:
                    continue
                
                amount = random.uniform(100, max_amount)
                amount = min(amount, category_budget)
                
                # Get description
                descriptions = self.categories[category]
                description = random.choice(descriptions)
                
                expenses.append({
                    'date': datetime(year, month, day),
                    'amount': -round(amount, 2),
                    'description': description,
                    'category': category
                })
                
                category_budget -= amount
        
        return expenses

    def _get_max_amount_for_category(self, category: str) -> float:
        """Get maximum realistic amount for a category"""
        max_amounts = {
            'Food & Dining': 2000,
            'Transportation': 1500,
            'Shopping': 5000,
            'Entertainment': 2000,
            'Healthcare': 3000,
            'Education': 2000,
            'Travel': 4000,
            'Other': 1000
        }
        return max_amounts.get(category, 1000)

    def _adjust_expenses(self, transactions: List[Dict], max_expenses: float) -> List[Dict]:
        """Adjust expenses to ensure they don't exceed maximum"""
        # Separate income and expenses
        income_tx = [tx for tx in transactions if tx['amount'] > 0]
        expense_tx = [tx for tx in transactions if tx['amount'] < 0]
        
        # Calculate current total expenses
        current_expenses = sum(abs(tx['amount']) for tx in expense_tx)
        
        if current_expenses <= max_expenses:
            return transactions
        
        # Scale down expenses proportionally
        scale_factor = max_expenses / current_expenses
        
        for tx in expense_tx:
            tx['amount'] = tx['amount'] * scale_factor
        
        return income_tx + expense_tx

    def generate_year_data(self, year: int) -> List[Dict]:
        """Generate all transactions for a year"""
        year_transactions = []
        
        for month in range(1, 13):
            monthly_transactions = self.generate_monthly_transactions(year, month)
            year_transactions.extend(monthly_transactions)
            
            # Verify salary > expenses for this month
            monthly_income = sum(tx['amount'] for tx in monthly_transactions if tx['amount'] > 0)
            monthly_expenses = sum(abs(tx['amount']) for tx in monthly_transactions if tx['amount'] < 0)
            
            print(f"{year}-{month:02d}: Income=Rs.{monthly_income:,.0f}, Expenses=Rs.{monthly_expenses:,.0f}, Ratio={monthly_expenses/monthly_income:.2f}")
        
        return year_transactions

    def generate_all_data(self) -> List[Dict]:
        """Generate data for all years (2023-2026)"""
        all_transactions = []
        
        for year in [2023, 2024, 2025, 2026]:
            print(f"\n=== Generating {year} Data ===")
            year_transactions = self.generate_year_data(year)
            all_transactions.extend(year_transactions)
        
        return all_transactions

def load_fake_data_to_database():
    """Generate and load fake data into database"""
    print("=== Generating Comprehensive Fake Data (2023-2026) ===")
    
    # Clear existing data
    Transaction._collection().delete_many({})
    print("Cleared existing transactions")
    
    # Generate fake data
    generator = FakeDataGenerator()
    all_transactions = generator.generate_all_data()
    
    print(f"\nGenerated {len(all_transactions)} total transactions")
    
    # Load into database
    loaded_count = 0
    for tx in all_transactions:
        try:
            Transaction.create(
                date=tx['date'],
                amount=tx['amount'],
                description=tx['description'],
                category=tx['category']
            )
            loaded_count += 1
        except Exception as e:
            print(f"Error loading transaction: {e}")
    
    print(f"Successfully loaded {loaded_count} transactions into database")
    
    # Verify data
    verify_data()
    
    return loaded_count

def verify_data():
    """Verify the loaded data meets requirements"""
    print("\n=== Data Verification ===")
    
    transactions = Transaction.find_all()
    print(f"Total transactions in database: {len(transactions)}")
    
    # Check yearly summaries
    years = [2023, 2024, 2025, 2026]
    
    for year in years:
        year_tx = [tx for tx in transactions if tx['date'].year == year]
        
        yearly_income = sum(tx['amount'] for tx in year_tx if tx['amount'] > 0)
        yearly_expenses = sum(abs(tx['amount']) for tx in year_tx if tx['amount'] < 0)
        
        print(f"\n{year} Summary:")
        print(f"  Income: Rs.{yearly_income:,.0f}")
        print(f"  Expenses: Rs.{yearly_expenses:,.0f}")
        print(f"  Net: Rs.{yearly_income - yearly_expenses:,.0f}")
        print(f"  Savings Rate: {((yearly_income - yearly_expenses) / yearly_income * 100):.1f}%")
        
        # Check monthly compliance
        months = range(1, 13)
        compliant_months = 0
        
        for month in months:
            month_tx = [tx for tx in year_tx if tx['date'].month == month]
            monthly_income = sum(tx['amount'] for tx in month_tx if tx['amount'] > 0)
            monthly_expenses = sum(abs(tx['amount']) for tx in month_tx if tx['amount'] < 0)
            
            if monthly_income > monthly_expenses:
                compliant_months += 1
            else:
                print(f"    WARNING: {year}-{month:02d} - Expenses (Rs.{monthly_expenses:,.0f}) >= Income (Rs.{monthly_income:,.0f})")
        
        print(f"  Compliant months: {compliant_months}/12 ({compliant_months/12*100:.1f}%)")
    
    # Category breakdown
    categories = {}
    for tx in transactions:
        if tx['amount'] < 0:  # Only expenses
            cat = tx['category']
            categories[cat] = categories.get(cat, 0) + abs(tx['amount'])
    
    print(f"\nCategory Breakdown:")
    for cat, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat}: Rs.{amount:,.0f}")

if __name__ == "__main__":
    load_fake_data_to_database()
