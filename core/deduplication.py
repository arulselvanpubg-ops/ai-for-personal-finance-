"""
Enhanced deduplication system for financial transactions
"""

from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple, Optional
import hashlib
from core.db import Transaction
from utils.monitoring import log_event


class TransactionDeduplicator:
    """Advanced deduplication system for financial transactions"""
    
    def __init__(self):
        self.similarity_threshold = 0.8  # For fuzzy matching
        self.amount_tolerance = 0.01    # 1 paisa tolerance for amounts
        self.date_tolerance_days = 1    # Same day or adjacent days
    
    def generate_transaction_key(self, transaction: Dict) -> str:
        """Generate a unique key for a transaction"""
        # Normalize description
        description = transaction['description'].lower().strip()
        # Remove common variations
        description = self._normalize_description(description)
        
        # Round amount to 2 decimal places
        amount = round(float(transaction['amount']), 2)
        
        # Use date only (not time)
        date = transaction['date'].date() if hasattr(transaction['date'], 'date') else transaction['date']
        
        # Create key components
        key_components = [
            str(date),
            str(amount),
            description[:100]  # First 100 chars
        ]
        
        # Generate hash
        key_string = '|'.join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _normalize_description(self, description: str) -> str:
        """Normalize transaction description for better matching"""
        import re
        
        # Remove extra spaces and special characters
        description = re.sub(r'\s+', ' ', description)
        description = re.sub(r'[^\w\s]', '', description)
        
        # Remove common prefixes/suffixes
        prefixes_to_remove = ['txn', 'transaction', 'transfer', 'payment', 'dr', 'cr']
        suffixes_to_remove = [' ltd', ' pvt', ' limited', ' private', ' limited']
        
        for prefix in prefixes_to_remove:
            if description.startswith(prefix):
                description = description[len(prefix):].strip()
        
        for suffix in suffixes_to_remove:
            if description.endswith(suffix):
                description = description[:-len(suffix)].strip()
        
        return description
    
    def find_existing_transactions(self, new_transactions: List[Dict]) -> Dict[str, Dict]:
        """Find existing transactions that match new ones"""
        existing_transactions = Transaction.find_all()
        
        # Create mapping of existing transaction keys
        existing_map = {}
        for tx in existing_transactions:
            key = self.generate_transaction_key(tx)
            existing_map[key] = tx
        
        return existing_map
    
    def calculate_similarity(self, desc1: str, desc2: str) -> float:
        """Calculate similarity between two descriptions using simple approach"""
        # Simple character-based similarity
        shorter = min(len(desc1), len(desc2))
        if shorter == 0:
            return 0.0
        
        # Count matching characters
        matches = sum(c1 == c2 for c1, c2 in zip(desc1, desc2))
        return matches / max(len(desc1), len(desc2))
    
    def is_similar_transaction(self, tx1: Dict, tx2: Dict) -> bool:
        """Check if two transactions are similar enough to be considered duplicates"""
        # Check amount similarity
        amount1 = round(float(tx1['amount']), 2)
        amount2 = round(float(tx2['amount']), 2)
        if abs(amount1 - amount2) > self.amount_tolerance:
            return False
        
        # Check date proximity
        date1 = tx1['date'].date() if hasattr(tx1['date'], 'date') else tx1['date']
        date2 = tx2['date'].date() if hasattr(tx2['date'], 'date') else tx2['date']
        
        date_diff = abs((date1 - date2).days)
        if date_diff > self.date_tolerance_days:
            return False
        
        # Check description similarity
        desc1 = self._normalize_description(tx1['description'].lower())
        desc2 = self._normalize_description(tx2['description'].lower())
        
        similarity = self.calculate_similarity(desc1, desc2)
        return similarity >= self.similarity_threshold
    
    def deduplicate_transactions(self, new_transactions: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Deduplicate new transactions against existing ones
        
        Returns:
            Tuple of (unique_transactions, duplicate_transactions)
        """
        existing_map = self.find_existing_transactions(new_transactions)
        
        unique_transactions = []
        duplicate_transactions = []
        duplicate_keys = set()
        
        for new_tx in new_transactions:
            new_key = self.generate_transaction_key(new_tx)
            
            # Check exact match
            if new_key in existing_map:
                duplicate_transactions.append({
                    'new_transaction': new_tx,
                    'existing_transaction': existing_map[new_key],
                    'match_type': 'exact'
                })
                duplicate_keys.add(new_key)
                continue
            
            # Check for similar transactions
            similar_found = False
            for existing_key, existing_tx in existing_map.items():
                if self.is_similar_transaction(new_tx, existing_tx):
                    duplicate_transactions.append({
                        'new_transaction': new_tx,
                        'existing_transaction': existing_tx,
                        'match_type': 'similar'
                    })
                    similar_found = True
                    break
            
            if not similar_found:
                unique_transactions.append(new_tx)
        
        return unique_transactions, duplicate_transactions
    
    def smart_merge_transactions(self, new_transactions: List[Dict], 
                               merge_strategy: str = 'keep_newest') -> List[Dict]:
        """
        Smart merge transactions with existing ones
        
        Args:
            new_transactions: List of new transactions to merge
            merge_strategy: 'keep_newest', 'keep_existing', 'merge_all'
        
        Returns:
            List of transactions after merging
        """
        if merge_strategy == 'merge_all':
            # Don't deduplicate, just add all
            return new_transactions
        
        unique_tx, duplicate_tx = self.deduplicate_transactions(new_transactions)
        
        if merge_strategy == 'keep_existing':
            # Only add unique transactions, skip duplicates
            return unique_tx
        
        elif merge_strategy == 'keep_newest':
            # Add unique transactions, and update duplicates with newer data
            merged_transactions = unique_tx.copy()
            
            for dup in duplicate_tx:
                new_tx = dup['new_transaction']
                existing_tx = dup['existing_transaction']
                
                # Keep the newer transaction (based on date or creation time)
                new_date = new_tx['date']
                existing_date = existing_tx['date']
                
                if new_date > existing_date:
                    # Update existing transaction with new data
                    try:
                        Transaction.update(existing_tx['_id'], {
                            'date': new_tx['date'],
                            'amount': new_tx['amount'],
                            'description': new_tx['description'],
                            'category': new_tx['category'],
                            'updated_at': datetime.now()
                        })
                        log_event("info", "transaction_updated", 
                                transaction_id=existing_tx['_id'],
                                new_date=new_date)
                    except Exception as e:
                        log_event("error", "transaction_update_failed", 
                                error=str(e), transaction_id=existing_tx['_id'])
                        # If update fails, just add the new one
                        merged_transactions.append(new_tx)
                # If existing is newer, skip the new one
            
            return merged_transactions
        
        return unique_tx
    
    def get_deduplication_stats(self, new_transactions: List[Dict]) -> Dict:
        """Get statistics about deduplication process"""
        existing_map = self.find_existing_transactions(new_transactions)
        unique_tx, duplicate_tx = self.deduplicate_transactions(new_transactions)
        
        return {
            'new_transactions_count': len(new_transactions),
            'existing_transactions_count': len(existing_map),
            'unique_transactions_count': len(unique_tx),
            'duplicate_transactions_count': len(duplicate_tx),
            'duplicate_percentage': (len(duplicate_tx) / len(new_transactions) * 100) if new_transactions else 0,
            'duplicates_by_type': {
                'exact': len([d for d in duplicate_tx if d['match_type'] == 'exact']),
                'similar': len([d for d in duplicate_tx if d['match_type'] == 'similar'])
            }
        }


# Global deduplicator instance
deduplicator = TransactionDeduplicator()


def deduplicate_import_transactions(transactions: List[Dict], 
                                  merge_strategy: str = 'keep_newest') -> Tuple[List[Dict], Dict]:
    """
    Main function to deduplicate transactions during import
    
    Args:
        transactions: List of new transactions to import
        merge_strategy: Strategy for handling duplicates
    
    Returns:
        Tuple of (deduplicated_transactions, stats)
    """
    stats = deduplicator.get_deduplication_stats(transactions)
    
    if merge_strategy == 'replace_all':
        # Clear all existing and import new ones (current behavior)
        Transaction._collection().delete_many({})
        deduplicated = transactions
    else:
        # Smart merge
        deduplicated = deduplicator.smart_merge_transactions(transactions, merge_strategy)
    
    log_event("info", "deduplication_completed", stats=stats)
    
    return deduplicated, stats
