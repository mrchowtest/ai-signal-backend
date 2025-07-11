import os
import sqlite3
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import requests

load_dotenv()

TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DB_NAME = "signals.db"

def get_today_summary():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now

    c.execute("""
        SELECT pair, action, confidence_level, entry_price, live_price,
               take_profit, stop_loss, timestamp, risk_reward_ratio
        FROM signals
        WHERE timestamp BETWEEN ? AND ?
        ORDER BY timestamp ASC
    """, (start.isoformat(), end.isoformat()))

    rows = c.fetchall()
    conn.close()
    return rows

def format_summary(rows):
    if not rows:
        return "📊 *Daily Summary*\n\nNo entry-ready signals were logged today."

    summary = ["📊 *Daily Signal Summary*\n"]
    for row in rows:
        (pair, action, confidence, entry, live, tp, sl, ts, rr) = row
        delta = round(abs(live - entry), 5)
        summary.append(
            f"\n*Pair:* {pair}\n"
            f"*Action:* {action}\n"
            f"*Confidence:* {confidence}%\n"
            f"*Entry:* {entry}\n"
            f"*Live:* {live}\n"
            f"*Delta:* {delta}\n"
            f"*TP:* {tp} | *SL:* {sl}\n"
            f"*R/R:* {rr}\n"
            f"*Time:* {ts}\n"
            f"{'-'*20}"
        )
    return "\n".join(summary)

def send_to_telegram(message):
    if not TELEGRAM_API_KEY or not TELEGRAM_CHAT_ID:
        print("❌ Telegram credentials missing.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        r = requests.post(url, json=payload)
        print(f"📬 Telegram sent: {r.text}")
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")

def main():
    if datetime.now(timezone.utc).weekday() >= 5:
        print("🛌 Weekend. No summary sent.")
        return

    summary_rows = get_today_summary()
    message = format_summary(summary_rows)
    send_to_telegram(message)

if __name__ == "__main__":
    main()
