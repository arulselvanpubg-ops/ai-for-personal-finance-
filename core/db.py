import os
import sqlite3
from datetime import datetime

from pymongo import MongoClient
from utils.monitoring import log_event

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
    SUPABASE_URL = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
except Exception:
    MONGODB_URI = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "finsight")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", os.path.join("data", "finsight.db"))

try:
    import certifi

    CA_BUNDLE = certifi.where()
except ImportError:
    CA_BUNDLE = None

try:
    from supabase import create_client

    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

_mongo_client = None
_mongo_db = None
_sqlite_conn = None
_supabase_client = None
_backend = None
_backend_message = None
_backend_error = None

DATETIME_FIELDS = {
    "date",
    "created_at",
    "target_date",
    "purchase_date",
    "timestamp",
    "last_login",
}
DEFAULT_CATEGORIES = [
    "Food & Dining",
    "Transportation",
    "Shopping",
    "Entertainment",
    "Bills & Utilities",
    "Healthcare",
    "Education",
    "Travel",
    "Other",
]


class InsertResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


def _serialize_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _deserialize_doc(doc):
    parsed = dict(doc)
    for field in DATETIME_FIELDS:
        value = parsed.get(field)
        if isinstance(value, str):
            try:
                parsed[field] = datetime.fromisoformat(value)
            except ValueError:
                pass
    return parsed


def _sqlite_row_to_doc(row):
    doc = dict(row)
    if "id" in doc:
        doc["_id"] = str(doc["id"])
    return _deserialize_doc(doc)


def _matches_filter(doc, query):
    if not query:
        return True

    for key, expected in query.items():
        actual = doc.get(key)
        if key == "_id" and actual is None and "id" in doc:
            actual = str(doc["id"])
        if isinstance(expected, dict):
            for operator, value in expected.items():
                compare_value = _serialize_value(value)
                actual_value = _serialize_value(actual)
                if operator == "$gte" and not (actual_value >= compare_value):
                    return False
                if operator == "$gt" and not (actual_value > compare_value):
                    return False
                if operator == "$lte" and not (actual_value <= compare_value):
                    return False
                if operator == "$lt" and not (actual_value < compare_value):
                    return False
            continue
        if str(actual) != str(expected):
            return False
    return True


def get_mongo_client(uri):
    if not uri:
        raise RuntimeError("MongoDB URI is not configured.")

    base_kwargs = {
        "serverSelectionTimeoutMS": 1500,
        "connectTimeoutMS": 1500,
        "socketTimeoutMS": 1500,
    }
    attempts = [base_kwargs]

    if CA_BUNDLE:
        attempts.append({**base_kwargs, "tlsCAFile": CA_BUNDLE})

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


def _ensure_sqlite():
    global _sqlite_conn

    if _sqlite_conn is not None:
        return _sqlite_conn

    sqlite_dir = os.path.dirname(SQLITE_DB_PATH)
    if sqlite_dir:
        os.makedirs(sqlite_dir, exist_ok=True)

    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT
        );
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            notes TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            budget REAL NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id TEXT NOT NULL,
            month TEXT NOT NULL,
            amount REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL NOT NULL,
            target_date TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS investments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            quantity REAL NOT NULL,
            purchase_price REAL NOT NULL,
            purchase_date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_message TEXT NOT NULL,
            ai_response TEXT NOT NULL,
            timestamp TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
        CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
        CREATE INDEX IF NOT EXISTS idx_budgets_month ON budgets(month);
        CREATE INDEX IF NOT EXISTS idx_chat_history_timestamp ON chat_history(timestamp);
        """
    )

    existing_categories = conn.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
    if existing_categories == 0:
        conn.executemany(
            "INSERT INTO categories (name, budget) VALUES (?, ?)",
            [(category, 0.0) for category in DEFAULT_CATEGORIES],
        )
        conn.commit()

    _sqlite_conn = conn
    return _sqlite_conn


def _ensure_supabase():
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_AVAILABLE:
        raise RuntimeError("supabase-py is not installed. Run: pip install supabase")

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("SUPABASE_URL and SUPABASE_KEY environment variables are required")

    try:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Test the connection by querying the users table
        _supabase_client.table("users").select("id").limit(1).execute()
        return _supabase_client
    except Exception as exc:
        raise RuntimeError(f"Failed to connect to Supabase: {exc}")


def _select_backend():
    global _backend, _backend_error, _backend_message, _mongo_client, _mongo_db, _supabase_client

    if _backend is not None:
        return _backend

    requested_backend = os.getenv("DB_BACKEND", "auto").lower()

    if requested_backend == "supabase":
        try:
            _ensure_supabase()
            _backend = "supabase"
            _backend_message = f"Connected to Supabase database at `{SUPABASE_URL}`."
            log_event("info", "db_backend_selected", backend=_backend, url=SUPABASE_URL)
            return _backend
        except Exception as exc:
            _backend_error = str(exc)
            raise

    if requested_backend == "sqlite":
        _ensure_sqlite()
        _backend = "sqlite"
        _backend_message = f"Using SQLite database at `{SQLITE_DB_PATH}`."
        log_event("info", "db_backend_selected", backend=_backend, path=SQLITE_DB_PATH)
        return _backend

    if requested_backend == "mongodb" or (requested_backend == "auto" and MONGODB_URI):
        if MONGODB_URI:
            try:
                _mongo_client = get_mongo_client(MONGODB_URI)
                _mongo_db = _mongo_client[MONGODB_DB_NAME]
                _backend = "mongodb"
                _backend_message = f"Connected to MongoDB database `{MONGODB_DB_NAME}`."
                log_event("info", "db_backend_selected", backend=_backend, database=MONGODB_DB_NAME)
                return _backend
            except Exception as exc:
                _backend_error = str(exc)
                if requested_backend == "mongodb":
                    raise

    if requested_backend == "auto" and SUPABASE_URL and SUPABASE_KEY and SUPABASE_AVAILABLE:
        try:
            _ensure_supabase()
            _backend = "supabase"
            _backend_message = f"Connected to Supabase database at `{SUPABASE_URL}`."
            log_event("info", "db_backend_selected", backend=_backend, url=SUPABASE_URL)
            return _backend
        except Exception as exc:
            _backend_error = str(exc)

    _ensure_sqlite()
    _backend = "sqlite"
    if _backend_error:
        _backend_message = f"Using SQLite fallback at `{SQLITE_DB_PATH}` because the primary backend is unavailable."
        log_event(
            "warning",
            "db_backend_fallback",
            backend="sqlite",
            path=SQLITE_DB_PATH,
            reason=_backend_error,
        )
    else:
        _backend_message = f"Using SQLite database at `{SQLITE_DB_PATH}`."
        log_event("info", "db_backend_selected", backend=_backend, path=SQLITE_DB_PATH)
    return _backend


def get_backend_name():
    return _select_backend()


def get_db_status():
    try:
        backend = _select_backend()
        status = {
            "ok": True,
            "backend": backend,
            "message": _backend_message,
        }
        if _backend_error:
            status["fallback_reason"] = _backend_error
        return status
    except Exception as exc:
        return {
            "ok": False,
            "backend": None,
            "message": str(exc),
        }


def get_db():
    backend = _select_backend()
    if backend == "mongodb":
        return _mongo_db
    elif backend == "supabase":
        return _supabase_client
    return _ensure_sqlite()


class SQLiteCollection:
    def __init__(self, table_name):
        self.table_name = table_name

    def create_index(self, *args, **kwargs):
        return None

    def insert_one(self, doc):
        conn = _ensure_sqlite()
        payload = {key: _serialize_value(value) for key, value in doc.items()}
        columns = ", ".join(payload.keys())
        placeholders = ", ".join(["?"] * len(payload))
        cursor = conn.execute(
            f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})",
            list(payload.values()),
        )
        conn.commit()
        return InsertResult(cursor.lastrowid)

    def find(self, query=None):
        conn = _ensure_sqlite()
        rows = conn.execute(f"SELECT * FROM {self.table_name}").fetchall()
        docs = [_sqlite_row_to_doc(row) for row in rows]
        return [doc for doc in docs if _matches_filter(doc, query)]

    def find_one(self, query=None):
        results = self.find(query)
        return results[0] if results else None

    def update_one(self, query, update):
        conn = _ensure_sqlite()
        existing = self.find_one(query)
        if not existing:
            return None

        updates = {key: _serialize_value(value) for key, value in update.get("$set", {}).items()}
        if not updates:
            return None

        assignments = ", ".join(f"{key} = ?" for key in updates.keys())
        values = list(updates.values()) + [int(existing["id"])]
        conn.execute(
            f"UPDATE {self.table_name} SET {assignments} WHERE id = ?",
            values,
        )
        conn.commit()
        return None

    def delete_one(self, query):
        conn = _ensure_sqlite()
        existing = self.find_one(query)
        if not existing:
            return None
            
        conn.execute(
            f"DELETE FROM {self.table_name} WHERE id = ?",
            (int(existing["id"]),)
        )
        conn.commit()
        return None

    def delete_many(self, query=None):
        conn = _ensure_sqlite()
        if query is None:
            # Delete all records
            conn.execute(f"DELETE FROM {self.table_name}")
        else:
            # Delete records matching query (for simplicity, we'll find and delete one by one)
            docs = self.find(query)
            for doc in docs:
                conn.execute(f"DELETE FROM {self.table_name} WHERE id = ?", (int(doc["id"]),))
        conn.commit()
        return None


class SupabaseCollection:
    """Wrapper for Supabase table operations compatible with MongoDB-like interface."""

    def __init__(self, table_name):
        self.table_name = table_name

    def create_index(self, *args, **kwargs):
        """Supabase handles indexing automatically."""
        return None

    def insert_one(self, doc):
        """Insert a document into Supabase table."""
        global _supabase_client
        if _supabase_client is None:
            raise RuntimeError("Supabase client not initialized")

        payload = {key: _serialize_value(value) for key, value in doc.items()}
        response = _supabase_client.table(self.table_name).insert(payload).execute()

        if response.data and len(response.data) > 0:
            return InsertResult(response.data[0].get("id"))
        raise RuntimeError("Failed to insert into Supabase")

    def find(self, query=None):
        """Find documents in Supabase table."""
        global _supabase_client
        if _supabase_client is None:
            raise RuntimeError("Supabase client not initialized")

        try:
            response = _supabase_client.table(self.table_name).select("*").execute()
            docs = response.data if response.data else []

            # Convert to consistent format and apply filters
            for doc in docs:
                if "id" in doc and "_id" not in doc:
                    doc["_id"] = str(doc["id"])

            if query:
                return [doc for doc in docs if _matches_filter(_deserialize_doc(doc), query)]
            return [_deserialize_doc(doc) for doc in docs]
        except Exception as exc:
            log_event("error", "supabase_find_error", table=self.table_name, error=str(exc))
            return []

    def find_one(self, query=None):
        """Find a single document in Supabase table."""
        results = self.find(query)
        return results[0] if results else None

    def update_one(self, query, update):
        """Update a document in Supabase table."""
        global _supabase_client
        if _supabase_client is None:
            raise RuntimeError("Supabase client not initialized")

        existing = self.find_one(query)
        if not existing:
            return None

        updates = {
            key: _serialize_value(value) for key, value in update.get("$set", {}).items()
        }
        if not updates:
            return None

        doc_id = existing.get("id") or existing.get("_id")
        _supabase_client.table(self.table_name).update(updates).eq("id", doc_id).execute()
        return None

    def delete_one(self, query):
        """Delete a document in Supabase table."""
        global _supabase_client
        if _supabase_client is None:
            raise RuntimeError("Supabase client not initialized")

        existing = self.find_one(query)
        if not existing:
            return None

        doc_id = existing.get("id") or existing.get("_id")
        _supabase_client.table(self.table_name).delete().eq("id", doc_id).execute()
        return None

    def delete_many(self, query=None):
        """Delete documents in Supabase table."""
        global _supabase_client
        if _supabase_client is None:
            raise RuntimeError("Supabase client not initialized")

        if query is None:
            # Delete all records
            _supabase_client.table(self.table_name).delete().execute()
        else:
            # Delete records matching query (for simplicity, we'll find and delete one by one)
            docs = self.find(query)
            for doc in docs:
                doc_id = doc.get("id") or doc.get("_id")
                _supabase_client.table(self.table_name).delete().eq("id", doc_id).execute()
        return None


def get_collection(name: str):
    backend = _select_backend()
    if backend == "mongodb":
        return _mongo_db[name]
    elif backend == "supabase":
        return SupabaseCollection(name)
    return SQLiteCollection(name)


class Transaction:
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
            "created_at": datetime.now(),
        }
        result = Transaction._collection().insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_by_date_range(start_date, end_date):
        results = Transaction._collection().find(
            {"date": {"$gte": start_date, "$lt": end_date}}
        )
        return sorted(results, key=lambda item: item["date"], reverse=True)

    @staticmethod
    def find_all():
        results = Transaction._collection().find()
        return sorted(results, key=lambda item: item["date"], reverse=True)

    @staticmethod
    def seed_dummy_data():
        """Seed the database with sample transactions, goals, and investments."""
        # Avoid circular import
        from ui.dummy_data import _raw_txns, _d, DUMMY_GOALS, DUMMY_INVESTMENTS
        
        # Clear existing data
        Transaction._collection().delete_many({})
        from core.db import Goal, Investment
        Goal._collection().delete_many({})
        Investment._collection().delete_many({})
        
        # Seed Transactions
        for i, (amt, desc, cat) in enumerate(_raw_txns):
            Transaction.create(
                date=datetime.combine(_d(i * 2), datetime.min.time()),
                amount=amt,
                description=desc,
                category=cat,
                notes="Sample transaction"
            )
            
        # Seed Goals
        for g in DUMMY_GOALS:
            Goal.create(
                name=g["name"],
                target_amount=g["target_amount"],
                current_amount=g["current_amount"],
                target_date=g["target_date"]
            )
            
        # Seed Investments
        for inv in DUMMY_INVESTMENTS:
            Investment.create(
                ticker=inv["ticker"],
                quantity=inv["quantity"],
                purchase_price=inv["purchase_price"],
                purchase_date=inv["purchase_date"]
            )
            
        return len(_raw_txns)

    @staticmethod
    def update(transaction_id, update_data):
        Transaction._collection().update_one({"_id": str(transaction_id)}, {"$set": update_data})

    @staticmethod
    def delete(transaction_id):
        Transaction._collection().delete_one({"_id": str(transaction_id)})


class Category:
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
        categories = Category._collection().find()
        return sorted(categories, key=lambda item: item["name"].lower())

    @staticmethod
    def update_budget(name, budget):
        Category._collection().update_one(
            {"name": name},
            {"$set": {"budget": float(budget)}},
        )


class Budget:
    @staticmethod
    def _collection():
        return get_collection("budgets")

    @staticmethod
    def create(category_id, month, amount):
        existing = Budget._collection().find_one(
            {"category_id": str(category_id), "month": str(month)}
        )
        if existing:
            Budget._collection().update_one(
                {"_id": existing["_id"]},
                {"$set": {"amount": float(amount)}},
            )
            return existing["_id"]

        doc = {
            "category_id": str(category_id),
            "month": str(month),
            "amount": float(amount),
        }
        result = Budget._collection().insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_by_month(month):
        return Budget._collection().find({"month": str(month)})


class Goal:
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
            "created_at": datetime.now(),
        }
        result = Goal._collection().insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_all():
        results = Goal._collection().find()
        return sorted(results, key=lambda item: item.get("created_at", datetime.min), reverse=True)

    @staticmethod
    def update(goal_id, update_data):
        Goal._collection().update_one({"_id": str(goal_id)}, {"$set": update_data})

    @staticmethod
    def delete(goal_id):
        Goal._collection().delete_one({"_id": str(goal_id)})


class Investment:
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
        return Investment._collection().find()

    @staticmethod
    def update(investment_id, update_data):
        Investment._collection().update_one({"_id": str(investment_id)}, {"$set": update_data})

    @staticmethod
    def delete(investment_id):
        Investment._collection().delete_one({"_id": str(investment_id)})


class ChatHistory:
    @staticmethod
    def _collection():
        return get_collection("chat_history")

    @staticmethod
    def create(user_message, ai_response):
        doc = {
            "user_message": str(user_message),
            "ai_response": str(ai_response),
            "timestamp": datetime.now(),
        }
        result = ChatHistory._collection().insert_one(doc)
        return result.inserted_id

    @staticmethod
    def find_recent(limit=10):
        results = ChatHistory._collection().find()
        results = sorted(results, key=lambda item: item["timestamp"], reverse=True)
        return results[:limit]


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
