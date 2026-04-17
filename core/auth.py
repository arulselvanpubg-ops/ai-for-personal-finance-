from datetime import datetime

import bcrypt

from core.db import get_backend_name, get_collection
from utils.monitoring import log_event
from utils.validators import (
    normalize_email,
    sanitize_input,
    validate_email,
    validate_name,
    validate_password,
)


class User:
    @staticmethod
    def _normalize_user_id(user_id: str):
        if get_backend_name() == "mongodb":
            from bson.objectid import ObjectId

            return ObjectId(user_id)
        return str(user_id)

    @staticmethod
    def _users_collection():
        return get_collection("users")

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash."""
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

    @staticmethod
    def register(email: str, password: str, name: str) -> dict:
        """Register a new user."""
        email = normalize_email(email)
        name = sanitize_input(name, max_length=80)

        if not validate_name(name):
            return {"success": False, "error": "Please enter a valid name."}
        if not validate_email(email):
            return {"success": False, "error": "Please enter a valid email address."}
        if not validate_password(password):
            return {"success": False, "error": "Password must be at least 8 characters."}

        users_collection = User._users_collection()
        existing = users_collection.find_one({"email": email})
        if existing:
            log_event("warning", "register_duplicate_email", email=email)
            return {"success": False, "error": "Email already registered"}

        hashed_password = User.hash_password(password)
        user_doc = {
            "email": email,
            "password": hashed_password,
            "name": name,
            "created_at": datetime.now(),
            "last_login": None,
        }

        result = users_collection.insert_one(user_doc)
        log_event("info", "register_success", email=email, user_id=result.inserted_id)
        return {"success": True, "user_id": str(result.inserted_id)}

    @staticmethod
    def login(email: str, password: str) -> dict:
        """Authenticate user login."""
        email = normalize_email(email)
        if not validate_email(email):
            return {"success": False, "error": "Please enter a valid email address."}

        users_collection = User._users_collection()
        user = users_collection.find_one({"email": email})

        if not user:
            log_event("warning", "login_email_not_found", email=email)
            return {"success": False, "error": "Email not found"}

        if not User.verify_password(password, user["password"]):
            log_event("warning", "login_invalid_password", email=email)
            return {"success": False, "error": "Invalid password"}

        users_collection.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.now()}},
        )

        log_event("info", "login_success", email=email, user_id=user["_id"])
        return {
            "success": True,
            "user_id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"],
        }

    @staticmethod
    def find_by_email(email: str) -> dict:
        """Get user by email."""
        return User._users_collection().find_one({"email": email})

    @staticmethod
    def find_by_id(user_id: str) -> dict:
        """Get user by ID."""
        try:
            return User._users_collection().find_one(
                {"_id": User._normalize_user_id(user_id)}
            )
        except Exception:
            return None

    @staticmethod
    def update_profile(user_id: str, name: str = None, email: str = None) -> dict:
        """Update user profile."""
        update_data = {}

        if name:
            update_data["name"] = name
        if email:
            update_data["email"] = email

        if update_data:
            User._users_collection().update_one(
                {"_id": User._normalize_user_id(user_id)},
                {"$set": update_data},
            )

        return {"success": True}
