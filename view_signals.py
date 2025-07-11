# view_signals.py
import sqlite3
import os

DB_NAME = "signals.db"

def show_signals(limit=10):
    if not os.path.exists(DB_NAME):
        print("⚠️ signals.db does not exist.")
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("SELECT * FROM signals ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        if rows:
            for row in rows:
                print(row)
        else:
            print("📭 No signals found.")
    except sqlite3.OperationalError:
        print("⚠️ Table 'signals' does not exist. Has demo_tracker.py run yet?")
    conn.close()

if __name__ == "__main__":
    show_signals()
