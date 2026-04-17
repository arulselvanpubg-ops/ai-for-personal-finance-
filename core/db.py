from datetime import datetime

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

from utils.helpers import get_env

_client = None
_db = None
_connection_error = None


def _get_mongo_config():
    """Read MongoDB config from Streamlit secrets or environment variables."""
    return {
        "uri": get_env("MONGODB_URI"),
        "db_name": get_env("MONGODB_DB_NAME", "finsight"),
    }


def is_db_configured() -> bool:
    """Return True when the MongoDB URI is available."""
    config = _get_mongo_config()
    return bool(config["uri"])


def get_db_status() -> dict:
    """Provide a user-friendly status for UI checks."""
    config = _get_mongo_config()

    if not config["uri"]:
        return {
            "ok": False,
            "message": (
                "MongoDB is not configured. Set `MONGODB_URI` in Streamlit Secrets "
                "or in your local `.env` file."
            ),
        }

    if _connection_error:
        return {
            "ok": False,
            "message": f"MongoDB connection failed: {_connection_error}",
        }

    return {"ok": True, "message": ""}


def get_db():
    """Return a connected MongoDB database instance."""
    global _client, _db, _connection_error

    if _db is not None:
        return _db

    config = _get_mongo_config()
    if not config["uri"]:
        raise RuntimeError(
            "MongoDB is not configured. Set MONGODB_URI in Streamlit Secrets or .env."
        )

    try:
        _client = MongoClient(config["uri"], serverSelectionTimeoutMS=5000)
        _client.admin.command("ping")
        _db = _client[config["db_name"]]
        _connection_error = None
        return _db
    except ConnectionFailure as exc:
        _connection_error = exc
        raise RuntimeError(f"Failed to connect to MongoDB: {exc}") from exc


def get_collection(name: str):
    """Return a collection from the configured database."""
    return get_db()[name]


def ensure_indexes():
    """Create indexes after the first successful connection."""
    try:
        get_collection("transactions").create_index("date")
        get_collection("transactions").create_index("category")
        get_collection("budgets").create_index("month")
        get_collection("chat_history").create_index("timestamp")
        get_collection("users").create_index("email", unique=True)
    except PyMongoError:
        # Index creation should not block the app from starting.
        pass


class Transaction:
    """MongoDB Transaction document helper."""

    @staticmethod
    def create(date, amount, description, category, notes=None):
        doc = {
            "date": date if isinstance(date, datetime) else datetime.fromisoformat(str(date)),
            "amount": float(amount),
            "description": str(description),
            "category": str(category),
            "notes": notes,
            "created_at": datetime.utcnow(),
        }
        result = get_collection("transactions").insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_by_date_range(start_date, end_date):
        return list(
            get_collection("transactions")
            .find({"date": {"$gte": start_date, "$lt": end_date}})
            .sort("date", -1)
        )

    @staticmethod
    def find_all():
        return list(get_collection("transactions").find().sort("date", -1))


class Category:
    """MongoDB Category document helper."""

    @staticmethod
    def create(name, budget=0.0):
        doc = {"name": str(name), "budget": float(budget)}
        result = get_collection("categories").insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_all():
        return list(get_collection("categories").find())

    @staticmethod
    def update_budget(name, budget):
        get_collection("categories").update_one(
            {"name": name},
            {"$set": {"budget": float(budget)}},
        )


class Budget:
    """MongoDB Budget document helper."""

    @staticmethod
    def create(category_id, month, amount):
        doc = {
            "category_id": category_id,
            "month": str(month),
            "amount": float(amount),
        }
        result = get_collection("budgets").insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_by_month(month):
        return list(get_collection("budgets").find({"month": month}))


class Goal:
    """MongoDB Goal document helper."""

    @staticmethod
    def create(name, target_amount, target_date, current_amount=0.0):
        doc = {
            "name": str(name),
            "target_amount": float(target_amount),
            "current_amount": float(current_amount),
            "target_date": (
                target_date
                if isinstance(target_date, datetime)
                else datetime.fromisoformat(str(target_date))
            ),
            "created_at": datetime.utcnow(),
        }
        result = get_collection("goals").insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_all():
        return list(get_collection("goals").find())


class Investment:
    """MongoDB Investment document helper."""

    @staticmethod
    def create(ticker, quantity, purchase_price, purchase_date):
        doc = {
            "ticker": str(ticker),
            "quantity": float(quantity),
            "purchase_price": float(purchase_price),
            "purchase_date": (
                purchase_date
                if isinstance(purchase_date, datetime)
                else datetime.fromisoformat(str(purchase_date))
            ),
        }
        result = get_collection("investments").insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_all():
        return list(get_collection("investments").find())


class ChatHistory:
    """MongoDB ChatHistory document helper."""

    @staticmethod
    def create(user_message, ai_response):
        doc = {
            "user_message": str(user_message),
            "ai_response": str(ai_response),
            "timestamp": datetime.utcnow(),
        }
        result = get_collection("chat_history").insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_recent(limit=10):
        return list(get_collection("chat_history").find().sort("timestamp", -1).limit(limit))


class DB:
    @staticmethod
    def get_transactions():
        return get_collection("transactions")

    @staticmethod
    def get_categories():
        return get_collection("categories")

    @staticmethod
    def get_budgets():
        return get_collection("budgets")

    @staticmethod
    def get_chat_history():
        return get_collection("chat_history")


ensure_indexes()
