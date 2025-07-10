import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from main import get_price_history  # Reuse your existing logic if possible

load_dotenv()

TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Dummy signals; in production replace with actual /analyze API or DB
FOREX_SIGNALS = [
    {
        "pair": "EURUSD",
        "trend_direction": "up",
        "confidence_level": 90,
        "reason": "Strong Eurozone data",
        "entry_price": 1.10,
        "take_profit": 1.12,
        "stop_loss": 1.095
    },
    {
        "pair": "GBPUSD",
        "trend_direction": "down",
        "confidence_level": 85,
        "reason": "UK recession fears",
        "entry_price": 1.25,
        "take_profit": 1.22,
        "stop_loss": 1.255
    },
    # Add more dummy signals as needed
]

def send_telegram_alert(signal):
    text = (
        f"😔😔😔 *NEW SIGNAL* 😔😔😔\n\n"
        f"*Pair:* {signal['pair']}\n"
        f"*Action:* {signal['action']}\n"
        f"*Trend:* {signal['trend_direction'].title()}\n"
        f"*Confidence:* {signal['confidence_level']}%\n"
        f"*Entry Price:* {signal['entry_price']}\n"
        f"*Live Price:* {signal['live_price']}\n"
        f"*Distance to Entry:* {round(signal['distance_to_entry'], 5)}\n"
        f"*Take Profit:* {signal['take_profit']}\n"
        f"*Stop Loss:* {signal['stop_loss']}\n"
        f"🟢 *Entry Ready:* {'✅ YES' if signal['entry_ready'] else '❌ NO'}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"})

def check_signals():
    for signal in FOREX_SIGNALS:
        pair = signal['pair']
        live_price = get_price_history(pair)
        if not live_price:
            continue

        signal['live_price'] = round(live_price, 5)
        signal['action'] = 'BUY' if signal['trend_direction'].lower() == 'up' else 'SELL'
        signal['distance_to_entry'] = abs(live_price - signal['entry_price'])
        signal['entry_ready'] = (
            (signal['action'] == 'BUY' and live_price >= signal['entry_price']) or
            (signal['action'] == 'SELL' and live_price <= signal['entry_price'])
        )

        if signal['entry_ready']:
            send_telegram_alert(signal)

if __name__ == "__main__":
    print(f"\u23f0 Running demo tracker at {datetime.utcnow().isoformat()}Z")
    check_signals()
