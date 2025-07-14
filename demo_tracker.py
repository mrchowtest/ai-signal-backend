import requests
import os
import sqlite3
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")

DB_NAME = "signals.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pair TEXT,
            action TEXT,
            confidence_level INTEGER,
            entry_price REAL,
            live_price REAL,
            take_profit REAL,
            stop_loss REAL,
            timestamp TEXT,
            risk_reward_ratio REAL
        )
    """)
    conn.commit()
    conn.close()

def is_peak_hours():
    now = datetime.now(timezone.utc)
    if now.weekday() >= 5:
        return False  # Saturday or Sunday
    return (0 <= now.hour < 3) or (6 <= now.hour < 10) or (12 <= now.hour < 16)

def fetch_signals():
    if not BACKEND_URL:
        print("❌ BACKEND_URL is not set.")
        return []
    try:
        res = requests.get(f"{BACKEND_URL}/analyze", timeout=30)
        res.raise_for_status()
        data = res.json()
        return data.get("signals", [])
    except Exception as e:
        print(f"❌ Error fetching/analyzing signals: {e}")
        return []

def log_signal_to_db(signal):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("""
            INSERT INTO signals (
                pair, action, confidence_level, entry_price, live_price,
                take_profit, stop_loss, timestamp, risk_reward_ratio
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal.get("pair"),
            signal.get("action"),
            signal.get("confidence_level"),
            signal.get("entry_price"),
            signal.get("live_price"),
            signal.get("take_profit"),
            signal.get("stop_loss"),
            signal.get("timestamp"),
            signal.get("risk_reward_ratio")
        ))
        conn.commit()
        conn.close()
        print(f"✅ Logged to DB: {signal.get('pair')} @ {signal.get('entry_price')}")
    except Exception as e:
        print(f"⚠️ DB logging error: {e}")

def track_openai_usage():
    if not OPENAI_API_KEY:
        return
    try:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        r = requests.get("https://api.openai.com/v1/dashboard/billing/usage", headers=headers)
        usage = r.json()
        print(f"💳 OpenAI usage: {usage}")
    except Exception as e:
        print(f"⚠️ Usage tracking error: {e}")

def main():
    now = datetime.now(timezone.utc)
    print(f"\n⏱️ Checking at {now.isoformat()}")

    if not is_peak_hours():
        print("⏸️ Outside trading hours. Skipping.")
        return

    signals = fetch_signals()
    print(f"📈 Fetched {len(signals)} signals.")

    if not TWELVE_API_KEY:
        print("⚠️ No Twelve Data API key provided.")

    count = 0
    for s in signals:
        if s.get("entry_ready"):
            log_signal_to_db(s)
            count += 1

    print(f"📬 Total entry-ready signals stored: {count}")
    track_openai_usage()

if __name__ == "__main__":
    init_db()
    main()
