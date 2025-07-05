from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
import yfinance as yf
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENV VARS
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
EXPO_PUSH_TOKEN = os.getenv("EXPO_PUSH_TOKEN")

# Commodity lookup
commodities = {
    "gold": "GC=F",
    "oil": "CL=F",
    "natural gas": "NG=F",
    "wheat": "ZW=F",
    "copper": "HG=F"
}

# Cache
recent_signals = []

def fetch_news():
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        url = f"https://newsapi.org/v2/everything?q=commodities&from={today}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        return [a["title"] + ". " + str(a.get("description", "")) for a in res.get("articles", [])][:15]
    except Exception as e:
        print("Error fetching news:", e)
        return []

def get_price_history(symbol):
    try:
        data = yf.download(symbol, period="7d", interval="1d")
        return list(data['Close'].dropna())
    except Exception as e:
        print("Error fetching price history:", e)
        return []

def analyze_news(news_snippets):
    # Hardcoded fake AI response to test functionality
    return """
[
  {"commodity": "gold", "trend": "up", "confidence": 91, "reason": "central bank demand", "entry": 2100, "exit": 2150, "stop_loss": 2079},
  {"commodity": "oil", "trend": "down", "confidence": 84, "reason": "oversupply concerns", "entry": 80, "exit": 74, "stop_loss": 83}
]
"""

def send_push_notification(title, body):
    if not EXPO_PUSH_TOKEN:
        return
    try:
        requests.post("https://exp.host/--/api/v2/push/send", json={
            "to": EXPO_PUSH_TOKEN,
            "sound": "default",
            "title": title,
            "body": body
        })
    except Exception as e:
        print("Error sending push notification:", e)

@app.get("/analyze")
def analyze():
    try:
        news = fetch_news()
        ai_response = analyze_news(news)

        try:
            parsed = eval(ai_response)
        except Exception as parse_error:
            print("Error parsing AI response:", parse_error)
            parsed = []

        enriched = []
        for rec in parsed[:8]:
            com = rec['commodity'].lower()
            symbol = commodities.get(com)
            history = get_price_history(symbol) if symbol else []
            pct_change = f"{((history[-1] - history[0]) / history[0]) * 100:.2f}%" if len(history) > 1 else "N/A"
            signal = {
                **rec,
                "change_pct": pct_change,
                "history": history,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
            enriched.append(signal)

            recent_signals.insert(0, signal)
            if len(recent_signals) > 10:
                recent_signals.pop()

            if rec['confidence'] >= 80 and history and abs((history[-1] - history[0]) / history[0]) >= 0.02:
                send_push_notification(
                    f"{rec['commodity'].capitalize()} {rec['trend']}trend detected",
                    f"{rec['reason']}. Entry: {rec['entry']}, Target: {rec['exit']}, Stop: {rec['stop_loss']}. Confidence: {rec['confidence']}%, 7d change: {pct_change}"
                )

        return {"signals": enriched}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

@app.get("/signals")
def get_signals():
    return {"signals": recent_signals}
