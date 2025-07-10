from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load API keys from .env
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Forex pairs to analyze
forex_pairs = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "EURGBP"]

def get_live_price(pair):
    base, quote = pair[:3], pair[3:]
    url = f"https://open.er-api.com/v6/latest/{base}"
    print(f"📡 API URL: {url}")
    try:
        res = requests.get(url)
        data = res.json()
        print(f"🔍 Fetching price for {pair}: {data}")
        if data["result"] == "success":
            return float(data["rates"].get(quote))
    except Exception as e:
        print(f"⚠️ Error fetching price for {pair}: {e}")
    return None

def send_telegram_alert(signal):
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
        f"🟢 *Entry Ready:* {'✅ YES' if signal['entry_ready'] else '❌ NO'}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
    try:
        response = requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        })
        print("✅ Telegram alert sent.")
    except Exception as e:
        print(f"❌ Telegram alert error: {e}")

@app.get("/analyze")
def analyze_forex():
    prompt = (
        "Act as a professional Forex trader. Based on recent macroeconomic news and market trends, "
        "generate high-confidence trading signals for these forex pairs: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, EURGBP. "
        "Return a JSON list of objects with:\n\n"
        "- pair (e.g., EURUSD)\n"
        "- trend_direction (up/down)\n"
        "- confidence_level (0-100)\n"
        "- reason\n"
        "- entry_price\n"
        "- take_profit\n"
        "- stop_loss\n\n"
        "Example:\n"
        "[{\"pair\": \"EURUSD\", \"trend_direction\": \"up\", \"confidence_level\": 90, \"reason\": \"ECB statement\", \"entry_price\": 1.2000, \"take_profit\": 1.2150, \"stop_loss\": 1.1950}]"
    )

    try:
        res = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        raw_text = res.choices[0].message.content
        print(f"🧠 AI raw response: {raw_text}")
        signals = json.loads(raw_text)
    except Exception as e:
        print(f"❌ Failed to get or parse AI response: {e}")
        return {"error": "AI parsing failed"}

    result = []
    for signal in signals:
        pair = signal.get("pair")
        if not pair:
            continue

        live = get_live_price(pair)
        entry = signal.get("entry_price")
        stop = signal.get("stop_loss")
        tp = signal.get("take_profit")

        signal["live_price"] = round(live, 5) if live else None
        signal["action"] = "BUY" if signal["trend_direction"].lower() == "up" else "SELL"

        if live and entry:
            signal["distance_to_entry"] = round(abs(live - entry), 5)
            if signal["action"] == "BUY":
                signal["entry_ready"] = live >= entry
            else:
                signal["entry_ready"] = live <= entry
        else:
            signal["entry_ready"] = False

        if entry and stop and tp:
            risk = abs(entry - stop)
            reward = abs(tp - entry)
            signal["risk_reward_ratio"] = round(reward / risk, 2) if risk else None

        signal["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Only send to Telegram if ENTRY READY
        if signal["entry_ready"]:
            send_telegram_alert(signal)

        result.append(signal)

    return {"signals": result}
