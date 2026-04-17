import pandas as pd
import pdfplumber
import csv
from datetime import datetime
from typing import List, Dict
import os

from utils.validators import sanitize_input

def parse_csv(file_path: str) -> List[Dict]:
    """Parse CSV file and return list of transaction dicts."""
    transactions = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names (case insensitive)
            normalized = {(k or '').lower(): (v or '').strip() for k, v in row.items()}
            
            # Try to extract date, amount, description
            date_str = normalized.get('date') or normalized.get('transaction date')
            amount_str = normalized.get('amount') or normalized.get('debit') or normalized.get('credit')
            description = normalized.get('description') or normalized.get('memo') or normalized.get('details')
            
            if date_str and amount_str:
                try:
                    # Parse date - try common formats
                    date = None
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d %H:%M:%S']:
                        try:
                            date = datetime.strptime(date_str, fmt)
                            break
                        except ValueError:
                            continue
                    
                    if date:
                        amount = float(amount_str.replace('$', '').replace(',', ''))
                        transactions.append({
                            'date': date,
                            'amount': amount,
                            'description': sanitize_input(description or '', max_length=200),
                            'category': 'Uncategorized'
                        })
                except (ValueError, AttributeError):
                    continue
    
    return transactions

def parse_pdf(file_path: str) -> List[Dict]:
    """Parse PDF file and extract transactions."""
    transactions = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                # Simple text parsing - look for lines with dates and amounts
                lines = text.split('\n')
                for line in lines:
                    # Basic regex-like parsing for common formats
                    # This is a simplified version - real implementation would need more robust parsing
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            # Assume format: Date Description Amount
                            date_str = parts[0]
                            amount_str = parts[-1]
                            description = ' '.join(parts[1:-1])
                            
                            date = datetime.strptime(date_str, '%m/%d/%Y')
                            amount = float(amount_str.replace('$', '').replace(',', ''))
                            
                            transactions.append({
                                'date': date,
                                'amount': amount,
                                'description': sanitize_input(description, max_length=200),
                                'category': 'Uncategorized'
                            })
                        except (ValueError, IndexError):
                            continue
    
    return transactions

def import_transactions(file_path: str) -> List[Dict]:
    """Import transactions from file (CSV or PDF)."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.csv':
        return parse_csv(file_path)
    elif ext == '.pdf':
        return parse_pdf(file_path)
    else:
        raise ValueError("Unsupported file format. Use CSV or PDF.")
