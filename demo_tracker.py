import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")

# Check if it's the weekend
def is_weekend():
    return datetime.now(timezone.utc).weekday() >= 5

# Check if within peak hours: Asia (00–03 UTC), London (07–10 UTC), New York (12–16 UTC)
def is_peak_hour():
    utc_hour = datetime.now(timezone.utc).hour
    return utc_hour in list(range(0, 4)) + list(range(7, 11)) + list(range(12, 17))

# Send message to Telegram
def send_telegram(text):
    if not TELEGRAM_API_KEY or not TELEGRAM_CHAT_ID:
        print("❌ Missing Telegram credentials.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload)
        print(f"📤 Telegram response: {res.text}")
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")

# Log remaining Twelve Data usage
def log_twelve_data_usage():
    if not TWELVE_API_KEY:
        print("⚠️ No Twelve Data API key provided.")
        return
    try:
        r = requests.get(f"https://api.twelvedata.com/usage?apikey={TWELVE_API_KEY}")
        print(f"📊 Twelve Data usage: {r.json()}")
    except Exception as e:
        print(f"⚠️ Usage tracking error: {e}")

# Main logic
def run():
    now = datetime.now(timezone.utc)
    print(f"⏱️ Checking for signals at {now.isoformat()}")

    if is_weekend():
        print("⛔ Weekend detected. Skipping.")
        return

    if not is_peak_hour():
        print("⏸️ Outside peak trading hours. Skipping.")
        return

    try:
        response = requests.get(f"{BACKEND_URL}/analyze")
        response.raise_for_status()
        data = response.json()

        signals = data if isinstance(data, list) else data.get("signals", [])
        print(f"📈 Retrieved {len(signals)} signals.")

        sent_count = 0

        for signal in signals:
            if not signal.get("entry_ready"):
                continue

            message = (
                f"🔔🔔🔔 *NEW SIGNAL* 🔔🔔🔔\n\n"
                f"*Pair:* {signal['pair']}\n"
                f"*Action:* {signal['action']}\n"
                f"*Trend:* {signal['trend_direction'].title()}\n"
                f"*Confidence:* {signal['confidence_level']}%\n"
                f"*Entry Price:* {signal['entry_price']}\n"
                f"*Live Price:* {signal['live_price']}\n"
                f"*Distance to Entry:* {round(signal['distance_to_entry'], 5)}\n"
                f"*Take Profit:* {signal['take_profit']}\n"
                f"*Stop Loss:* {signal['stop_loss']}\n"
                f"🟢 *Entry Ready:* ✅ YES"
            )
            send_telegram(message)
            sent_count += 1

        print(f"✅ {sent_count} entry-ready signals sent to Telegram.")

    except Exception as e:
        print(f"❌ Error fetching/analyzing signals: {e}")

    # Log Twelve Data usage
    log_twelve_data_usage()

if __name__ == "__main__":
    run()
