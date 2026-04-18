import sqlite3
import os

db_path = os.path.join("data", "finsight.db")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM transactions")
        conn.execute("DELETE FROM goals")
        conn.execute("DELETE FROM investments")
        conn.execute("DELETE FROM budgets")
        conn.execute("DELETE FROM chat_history")
        conn.commit()
        print("Database cleared successfully.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()
else:
    print("Database not found.")
