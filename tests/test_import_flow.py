import os
from pathlib import Path
from uuid import uuid4
import pytest
from core.parser import import_transactions
from core.db import Transaction, get_db_status
import importlib

@pytest.fixture
def test_db(monkeypatch):
    db_path = Path("data") / f"test-import-{uuid4().hex}.db"
    db_path.parent.mkdir(exist_ok=True)
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_DB_PATH", str(db_path))
    
    import core.db as db_module
    db_module = importlib.reload(db_module)
    
    yield db_module
    
    # Cleanup
    conn = getattr(db_module, "_sqlite_conn", None)
    if conn is not None:
        conn.close()
        db_module._sqlite_conn = None
    if db_path.exists():
        db_path.unlink()

def test_full_import_flow(test_db):
    sample_csv = Path("sample_statements") / "statement_2026_04.csv"
    if not sample_csv.exists():
        pytest.skip("Sample CSV not found")
        
    # 1. Import from CSV
    transactions = import_transactions(str(sample_csv))
    assert len(transactions) > 0
    
    # 2. Save to DB
    for tx in transactions:
        inserted_id = Transaction.create(
            tx["date"].isoformat(),
            tx["amount"],
            tx["description"],
            tx["category"]
        )
        assert inserted_id
        
    # 3. Verify in DB
    saved_transactions = Transaction.find_all()
    assert len(saved_transactions) == len(transactions)
    
    # Check one transaction
    first_tx = saved_transactions[0]
    assert "amount" in first_tx
    assert "description" in first_tx
