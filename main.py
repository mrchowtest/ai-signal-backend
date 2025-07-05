from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import yfinance as yf
import os
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI()

# Allow mobile app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENV VARS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
EXPO_PUSH_TOKEN = os.getenv("EXPO_PUSH_TOKEN")

client = OpenAI(api_key=OPENAI_API_KEY)

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
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://newsapi.org/v2/everything?q=commodities&from={today}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    res = requests.get(url).json()
    return [a["title"] + ". " + str(a.get("description", "")) for a in res.get("articles", [])][:15]

def get_price_history(symbol):
    data = yf.download(symbol, period="7d", interval="1d")
    return list(data['Close'].dropna())

def analyze_news(news_snippets):
    prompt = f"""
Analyze the news headlines and recommend 6-8 high-confidence commodity trades.
For each, provide:
- commodity name
- trend (up/down)
- confidence % (like 89%)
- reason
- entry price
- exit price
- stop loss

News:
{''.join(f'- {n}\\n' for n in news_snippets)}

JSON Format:
[
  {{"commodity": "gold", "trend": "up", "confidence": 91, "reason": "central bank demand", "entry": 2100, "exit": 2150, "stop_loss": 2079}},
  ...
]
"""

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def send_push_notification(title, body):
    if not EXPO_PUSH_TOKEN:
        return
    requests.post("https://exp.host/--/api/v2/push/send", json={
        "to": EXPO_PUSH_TOKEN,
        "sound": "default",
        "title": title,
        "body": body
    })

@app.get("/analyze")
def analyze():
    news = fetch_news()
    ai_response = analyze_news(news)
    try:
        parsed = eval(ai_response)
    except Exception as e:
        print("Error parsing AI response:", e)
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

@app.get("/signals")
def get_signals():
    return {"signals": recent_signals}
