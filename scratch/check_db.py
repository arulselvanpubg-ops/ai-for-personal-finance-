import sqlite3
import os

db_path = os.path.join("data", "finsight.db")
if not os.path.exists(db_path):
    print(f"Database not found at {db_path}")
else:
    conn = sqlite3.connect(db_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
        print(f"Transaction count: {count}")
        if count > 0:
            sample = conn.execute("SELECT * FROM transactions LIMIT 1").fetchone()
            print(f"Sample transaction: {sample}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
