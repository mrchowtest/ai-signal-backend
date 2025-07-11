from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import openai
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment Variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
openai.api_key = OPENAI_API_KEY

# === Fetch live price ===
def get_price_history(pair):
    base, quote = pair[:3].upper(), pair[3:].upper()
    url = f"https://open.er-api.com/v6/latest/{base}"
    try:
        response = requests.get(url)
        data = response.json()
        return data.get("rates", {}).get(quote)
    except Exception as e:
        print(f"⚠️ Price fetch error: {e}")
        return None

# === Telegram Notification ===
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
        requests.post(url, json=payload)
    except Exception as e:
        print(f"⚠️ Telegram error: {e}")

# === Analyze route ===
@app.get("/analyze")
def analyze_forex():
    prompt = (
        "Act as a professional Forex trader. Generate high-confidence signals for: "
        "EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, EURGBP, XAUUSD. "
        "Return a Python list of dicts with: pair, trend_direction, confidence_level, "
        "entry_price, take_profit, stop_loss."
    )
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        raw = response.choices[0].message.content
        signals = eval(raw)
    except Exception as e:
        print(f"❌ AI parsing error: {e}")
        return {"error": "AI parsing failed"}

    results = []
    for s in signals:
        if not isinstance(s, dict): continue
        pair = s.get("pair")
        if not pair: continue

        trend = s.get("trend_direction", "").lower()
        action = "BUY" if trend == "up" else "SELL"
        entry_price = s.get("entry_price")
        take_profit = s.get("take_profit")
        stop_loss = s.get("stop_loss")

        live_price = get_price_history(pair)
        if not live_price: continue

        s["action"] = action
        s["live_price"] = round(live_price, 5)
        s["distance_to_entry"] = round(abs(entry_price - live_price), 5)
        s["timestamp"] = datetime.utcnow().isoformat() + "Z"
        s["entry_ready"] = live_price >= entry_price if action == "BUY" else live_price <= entry_price

        if take_profit and stop_loss:
            r = abs(take_profit - entry_price)
            risk = abs(entry_price - stop_loss)
            s["risk_reward_ratio"] = round(r / risk, 2) if risk else None

        results.append(s)

        if s["entry_ready"]:
            msg = (
                f"🔔🔔🔔 *NEW SIGNAL* 🔔🔔🔔\n\n"
                f"*Pair:* {pair}\n"
                f"*Action:* {action}\n"
                f"*Trend:* {trend.title()}\n"
                f"*Confidence:* {s['confidence_level']}%\n"
                f"*Entry Price:* {entry_price}\n"
                f"*Live Price:* {s['live_price']}\n"
                f"*Distance to Entry:* {s['distance_to_entry']}\n"
                f"*Take Profit:* {take_profit}\n"
                f"*Stop Loss:* {stop_loss}\n"
                f"🟢 *Entry Ready:* ✅ YES"
            )
            send_telegram_message(msg)

    return {"signals": results}
