import requests
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "https://ai-signal-api-onq4.onrender.com/analyze")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_message(text):
    if not TELEGRAM_API_KEY or not TELEGRAM_CHAT_ID:
        print("❌ Telegram config missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload)
        print("✅ Telegram sent:", res.status_code)
    except Exception as e:
        print("⚠️ Telegram error:", e)

def fetch_and_alert():
    try:
        res = requests.get(BACKEND_URL)
        data = res.json()
        signals = data.get("signals", [])
        for s in signals:
            if s.get("entry_ready"):
                msg = (
                    f"🔔🔔🔔 *NEW SIGNAL* 🔔🔔🔔\n\n"
                    f"*Pair:* {s['pair']}\n"
                    f"*Action:* {s['action']}\n"
                    f"*Trend:* {s['trend_direction'].title()}\n"
                    f"*Confidence:* {s['confidence_level']}%\n"
                    f"*Entry Price:* {s['entry_price']}\n"
                    f"*Live Price:* {s['live_price']}\n"
                    f"*Distance to Entry:* {s['distance_to_entry']}\n"
                    f"*Take Profit:* {s['take_profit']}\n"
                    f"*Stop Loss:* {s['stop_loss']}\n"
                    f"🟢 *Entry Ready:* ✅ YES"
                )
                send_telegram_message(msg)
    except Exception as e:
        print("❌ Error fetching/analyzing signals:", e)

if __name__ == "__main__":
    fetch_and_alert()
