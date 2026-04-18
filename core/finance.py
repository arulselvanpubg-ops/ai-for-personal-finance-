from .db import Transaction, DB
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import numpy as np

def calculate_financial_health_score(year: int = None, month: int = None, db=None) -> float:
    """Calculate financial health score (0-100) for a given month."""
    now = datetime.now()
    year = year or now.year
    month = month or now.month
    
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
        
    # If the requested month is the current month, only calculate up to today
    if year == now.year and month == now.month:
        end_date = now
    
    transactions = Transaction.find_by_date_range(start_date, end_date)
    
    if not transactions:
        return 50.0  # Neutral score if no data
    
    df = pd.DataFrame([{
        'amount': t['amount'],
        'category': t['category']
    } for t in transactions])
    
    income = df[df['amount'] > 0]['amount'].sum()
    expenses = abs(df[df['amount'] < 0]['amount'].sum())
    
    if income == 0:
        return 0.0
    
    ratio = expenses / income
    
    # Score based on expense-to-income ratio
    if ratio <= 0.5:
        score = 100.0
    elif ratio <= 0.7:
        score = 80.0
    elif ratio <= 0.9:
        score = 60.0
    else:
        score = 20.0
    
    return min(100.0, max(0.0, score))

def get_monthly_summary(year: int, month: int, db=None) -> Dict:
    """Get monthly financial summary."""
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    transactions = Transaction.find_by_date_range(start_date, end_date)
    
    if not transactions:
        return {
            'income': 0.0,
            'expenses': 0.0,
            'net': 0.0,
            'categories': {}
        }
    
    df = pd.DataFrame([{
        'amount': t['amount'],
        'category': t['category']
    } for t in transactions])
    
    income = df[df['amount'] > 0]['amount'].sum()
    expenses = abs(df[df['amount'] < 0]['amount'].sum())
    
    category_breakdown = df.groupby('category')['amount'].sum().abs().to_dict()
    
    return {
        'income': income,
        'expenses': expenses,
        'net': income - expenses,
        'categories': category_breakdown
    }

def detect_anomalies(db=None) -> List[Dict]:
    """Detect anomalous transactions using Z-score."""
    transactions = Transaction.find_all()
    if len(transactions) < 10:
        return []
    
    df = pd.DataFrame([{
        'id': str(t.get('_id', '')),
        'amount': abs(t['amount']),
        'description': t['description'],
        'category': t['category'],
        'date': t['date']
    } for t in transactions])
    
    # Calculate Z-score for amounts
    mean = df['amount'].mean()
    std = df['amount'].std()
    
    if std == 0:
        return []
    
    df['z_score'] = (df['amount'] - mean) / std
    
    # Anomalies are Z-score > 3
    anomalies = df[df['z_score'] > 3].to_dict('records')
    
    return anomalies

def get_budget_progress(db=None) -> Dict[str, Dict]:
    """Get budget progress for current month."""
    now = datetime.now()
    month_str = now.strftime('%Y-%m')
    
    budgets = DB.get_budgets().find({'month': month_str})
    
    progress = {}
    for budget in budgets:
        category_name = budget.get('category_id', 'Uncategorized')
        budgeted = budget['amount']
        
        # Get spent amount
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        transactions = DB.get_transactions().find({
            'category': category_name,
            'date': {'$gte': start_of_month},
            'amount': {'$lt': 0}
        })
        
        spent_amount = abs(sum([t['amount'] for t in transactions]))
        
        progress[category_name] = {
            'budgeted': budgeted,
            'spent': spent_amount,
            'remaining': budgeted - spent_amount,
            'percentage': (spent_amount / budgeted * 100) if budgeted > 0 else 0
        }
    
    return progress