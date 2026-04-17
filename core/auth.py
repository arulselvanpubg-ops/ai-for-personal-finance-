import bcrypt
import hashlib
from datetime import datetime
from core.db import db

# Get users collection
users_collection = db['users']

# Create indexes for users collection
users_collection.create_index('email', unique=True)

class User:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def register(email: str, password: str, name: str) -> dict:
        """Register a new user."""
        # Check if user exists
        existing = users_collection.find_one({'email': email})
        if existing:
            return {'success': False, 'error': 'Email already registered'}
        
        # Hash password
        hashed_password = User.hash_password(password)
        
        # Create user
        user_doc = {
            'email': email,
            'password': hashed_password,
            'name': name,
            'created_at': datetime.now(),
            'last_login': None
        }
        
        result = users_collection.insert_one(user_doc)
        
        return {'success': True, 'user_id': str(result.inserted_id)}
    
    @staticmethod
    def login(email: str, password: str) -> dict:
        """Authenticate user login."""
        # Find user by email
        user = users_collection.find_one({'email': email})
        
        if not user:
            return {'success': False, 'error': 'Email not found'}
        
        # Verify password
        if not User.verify_password(password, user['password']):
            return {'success': False, 'error': 'Invalid password'}
        
        # Update last login
        users_collection.update_one(
            {'_id': user['_id']},
            {'$set': {'last_login': datetime.now()}}
        )
        
        return {
            'success': True,
            'user_id': str(user['_id']),
            'email': user['email'],
            'name': user['name']
        }
    
    @staticmethod
    def find_by_email(email: str) -> dict:
        """Get user by email."""
        return users_collection.find_one({'email': email})
    
    @staticmethod
    def find_by_id(user_id: str) -> dict:
        """Get user by ID."""
        from bson.objectid import ObjectId
        try:
            return users_collection.find_one({'_id': ObjectId(user_id)})
        except:
            return None
    
    @staticmethod
    def update_profile(user_id: str, name: str = None, email: str = None) -> dict:
        """Update user profile."""
        from bson.objectid import ObjectId
        update_data = {}
        
        if name:
            update_data['name'] = name
        if email:
            update_data['email'] = email
        
        if update_data:
            users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': update_data}
            )
        
        return {'success': True}
