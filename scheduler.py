import time
import requests

while True:
    try:
        print("🔁 Triggering /analyze")
        requests.get("https://your-app-name.onrender.com/analyze")  # Replace with Render URL
    except Exception as e:
        print(f"⚠️ Failed to trigger analyze: {e}")
    time.sleep(900)  # Every 15 mins
