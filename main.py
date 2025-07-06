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

# Symbol lookup
symbols = {
    "XAUUSD": "GC=F",
    "XAGUSD": "SI=F",
    "BTCUSD": "BTC-USD",
    "ETHUSD": "ETH-USD",
    "EURUSD": None,
    "GBPUSD": None,
    "USDJPY": None,
    "AUDUSD": None,
    "USDCHF": None,
    "USDCAD": None,
    "NZDUSD": None
}

recent_signals = []

def fetch_news():
    today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://newsapi.org/v2/everything?q=forex OR crypto OR gold&from={today}&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    res = requests.get(url).json()
    return [a["title"] + ". " + str(a.get("description", "")) for a in res.get("articles", [])][:15]

def get_price_history(symbol):
    if not symbol:
        return []
    try:
        data = yf.download(symbol, period="7d", interval="1d")
        return list(data['Close'].dropna())
    except:
        return []

def analyze_news(news_snippets):
    prompt = f"""
You are a financial trading assistant. Based on the news headlines below, generate 6–8 high-confidence trading signals ONLY for Forex currency pairs, precious metals (e.g., XAUUSD), and major crypto pairs (e.g., BTCUSD).
Do NOT include commodities like corn, wheat, oil, etc.

Only return pairs in standard format:
Examples: EURUSD, GBPUSD, USDJPY, XAUUSD, XAUEUR, USDCHF, AUDUSD, NZDUSD, BTCUSD, ETHUSD

For each trade, provide:
- symbol
- trend ("up" or "down")
- confidence % (80–100)
- reason
- entry price
- exit price
- stop loss

News:
{''.join(f'- {n}\n' for n in news_snippets)}

JSON format only:
[
  {{
    "symbol": "XAUUSD",
    "trend": "up",
    "confidence": 91,
    "reason": "increased safe haven demand due to geopolitical tensions",
    "entry": 1920,
    "exit": 1975,
    "stop_loss": 1905
  }},
  ...
]
"""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
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
        symbol = rec['symbol'].upper()
        yf_symbol = symbols.get(symbol)
        history = get_price_history(yf_symbol)
        pct_change = f"{((history[-1] - history[0]) / history[0]) * 100:.2f}%" if len(history) > 1 else "N/A"
        signal = {
            **rec,
            "change_pct": pct_change,
            "history": history or [symbol],
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        enriched.append(signal)

        recent_signals.insert(0, signal)
        if len(recent_signals) > 10:
            recent_signals.pop()

        if rec['confidence'] >= 80 and history and abs((history[-1] - history[0]) / history[0]) >= 0.02:
            send_push_notification(
                f"{rec['symbol']} {rec['trend']}trend detected",
                f"{rec['reason']}. Entry: {rec['entry']}, Target: {rec['exit']}, Stop: {rec['stop_loss']}. Confidence: {rec['confidence']}%, 7d change: {pct_change}"
            )

    return {"signals": enriched}

@app.get("/signals")
def get_signals():
    return {"signals": recent_signals}
