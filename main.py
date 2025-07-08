from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import requests
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

TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Sample Signal Generator (mocked data for now)
def generate_signals():
    return [
        {
            "pair": "EURUSD",
            "trend_direction": "up",
            "confidence_level": 80,
            "reason": "ECB hints at possible rate hike",
            "entry_price": 1.2050,
            "take_profit": 1.2150,
            "stop_loss": 1.2000,
            "action": "BUY",
            "live_price": 1.17325,
            "distance_to_entry": 0.03175,
            "entry_ready": False,
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "pair": "GBPUSD",
            "trend_direction": "down",
            "confidence_level": 85,
            "reason": "BoE dovish stance",
            "entry_price": 1.3100,
            "take_profit": 1.2950,
            "stop_loss": 1.3150,
            "action": "SELL",
            "live_price": 1.3210,
            "distance_to_entry": 0.0110,
            "entry_ready": True,
            "timestamp": datetime.utcnow().isoformat()
        },
    ]

# Format message for Telegram
def format_telegram_message(signal):
    return f"""
