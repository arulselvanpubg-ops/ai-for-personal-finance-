import os
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# MongoDB connection setup
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'finsight')

if not MONGODB_URI:
    raise ValueError("MONGODB_URI not set in .env file")

try:
    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    # Test the connection
    client.admin.command('ismaster')
    db = client[MONGODB_DB_NAME]
    print(f"✓ Connected to MongoDB: {MONGODB_DB_NAME}")
except ConnectionFailure as e:
    print(f"✗ Failed to connect to MongoDB: {e}")
    raise

# Collection definitions
transactions_collection = db['transactions']
categories_collection = db['categories']
budgets_collection = db['budgets']
goals_collection = db['goals']
investments_collection = db['investments']
chat_history_collection = db['chat_history']

# Create indexes for better performance
transactions_collection.create_index('date')
transactions_collection.create_index('category')
budgets_collection.create_index('month')
chat_history_collection.create_index('timestamp')

# Helper classes for ORM-like interface
class Transaction:
    """MongoDB Transaction document helper"""
    @staticmethod
    def create(date, amount, description, category, notes=None):
        doc = {
            'date': date if isinstance(date, datetime) else datetime.fromisoformat(str(date)),
            'amount': float(amount),
            'description': str(description),
            'category': str(category),
            'notes': notes,
            'created_at': datetime.utcnow()
        }
        result = transactions_collection.insert_one(doc)
        return result.inserted_id
    
    @staticmethod
    def find_by_date_range(start_date, end_date):
        return list(transactions_collection.find({
            'date': {'$gte': start_date, '$lt': end_date}
        }).sort('date', -1))
    
    @staticmethod
    def find_all():
        return list(transactions_collection.find().sort('date', -1))

class Category:
    """MongoDB Category document helper"""
    @staticmethod
    def create(name, budget=0.0):
        doc = {'name': str(name), 'budget': float(budget)}
        result = categories_collection.insert_one(doc)
        return result.inserted_id
    
    @staticmethod
    def find_all():
        return list(categories_collection.find())
    
    @staticmethod
    def update_budget(name, budget):
        categories_collection.update_one(
            {'name': name},
            {'$set': {'budget': float(budget)}}
        )

class Budget:
    """MongoDB Budget document helper"""
    @staticmethod
    def create(category_id, month, amount):
        doc = {
            'category_id': category_id,
            'month': str(month),
            'amount': float(amount)
        }
        result = budgets_collection.insert_one(doc)
        return result.inserted_id
    
    @staticmethod
    def find_by_month(month):
        return list(budgets_collection.find({'month': month}))

class Goal:
    """MongoDB Goal document helper"""
    @staticmethod
    def create(name, target_amount, target_date, current_amount=0.0):
        doc = {
            'name': str(name),
            'target_amount': float(target_amount),
            'current_amount': float(current_amount),
            'target_date': target_date if isinstance(target_date, datetime) else datetime.fromisoformat(str(target_date)),
            'created_at': datetime.utcnow()
        }
        result = goals_collection.insert_one(doc)
        return result.inserted_id
    
    @staticmethod
    def find_all():
        return list(goals_collection.find())

class Investment:
    """MongoDB Investment document helper"""
    @staticmethod
    def create(ticker, quantity, purchase_price, purchase_date):
        doc = {
            'ticker': str(ticker),
            'quantity': float(quantity),
            'purchase_price': float(purchase_price),
            'purchase_date': purchase_date if isinstance(purchase_date, datetime) else datetime.fromisoformat(str(purchase_date))
        }
        result = investments_collection.insert_one(doc)
        return result.inserted_id
    
    @staticmethod
    def find_all():
        return list(investments_collection.find())

class ChatHistory:
    """MongoDB ChatHistory document helper"""
    @staticmethod
    def create(user_message, ai_response):
        doc = {
            'user_message': str(user_message),
            'ai_response': str(ai_response),
            'timestamp': datetime.utcnow()
        }
        result = chat_history_collection.insert_one(doc)
        return result.inserted_id
    
    @staticmethod
    def find_recent(limit=10):
        return list(chat_history_collection.find().sort('timestamp', -1).limit(limit))

# Simplified database access
class DB:
    @staticmethod
    def get_transactions():
        return transactions_collection
    
    @staticmethod
    def get_categories():
        return categories_collection
    
    @staticmethod
    def get_budgets():
        return budgets_collection
    
    @staticmethod
    def get_chat_history():
        return chat_history_collection

def get_db():
    """Return database instance for use in other modules"""
    return db