import os
from datetime import datetime

from pymongo import MongoClient

# MongoDB connection setup
# Try to get from Streamlit secrets first (for Streamlit Cloud), then from environment variables
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

try:
    import streamlit as st

    MONGODB_URI = st.secrets.get("MONGODB_URI") or os.getenv("MONGODB_URI")
    MONGODB_DB_NAME = st.secrets.get(
        "MONGODB_DB_NAME",
        os.getenv("MONGODB_DB_NAME", "finsight"),
    )
except Exception:
    # Streamlit secrets are unavailable, so fall back to environment variables.
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "finsight")

try:
    import certifi

    CA_BUNDLE = certifi.where()
except ImportError:
    CA_BUNDLE = None


def get_mongo_client(uri):
    if not uri:
        raise RuntimeError(
            "MongoDB is not configured. Set `MONGODB_URI` in Streamlit secrets or environment variables."
        )

    base_kwargs = {"serverSelectionTimeoutMS": 5000}
    attempts = [base_kwargs]

    if CA_BUNDLE:
        attempts.append({**base_kwargs, "tlsCAFile": CA_BUNDLE})

    # Narrow fallback for environments that fail during certificate revocation checks.
    attempts.append({**base_kwargs, "tlsDisableOCSPEndpointCheck": True})
    if CA_BUNDLE:
        attempts.append(
            {
                **base_kwargs,
                "tlsCAFile": CA_BUNDLE,
                "tlsDisableOCSPEndpointCheck": True,
            }
        )

    last_exc = None
    for attempt_kwargs in attempts:
        try:
            client = MongoClient(uri, **attempt_kwargs)
            client.admin.command("ping")
            return client
        except Exception as exc:
            last_exc = exc

    raise last_exc


client = None
_db = None
_indexes_initialized = False


def _create_indexes():
    global _indexes_initialized
    if _indexes_initialized:
        return

    get_collection("transactions").create_index("date")
    get_collection("transactions").create_index("category")
    get_collection("budgets").create_index("month")
    get_collection("chat_history").create_index("timestamp")
    get_collection("users").create_index("email", unique=True)

    _indexes_initialized = True


def _init_db():
    global client, _db

    if _db is not None:
        return _db

    client = get_mongo_client(MONGODB_URI)
    _db = client[MONGODB_DB_NAME]

    _create_indexes()

    return _db


def get_db_status():
    try:
        _init_db()
        return {"ok": True, "message": f"Connected to MongoDB database '{MONGODB_DB_NAME}'"}
    except Exception as exc:
        return {"ok": False, "message": str(exc)}


def get_db():
    """Return database instance for use in other modules."""
    return _db if _db is not None else _init_db()


def get_collection(name: str):
    """Return a collection from the configured database."""
    db = _init_db()
    return db[name]


class Transaction:
    """MongoDB Transaction document helper."""

    @staticmethod
    def _collection():
        return get_collection("transactions")

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
        result = Transaction._collection().insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_by_date_range(start_date, end_date):
        return list(
            Transaction._collection()
            .find({"date": {"$gte": start_date, "$lt": end_date}})
            .sort("date", -1)
        )

    @staticmethod
    def find_all():
        return list(Transaction._collection().find().sort("date", -1))


class Category:
    """MongoDB Category document helper."""

    @staticmethod
    def _collection():
        return get_collection("categories")

    @staticmethod
    def create(name, budget=0.0):
        doc = {"name": str(name), "budget": float(budget)}
        result = Category._collection().insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_all():
        return list(Category._collection().find())

    @staticmethod
    def update_budget(name, budget):
        Category._collection().update_one(
            {"name": name},
            {"$set": {"budget": float(budget)}},
        )


class Budget:
    """MongoDB Budget document helper."""

    @staticmethod
    def _collection():
        return get_collection("budgets")

    @staticmethod
    def create(category_id, month, amount):
        doc = {
            "category_id": category_id,
            "month": str(month),
            "amount": float(amount),
        }
        result = Budget._collection().insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_by_month(month):
        return list(Budget._collection().find({"month": month}))


class Goal:
    """MongoDB Goal document helper."""

    @staticmethod
    def _collection():
        return get_collection("goals")

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
        result = Goal._collection().insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_all():
        return list(Goal._collection().find())


class Investment:
    """MongoDB Investment document helper."""

    @staticmethod
    def _collection():
        return get_collection("investments")

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
        result = Investment._collection().insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_all():
        return list(Investment._collection().find())


class ChatHistory:
    """MongoDB ChatHistory document helper."""

    @staticmethod
    def _collection():
        return get_collection("chat_history")

    @staticmethod
    def create(user_message, ai_response):
        doc = {
            "user_message": str(user_message),
            "ai_response": str(ai_response),
            "timestamp": datetime.utcnow(),
        }
        result = ChatHistory._collection().insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_recent(limit=10):
        return list(ChatHistory._collection().find().sort("timestamp", -1).limit(limit))


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
