import os
import requests
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        print("✅ Telegram message sent")
    except Exception as e:
        print(f"❌ Error sending Telegram message: {e}")

def is_peak_trading_hour():
    now_utc = datetime.now(timezone.utc)
    hour = now_utc.hour
    return (7 <= hour < 11) or (13 <= hour < 16)

def main():
    now_utc = datetime.now(timezone.utc).isoformat()
    print(f"⏱️ Checking for signals at {now_utc}")

    if not is_peak_trading_hour():
        print("⏸️ Outside peak trading hours. Skipping.")
        return

    try:
        response = requests.get(f"{BACKEND_URL}/analyze")
        response.raise_for_status()
        data = response.json()
        signals = data.get("signals", [])

        entry_ready_signals = [s for s in signals if s.get("entry_ready")]

        if not entry_ready_signals:
            print("📭 No entry-ready signals at this time.")
            return

        for signal in entry_ready_signals:
            message = (
                "🔔🔔🔔 *NEW SIGNAL* 🔔🔔🔔\n\n"
                f"*Pair:* {signal['pair']}\n"
                f"*Action:* {signal['action']}\n"
                f"*Trend:* {signal['trend_direction'].title()}\n"
                f"*Confidence:* {signal['confidence_level']}%\n"
                f"*Entry Price:* {signal['entry_price']}\n"
                f"*Live Price:* {signal['live_price']}\n"
                f"*Distance to Entry:* {round(signal['distance_to_entry'], 5)}\n"
                f"*Take Profit:* {signal['take_profit']}\n"
                f"*Stop Loss:* {signal['stop_loss']}\n"
                f"🟢 *Entry Ready:* ✅ YES\n"
            )
            send_telegram_message(message)

    except Exception as e:
        print(f"❌ Error fetching/analyzing signals: {e}")

if __name__ == "__main__":
    main()
