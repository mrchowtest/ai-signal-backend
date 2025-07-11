import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def fetch_signals():
    if not BACKEND_URL:
        raise ValueError("Missing BACKEND_URL")

    url = f"{BACKEND_URL.rstrip('/')}/signals"
    res = requests.get(url)
    res.raise_for_status()
    return res.json().get("signals", [])

def send_telegram_message(message):
    if not TELEGRAM_API_KEY or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram credentials missing.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    res = requests.post(url, json=payload)
    if res.ok:
        print("✅ Daily summary sent to Telegram.")
    else:
        print("❌ Telegram error:", res.text)

def run():
    now = datetime.now(timezone.utc)
    today = now.date()

    try:
        signals = fetch_signals()
        today_signals = [s for s in signals if s.get("entry_ready") and s.get("timestamp", "").startswith(str(today))]

        if not today_signals:
            send_telegram_message("📭 *No entry-ready signals were triggered today.*")
            return

        summary_lines = [f"📊 *Daily Signal Summary for {today}*"]
        for signal in today_signals:
            pair = signal["pair"]
            entry = signal["entry_price"]
            live = signal["live_price"]
            delta = round(float(live) - float(entry), 5)
            summary_lines.append(
                f"\n*{pair}* - {signal['action']} | 🎯 Entry: {entry} | 💰 Live: {live} | Δ {delta}"
            )

        summary = "\n".join(summary_lines)
        send_telegram_message(summary)

    except Exception as e:
        print(f"❌ Error creating daily summary: {e}")

if __name__ == "__main__":
    run()
