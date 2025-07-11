from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import openai
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENV VARS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")

openai.api_key = OPENAI_API_KEY

# === Get live price using Twelve Data ===
def get_price_history(pair):
    if not TWELVE_API_KEY:
        print("⚠️ No Twelve Data API key provided.")
        return None

    base, quote = pair[:3].upper(), pair[3:].upper()
    symbol = f"{base}/{quote}"
    url = f"https://api.twelvedata.com/price?symbol={symbol}&apikey={TWELVE_API_KEY}"
    print(f"📡 Price API: {url}")

    try:
        response = requests.get(url)
        data = response.json()
        print(f"🔍 Price data for {pair}: {data}")
        return float(data.get("price"))
    except Exception as e:
        print(f"⚠️ Error fetching price for {pair}: {e}")
        return None

# === Telegram message ===
def send_telegram_message(text: str):
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
        response = requests.post(url, json=payload)
        print(f"📤 Telegram response: {response.text}")
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")

# === Main analysis endpoint ===
@app.get("/analyze")
def analyze_forex():
    prompt = (
        "Act as a professional Forex trader. Based on recent macroeconomic news and trends, "
        "generate high-confidence trading signals for pairs: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, EURGBP. "
        "Include: forex pair, trend_direction (up/down), confidence_level (0-100), reason, entry_price, take_profit, stop_loss. "
        "Return as a valid Python list of dictionaries."
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        raw_text = response.choices[0].message.content
        print(f"🧠 AI response:\n{raw_text}")
        signals = eval(raw_text)
    except Exception as e:
        print(f"❌ Error parsing AI response: {e}")
        return {"error": "AI parsing failed"}, 500

    results = []

    for signal in signals:
        if not isinstance(signal, dict):
            print(f"⚠️ Skipping malformed signal: {signal}")
            continue

        pair = signal.get("pair") or signal.get("forex_pair")
        if not pair:
            print(f"⚠️ No 'pair' found in: {signal}")
            continue

        entry_price = signal.get("entry_price")
        take_profit = signal.get("take_profit")
        stop_loss = signal.get("stop_loss")
        trend = signal.get("trend_direction", "").lower()
        action = "BUY" if trend == "up" else "SELL"

        live_price = get_price_history(pair)
        if not live_price:
            continue

        signal["action"] = action
        signal["live_price"] = round(live_price, 5)
        signal["distance_to_entry"] = round(abs(entry_price - live_price), 5)
        signal["timestamp"] = datetime.utcnow().isoformat() + "Z"

        signal["entry_ready"] = (
            live_price >= entry_price if action == "BUY" else live_price <= entry_price
        )

        if take_profit and stop_loss:
            reward = abs(take_profit - entry_price)
            risk = abs(entry_price - stop_loss)
            signal["risk_reward_ratio"] = round(reward / risk, 2) if risk else None

        results.append(signal)

        if signal["entry_ready"]:
            message = (
                f"🔔🔔🔔 *NEW SIGNAL* 🔔🔔🔔\n\n"
                f"*Pair:* {pair}\n"
                f"*Action:* {action}\n"
                f"*Trend:* {trend.title()}\n"
                f"*Confidence:* {signal['confidence_level']}%\n"
                f"*Entry Price:* {entry_price}\n"
                f"*Live Price:* {signal['live_price']}\n"
                f"*Distance to Entry:* {signal['distance_to_entry']}\n"
                f"*Take Profit:* {take_profit}\n"
                f"*Stop Loss:* {stop_loss}\n"
                f"🟢 *Entry Ready:* ✅ YES"
            )
            send_telegram_message(message)

    return {"signals": results}
