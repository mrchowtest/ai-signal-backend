from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import openai
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = FastAPI()

# CORS config
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENV variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")

openai.api_key = OPENAI_API_KEY

# === Fetch live price using Twelve Data ===
def get_price_history(pair):
    if not TWELVE_API_KEY:
        print("❌ Twelve Data API key missing.")
        return None
    url = f"https://api.twelvedata.com/price?symbol={pair.upper()}&apikey={TWELVE_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        price = float(data["price"])
        print(f"💱 Live price for {pair}: {price}")
        return price
    except Exception as e:
        print(f"⚠️ Error fetching live price for {pair}: {e}")
        return None

# === Send to Telegram ===
def send_telegram_message(text: str):
    if not TELEGRAM_API_KEY or not TELEGRAM_CHAT_ID:
        print("❌ Telegram credentials missing.")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_API_KEY}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        r = requests.post(url, json=payload)
        print(f"📬 Telegram sent: {r.text}")
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")

# === Analyze Forex Signal Endpoint ===
@app.get("/analyze")
def analyze_forex():
    prompt = (
        "Act as a professional Forex trader. Based on macroeconomic trends and recent news, "
        "generate high-confidence trading signals for: EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, EURGBP, XAUUSD. "
        "Return a list of dictionaries with: pair, trend_direction (up/down), confidence_level (0-100), "
        "reason, entry_price, take_profit, stop_loss."
    )

    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content
        print("🧠 Raw response:", raw)
        signals = eval(raw)
    except Exception as e:
        print(f"❌ AI parsing error: {e}")
        return {"error": "AI response parsing failed"}

    results = []

    for signal in signals:
        pair = signal.get("pair")
        tp = signal.get("take_profit")
        sl = signal.get("stop_loss")
        trend = signal.get("trend_direction", "").lower()
        confidence = signal.get("confidence_level")

        action = "BUY" if trend == "up" else "SELL"

        # Live price as entry price
        live_price = get_price_history(pair)
        if not live_price:
            continue

        # Validate TP/SL logic
        if action == "BUY" and not (tp > live_price and sl < live_price):
            print(f"❌ TP/SL logic invalid for BUY on {pair}")
            continue
        if action == "SELL" and not (tp < live_price and sl > live_price):
            print(f"❌ TP/SL logic invalid for SELL on {pair}")
            continue

        signal["entry_price"] = round(live_price, 5)
        signal["live_price"] = round(live_price, 5)
        signal["action"] = action
        signal["timestamp"] = datetime.utcnow().isoformat() + "Z"
        signal["entry_ready"] = True  # Always ready because price is live

        # Risk/Reward
        if tp and sl:
            reward = abs(tp - live_price)
            risk = abs(sl - live_price)
            signal["risk_reward_ratio"] = round(reward / risk, 2) if risk else None

        # Message format
        message = (
            f"🔔 *LIVE SIGNAL ALERT* 🔔\n\n"
            f"*Pair:* {pair}\n"
            f"*Action:* {action}\n"
            f"*Confidence:* {confidence}%\n"
            f"*Live Entry:* {live_price}\n"
            f"*Take Profit:* {tp}\n"
            f"*Stop Loss:* {sl}\n"
            f"*R/R:* {signal.get('risk_reward_ratio')}\n"
            f"🧠 *Reason:* {signal.get('reason')}"
        )
        send_telegram_message(message)
        results.append(signal)

    return {"signals": results}
