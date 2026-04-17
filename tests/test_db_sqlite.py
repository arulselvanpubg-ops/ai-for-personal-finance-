import importlib
from pathlib import Path
from uuid import uuid4


def _db_path():
    path = Path("data") / f"test-{uuid4().hex}.db"
    path.parent.mkdir(exist_ok=True)
    return path


def _cleanup(db_module, db_path):
    conn = getattr(db_module, "_sqlite_conn", None)
    if conn is not None:
        conn.close()
        db_module._sqlite_conn = None
    if db_path.exists():
        db_path.unlink()


def test_sqlite_fallback_status(monkeypatch):
    db_path = _db_path()
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_DB_PATH", str(db_path))

    import core.db as db_module

    db_module = importlib.reload(db_module)
    status = db_module.get_db_status()

    assert status["ok"] is True
    assert status["backend"] == "sqlite"

    _cleanup(db_module, db_path)


def test_sqlite_user_and_transaction_flow(monkeypatch):
    db_path = _db_path()
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_DB_PATH", str(db_path))

    import core.auth as auth_module
    import core.db as db_module

    db_module = importlib.reload(db_module)
    auth_module = importlib.reload(auth_module)

    result = auth_module.User.register("test@example.com", "longpassword", "Tester")
    assert result["success"] is True

    login = auth_module.User.login("test@example.com", "longpassword")
    assert login["success"] is True

    inserted_id = db_module.Transaction.create(
        "2026-04-17T00:00:00",
        -15.25,
        "Coffee",
        "Food & Dining",
    )
    assert inserted_id
    assert len(db_module.Transaction.find_all()) == 1

    _cleanup(db_module, db_path)
