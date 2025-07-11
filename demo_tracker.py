import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")  # e.g., https://your-backend.onrender.com
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def fetch_signals():
    try:
        response = requests.get(f"{BACKEND_URL}/analyze", timeout=15)
        response.raise_for_status()
        return response.json().get("signals", [])
    except Exception as e:
        print(f"❌ Error fetching/analyzing signals: {e}")
        return []

def format_signal_message(signal):
    return (
        f"🔔🔔🔔 *NEW SIGNAL* 🔔🔔🔔\n\n"
        f"*Action:* {signal['action']}\n"
        f"*Trend:* {signal['trend_direction'].title()}\n"
        f"*Confidence:* {signal['confidence_level']}%\n"
        f"*Entry Price:* {float(signal['entry_price']):.5f}\n"
        f"*Live Price:* {float(signal['live_price']):.5f}\n"
        f"*Distance to Entry:* {float(signal['distance_to_entry']):.5f}\n"
        f"*Take Profit:* {float(signal['take_profit']):.5f}\n"
        f"*Stop Loss:* {float(signal['stop_loss']):.5f}\n"
        f"🟢 *Entry Ready:* ✅ YES"
    )

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ Failed to send Telegram message: {response.text}")
    except Exception as e:
        print(f"❌ Telegram error: {e}")

def main():
    print(f"⏱️ Checking for signals at {datetime.utcnow().isoformat()}Z")
    signals = fetch_signals()
    for signal in signals:
        if signal.get("entry_ready"):
            msg = format_signal_message(signal)
            send_telegram_message(msg)

if __name__ == "__main__":
    main()
