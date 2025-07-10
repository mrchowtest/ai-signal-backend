import os
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

API_URL = "http://localhost:8000/analyze"  # or your deployed URL
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload)
        if res.status_code != 200:
            print(f"❌ Telegram error: {res.text}")
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")

def format_signal(signal):
    return f"""🔔🔔🔔 *NEW SIGNAL* 🔔🔔🔔

*Pair:* {signal['pair']}
*Action:* {signal['action']}
*Trend:* {signal['trend_direction'].title()}
*Confidence:* {signal['confidence_level']}%
*Entry Price:* {signal['entry_price']}
*Live Price:* {signal['live_price']}
*Distance to Entry:* {round(signal['distance_to_entry'], 5)}
*Take Profit:* {signal['take_profit']}
*Stop Loss:* {signal['stop_loss']}
🟢 *Entry Ready:* ✅ YES
⏰ *Time:* {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
"""

def run():
    try:
        res = requests.get(API_URL)
        res.raise_for_status()
        data = res.json()
        for signal in data.get("signals", []):
            if signal.get("entry_ready"):
                msg = format_signal(signal)
                send_to_telegram(msg)
    except Exception as e:
        print(f"❌ Failed to fetch or process signals: {e}")

if __name__ == "__main__":
    run()
