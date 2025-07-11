import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")

def is_peak_trading_hour():
    now = datetime.now(timezone.utc)
    hour = now.hour
    weekday = now.weekday()  # Monday = 0, Sunday = 6
    if weekday >= 5:
        print("📴 Skipping weekend.")
        return False
    return (7 <= hour < 10) or (13 <= hour < 16) or (19 <= hour < 20)

def log_twelve_data_usage():
    if not TWELVE_API_KEY:
        print("⚠️ No Twelve Data API key provided.")
        return
    try:
        response = requests.get(
            f"https://api.twelvedata.com/usage?apikey={TWELVE_API_KEY}"
        )
        data = response.json()
        if "usage" in data:
            used = data["usage"]["requests"]
            limit = data["usage"]["plan"]["request_limit"]
            print(f"📊 Twelve Data usage: {used}/{limit} requests used.")
        else:
            print("⚠️ Couldn't fetch Twelve Data usage info.")
    except Exception as e:
        print(f"❌ Error checking Twelve Data usage: {e}")

def send_telegram_alert(signal):
    message = f"""🔔🔔🔔 *NEW SIGNAL* 🔔🔔🔔

*{signal['pair']}* {signal['action']}

*Trend:* {signal['trend_direction'].title()}
*Confidence:* {signal['confidence_level']}%
*Entry Price:* {signal['entry_price']}
*Live Price:* {signal['live_price']}
*Distance to Entry:* {round(signal['distance_to_entry'], 5)}
*Take Profit:* {signal['take_profit']}
*Stop Loss:* {signal['stop_loss']}
🟢 *Entry Ready:* ✅ YES
"""

    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload)
        print(f"📬 Sent alert for {signal['pair']}: {res.status_code}")
    except Exception as e:
        print(f"❌ Failed to send Telegram message: {e}")

def check_signals():
    if not is_peak_trading_hour():
        return

    print(f"⏱️ Checking for signals at {datetime.now(timezone.utc).isoformat()}")

    try:
        response = requests.get(f"{BACKEND_URL}/analyze")
        response.raise_for_status()
        data = response.json()

        signals = data.get("signals", [])
        entry_ready_signals = [s for s in signals if s.get("entry_ready")]

        if not entry_ready_signals:
            print("📭 No entry-ready signals at this time.")
        else:
            for signal in entry_ready_signals:
                send_telegram_alert(signal)

    except Exception as e:
        print(f"❌ Error fetching/analyzing signals: {e}")

    log_twelve_data_usage()

if __name__ == "__main__":
    check_signals()
