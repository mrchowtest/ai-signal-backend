import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")  # e.g. https://your-backend.onrender.com
TWELVE_API_KEY = os.getenv("TWELVE_API_KEY")

# === Utility: Check if it's a weekend ===
def is_weekend():
    return datetime.utcnow().weekday() >= 5  # Saturday or Sunday

# === Utility: Check if we're in a peak trading session ===
def is_peak_trading_hour():
    utc_hour = datetime.utcnow().hour
    # Asia: 00–04 UTC, London: 07–10 UTC, NY: 12–17 UTC
    return utc_hour in list(range(0, 5)) + list(range(7, 11)) + list(range(12, 18))

# === Utility: Get API usage remaining (Twelve Data) ===
def log_twelve_data_usage():
    if not TWELVE_API_KEY:
        print("⚠️ No Twelve Data API key provided.")
        return
    try:
        resp = requests.get(f"https://api.twelvedata.com/usage?apikey={TWELVE_API_KEY}")
        usage = resp.json()
        remaining = usage.get("requests_remaining")
        print(f"📊 Twelve Data API requests remaining: {remaining}")
    except Exception as e:
        print(f"⚠️ Failed to fetch Twelve Data usage: {e}")

# === Main logic ===
def main():
    print(f"⏱️ Checking for signals at {datetime.utcnow().isoformat()}Z")

    if is_weekend():
        print("⛔ It's the weekend. No trading.")
        return

    if not is_peak_trading_hour():
        print("⏸️ Outside peak trading hours. Skipping.")
        return

    if not BACKEND_URL:
        print("❌ BACKEND_URL not set in environment.")
        return

    try:
        response = requests.get(f"{BACKEND_URL}/analyze")
        response.raise_for_status()
        data = response.json()
        signals = data.get("signals", [])
        print(f"📈 Retrieved {len(signals)} signals.")

        # Log entry-ready signals only
        entry_ready = [s for s in signals if s.get("entry_ready")]
        print(f"✅ {len(entry_ready)} entry-ready signals sent to Telegram.")

        log_twelve_data_usage()

    except Exception as e:
        print(f"❌ Error fetching/analyzing signals: {e}")

if __name__ == "__main__":
    main()
