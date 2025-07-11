import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

# Load local .env if available (safe fallback for local testing)
load_dotenv()

# Get environment variables
BACKEND_URL = os.getenv("BACKEND_URL")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Validate required env vars
if not BACKEND_URL:
    raise ValueError("❌ BACKEND_URL is not set. Check your Render Environment Variables.")
if not TELEGRAM_API_KEY or not TELEGRAM_CHAT_ID:
    raise ValueError("❌ Telegram API Key or Chat ID missing in environment variables.")

def fetch_signals():
    try:
        print(f"⏱️ Checking for signals at {datetime.utcnow().isoformat()}Z")
        response = requests.get(f"{BACKEND_URL}/analyze")
        response.raise_for_status()
        return response.json().get("signals", [])
    except Exception as e:
        print(f"❌ Error fetching/analyzing signals: {e}")
        return []

def format_signal_message(signal):
    return f"""
🔔🔔🔔 *NEW SIGNAL* 🔔🔔🔔

*Pair:* {signal['pair']}
*Action:* {signal['action']}
*Trend:* {signal['trend_direction'].title()}
*Confidence:* {signal['confidence_level']}%
*Entry Price:* {signal['entry_price']}
*Live Price:* {signal['live_price']}
*Distance to Entry:* {round(signal['distance_to_entry'], 5)}
*Take Profit:* {signal['take_profit']}
*Stop Loss:* {signal['stop_loss']}
🟢 *Entry Ready:* {'✅ YES' if signal['entry_ready'] else '❌ NO'}
""".strip()

def send_telegram_alert(message):
    try:
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(telegram_url, json=payload)
        print(f"📬 Telegram sent: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def main():
    signals = fetch_signals()
    ready_signals = [s for s in signals if s.get("entry_ready") is True]

    if not ready_signals:
        print("📭 No entry-ready signals at this time.")
        return

    for signal in ready_signals:
        msg = format_signal_message(signal)
        send_telegram_alert(msg)

if __name__ == "__main__":
    main()
